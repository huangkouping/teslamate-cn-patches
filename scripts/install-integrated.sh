#!/usr/bin/env bash
# 在已有官方 TeslaMate 部署上，一次完成中文版仪表盘迁移与本仓库补丁。
# 不会触碰车辆数据；中文版迁移脚本会先备份 Compose 配置。

set -euo pipefail

PATCH_VERSION="v1.2.0"
CN_VERSION="v1.13.0"
CN_REPO="https://github.com/wjsall/teslamate-chinese-dashboards.git"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="${ROOT_DIR}/.upstream/teslamate-chinese-dashboards-${CN_VERSION}"
COMPOSE_FILE="${COMPOSE_FILE:-}"
ASSUME_YES=0
SKIP_GRAFANA=0
NGINX_CONFIG="${NGINX_CONFIG:-}"
SELFHEAL=1

usage() {
  cat <<'EOF'
用法：
  sudo bash scripts/install-integrated.sh [选项]

选项：
  --compose-file /路径/compose.yml  指定官方 TeslaMate 的 Compose 文件
  --yes                            跳过开始前确认（仍会要求输入 Grafana 密码）
  --skip-grafana-patches           只迁移中文版仪表盘，不运行本仓库的 Grafana 菜单补丁
  --nginx-config /路径/站点.conf   自动安全配置标准 Nginx 站点；会先备份、测试再重载
  --skip-navigation-selfheal       不安装导航自愈定时器（默认安装）
  -h, --help                       显示帮助

环境变量：
  GRAFANA_URL      默认 http://127.0.0.1:3000
  GRAFANA_USER     默认 admin
  GRAFANA_PASSWORD 可预先设置，避免交互输入

检测到标准 Nginx 单站点配置时，脚本会先备份、测试后自动注入浏览器补丁。
无法安全识别站点时不会改写；请使用 --nginx-config 指定实际站点配置文件，
或按 docs/installation.md 手动合并注入片段。
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compose-file) COMPOSE_FILE="${2:?--compose-file 需要文件路径}"; shift 2 ;;
    --yes) ASSUME_YES=1; shift ;;
    --skip-grafana-patches) SKIP_GRAFANA=1; shift ;;
    --nginx-config) NGINX_CONFIG="${2:?--nginx-config 需要文件路径}"; shift 2 ;;
    --skip-navigation-selfheal) SELFHEAL=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数：$1" >&2; usage >&2; exit 2 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "缺少命令：$1" >&2; exit 1; }; }
need git
need docker
need python3

if [[ -z "$COMPOSE_FILE" ]]; then
  echo "为保证版本检查可靠，必须提供官方 TeslaMate 的 Compose 文件：--compose-file /路径/compose.yml" >&2
  exit 2
fi
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "找不到 Compose 文件：$COMPOSE_FILE" >&2
  exit 1
fi
if ! grep -Eq "teslamate/teslamate:4\\.5\\.0([[:space:]]|$|[\\\"'])" "$COMPOSE_FILE"; then
  echo "当前安装器仅验证 TeslaMate 4.5.0；请先按 docs/upgrading.md 升级官方 TeslaMate 到 4.5.0，再运行本脚本。" >&2
  exit 2
fi

cat <<EOF
将执行以下受控操作：
  1. 使用中文版仪表盘 ${CN_VERSION} 的官方迁移脚本，把官方 Grafana 切换为中文版；
  2. 通过 Grafana API 应用本仓库 ${PATCH_VERSION} 的分类、8 项导航与概览提示；
  3. 安装 systemd 自愈定时器（teslamate-cn-nav.timer），Grafana 重启后导航自动恢复；
  4. 在 ${ROOT_DIR}/backups 中保留仪表盘修改前的备份。

不会修改 TeslaMate、PostgreSQL 或已有车辆数据。
EOF

if [[ "$ASSUME_YES" != "1" ]]; then
  read -r -p "确认继续？[y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] || { echo "已取消。"; exit 0; }
fi

mkdir -p "$(dirname "$UPSTREAM_DIR")"
if [[ ! -d "$UPSTREAM_DIR/.git" ]]; then
  git clone --depth 1 --branch "$CN_VERSION" "$CN_REPO" "$UPSTREAM_DIR"
