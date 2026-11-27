#!/usr/bin/env bash
# 给 Grafana 导航补丁装一个 systemd 自愈定时器：
# 镜像每次重启都会按内置 JSON 重新签出面板，把本仓库写过的导航链接和分类标签覆盖回默认值。
# 定时器定期检测，一旦发现被覆盖就自动重新应用（默认 5 分钟一轮，没有改动时不写库）。
#
# 默认安装单元：
#   teslamate-cn-nav.service  一次性执行 reapply_grafana_customizations.py
#   teslamate-cn-nav.timer    开机 2 分钟后首跑，之后每 5 分钟一轮
#
# 用法：
#   sudo GRAFANA_PASSWORD='***' bash scripts/install-navigation-selfheal.sh --compose-file /opt/teslamate/compose.yml
#   sudo bash scripts/install-navigation-selfheal.sh --uninstall

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-}"
INTERVAL_MIN="5"
UNINSTALL=0
ENV_FILE="/etc/default/teslamate-cn-nav"
UNIT_DIR="/etc/systemd/system"

usage() {
  cat <<'EOF'
用法：
  sudo bash scripts/install-navigation-selfheal.sh [选项]

选项：
  --compose-file /路径/compose.yml   TeslaMate 的 Compose 文件（用于定位备份目录）
  --interval N                       自愈间隔（分钟，默认 5）
  --uninstall                        删除自愈单元与密码文件
  -h, --help                         显示帮助

环境变量：
  GRAFANA_URL      默认 http://127.0.0.1:3000
  GRAFANA_USER     默认 admin
  GRAFANA_PASSWORD 可预先设置，避免交互输入（会写入 chmod 600 的 /etc/default/teslamate-cn-nav）
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compose-file) COMPOSE_FILE="${2:?需要文件路径}"; shift 2 ;;
    --interval) INTERVAL_MIN="${2:?需要分钟数}"; shift 2 ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数：$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "$UNINSTALL" == "1" ]]; then
  systemctl disable --now teslamate-cn-nav.timer 2>/dev/null || true
  rm -f "${UNIT_DIR}/teslamate-cn-nav.service" "${UNIT_DIR}/teslamate-cn-nav.timer" "${ENV_FILE}"
  systemctl daemon-reload
  echo "已删除自愈单元与 ${ENV_FILE}。补丁本身不会被回滚；下一轮镜像重启后导航会回到默认值。"
  exit 0
fi

[[ "$(id -u)" == "0" ]] || { echo "请用 root 运行（sudo）。" >&2; exit 1; }
command -v systemctl >/dev/null 2>&1 || { echo "当前系统没有 systemd，无法安装自愈定时器。" >&2; exit 1; }

if [[ -z "$COMPOSE_FILE" ]]; then
  echo "需要 --compose-file /路径/compose.yml（用于把备份写在项目目录下）。" >&2
  exit 2
fi
[[ -f "$COMPOSE_FILE" ]] || { echo "找不到 Compose 文件：$COMPOSE_FILE" >&2; exit 1; }
COMPOSE_DIR="$(cd "$(dirname "$COMPOSE_FILE")" && pwd)"
BACKUP_DIR="${COMPOSE_DIR}/backups"
mkdir -p "$BACKUP_DIR"

if [[ -z "${GRAFANA_PASSWORD:-}" ]]; then
  read -r -s -p "Grafana 管理员密码（不会显示）：" GRAFANA_PASSWORD
  echo
  [[ -n "$GRAFANA_PASSWORD" ]] || { echo "密码不能为空。" >&2; exit 1; }
export GRAFANA_PASSWORD
fi

umask 077
cat > "$ENV_FILE" <<ENV
GRAFANA_URL=${GRAFANA_URL:-http://127.0.0.1:3000}
GRAFANA_USER=${GRAFANA_USER:-admin}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
ENV
chmod 600 "$ENV_FILE"

cat > "${UNIT_DIR}/teslamate-cn-nav.service" <<UNIT
[Unit]
Description=Reapply TeslaMate CN Grafana navigation
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile=${ENV_FILE}
ExecStart=/usr/bin/env python3 ${ROOT_DIR}/scripts/reapply_grafana_customizations.py --backup-dir ${BACKUP_DIR} --keep-backups 5 --quiet
TimeoutStartSec=5min
UNIT

cat > "${UNIT_DIR}/teslamate-cn-nav.timer" <<UNIT
[Unit]
Description=Periodic reapply of TeslaMate CN Grafana navigation

[Timer]
OnBootSec=2min
OnUnitActiveSec=${INTERVAL_MIN}min
AccuracySec=30s

[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now teslamate-cn-nav.timer
systemctl start teslamate-cn-nav.service || true
printf '\n自愈定时器已启用：%s 分钟一轮（开机 2 分钟后首跑）。\n' "$INTERVAL_MIN"
echo "立即验收："
echo "  systemctl status teslamate-cn-nav.timer --no-pager"
echo "  journalctl -u teslamate-cn-nav.service -n 20 --no-pager"
echo "想做到重启后零等待，请继续看 docs/grafana-navigation-persistence.md 的“零窗口”一节。"
