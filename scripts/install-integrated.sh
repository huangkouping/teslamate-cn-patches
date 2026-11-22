#!/usr/bin/env bash
# 在已有官方 TeslaMate 部署上，一次完成中文版仪表盘迁移与本仓库补丁。
# 不会触碰车辆数据；中文版迁移脚本会先备份 Compose 配置。

set -euo pipefail

PATCH_VERSION="v1.1.0"
CN_VERSION="v1.13.0"
CN_REPO="https://github.com/wjsall/teslamate-chinese-dashboards.git"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="${ROOT_DIR}/.upstream/teslamate-chinese-dashboards-${CN_VERSION}"
COMPOSE_FILE="${COMPOSE_FILE:-}"
ASSUME_YES=0
SKIP_GRAFANA=0

usage() {
  cat <<'EOF'
用法：
  sudo bash scripts/install-integrated.sh [选项]

选项：
  --compose-file /路径/compose.yml  指定官方 TeslaMate 的 Compose 文件
  --yes                            跳过开始前确认（仍会要求输入 Grafana 密码）
  --skip-grafana-patches           只迁移中文版仪表盘，不运行本仓库的 Grafana 菜单补丁
  -h, --help                       显示帮助

环境变量：
  GRAFANA_URL      默认 http://127.0.0.1:3000
  GRAFANA_USER     默认 admin
  GRAFANA_PASSWORD 可预先设置，避免交互输入

本脚本不自动改写 Nginx。完成后请按 docs/installation.md 合并一次 Nginx 注入片段，
这是为了避免覆盖你的域名、证书、访问控制和反向代理配置。
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compose-file) COMPOSE_FILE="${2:?--compose-file 需要文件路径}"; shift 2 ;;
    --yes) ASSUME_YES=1; shift ;;
    --skip-grafana-patches) SKIP_GRAFANA=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数：$1" >&2; usage >&2; exit 2 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "缺少命令：$1" >&2; exit 1; }; }
need git
need docker
need python3

if [[ -n "$COMPOSE_FILE" && ! -f "$COMPOSE_FILE" ]]; then
  echo "找不到 Compose 文件：$COMPOSE_FILE" >&2
  exit 1
fi

cat <<EOF
将执行以下受控操作：
  1. 使用中文版仪表盘 ${CN_VERSION} 的官方迁移脚本，把官方 Grafana 切换为中文版；
  2. 通过 Grafana API 应用本仓库 ${PATCH_VERSION} 的分类、导航与概览提示；
  3. 在 ${ROOT_DIR}/backups 中保留仪表盘修改前的备份。

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

echo "\n==> 迁移为中文版仪表盘 ${CN_VERSION}"
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

echo "\n==> 应用 Grafana 分类、导航与概览提示"
cd "$ROOT_DIR"
python3 scripts/tag_grafana_categories.py --backup-dir ./backups
python3 scripts/sync_grafana_navigation.py --backup-dir ./backups
python3 scripts/patch_overview_empty_state.py --backup-dir ./backups

cat <<EOF

完成：中文版仪表盘和 Grafana 优化已应用。

还差一次 Nginx 配置合并，才能启用 TeslaMate 原生菜单中文分组、定位跳转高德，以及
Grafana 浏览器导航样式。请按以下文件的“注入浏览器补丁”步骤操作：
  ${ROOT_DIR}/docs/installation.md

完成 Nginx 重载后，使用浏览器强制刷新或无痕窗口验收。
EOF