else
  git -C "$UPSTREAM_DIR" fetch --depth 1 origin "refs/tags/${CN_VERSION}:refs/tags/${CN_VERSION}"
  git -C "$UPSTREAM_DIR" checkout --detach "$CN_VERSION"
fi

printf '\n==> 迁移为中文版仪表盘 %s\n' "$CN_VERSION"
migrate=(env "TARGET_REF=${CN_VERSION}" TESLAMATE_CN_PINNED=1)
[[ -n "$COMPOSE_FILE" ]] && migrate+=("COMPOSE_FILE=${COMPOSE_FILE}")
migrate+=(bash "$UPSTREAM_DIR/migrate-from-official.sh")
"${migrate[@]}"

if [[ "$SKIP_GRAFANA" == "1" ]]; then
  echo "\n中文版仪表盘已迁移；按 docs/installation.md 合并 Nginx 片段后，再运行 Grafana 补丁。"
  exit 0
fi

if [[ -z "${GRAFANA_PASSWORD:-}" ]]; then
  read -r -s -p "Grafana 管理员密码（不会显示）：" GRAFANA_PASSWORD
  echo
  [[ -n "$GRAFANA_PASSWORD" ]] || { echo "密码不能为空。" >&2; exit 1; }
  export GRAFANA_PASSWORD
fi

printf '\n==> 应用 Grafana 分类、导航与概览提示\n'
cd "$ROOT_DIR"
python3 scripts/reapply_grafana_customizations.py --backup-dir ./backups
python3 scripts/patch_overview_empty_state.py --backup-dir ./backups

selfheal_installed=0
if [[ "$SELFHEAL" == "1" ]] && command -v systemctl >/dev/null 2>&1; then
  printf '\n==> 安装导航自愈定时器（重启后自动恢复分类导航）\n'
  if GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}" bash scripts/install-navigation-selfheal.sh \
       --compose-file "$COMPOSE_FILE" --interval 5; then
    selfheal_installed=1
  else
    echo "自愈定时器安装失败；导航当前可用，但 Grafana 重启后会被镜像覆盖。可稍后重跑：sudo bash scripts/install-navigation-selfheal.sh --compose-file $COMPOSE_FILE" >&2
  fi
elif [[ "$SELFHEAL" != "1" ]]; then
  echo "已按要求跳过导航自愈定时器（--skip-navigation-selfheal）。"
else
  echo "当前系统没有 systemd，跳过导航自愈定时器。"
fi

nginx_configured=0
if command -v nginx >/dev/null 2>&1; then
  printf '\n==> 配置 Nginx 浏览器补丁\n'
  nginx_args=(--root "$ROOT_DIR")
  [[ -n "$NGINX_CONFIG" ]] && nginx_args+=(--config "$NGINX_CONFIG")
  if python3 scripts/configure_nginx.py "${nginx_args[@]}"; then
    nginx_configured=1
  else
    echo "Nginx 未自动修改；请按上方提示指定 --nginx-config，或参阅安装说明。" >&2
  fi
else
  echo "未检测到 Nginx；跳过浏览器补丁注入。"
fi

cat <<EOF

完成：中文版仪表盘、分类导航和 Grafana 优化已应用。
EOF

if [[ "$selfheal_installed" == "1" ]]; then
  echo "导航自愈已装好（5 分钟一轮，开机 2 分钟后首跑）：Grafana 重启后最多等一轮就会自动恢复。"
else
  echo "提示：导航未装自愈定时器，Grafana 重启后会回到镜像默认导航。"
fi

if [[ "$nginx_configured" == "1" ]]; then
  echo "Nginx 浏览器补丁已自动配置并重载；请使用浏览器强制刷新或无痕窗口验收。"
else
  cat <<EOF

还差一次 Nginx 配置合并，才能启用 TeslaMate 原生菜单中文分组、定位跳转高德，以及
Grafana 浏览器导航样式。请按以下文件的“注入浏览器补丁”步骤操作：
  ${ROOT_DIR}/docs/installation.md
EOF
fi
