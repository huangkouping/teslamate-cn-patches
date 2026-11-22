#!/usr/bin/env bash
# Fresh, guided TeslaMate deployment. Run as root or with sudo.
set -euo pipefail

REPO_URL="https://github.com/huangkouping/teslamate-cn-patches.git"
REPO_DIR="/opt/teslamate-cn-patches"
INSTALL_DIR="/opt/teslamate"

[[ "${EUID}" == 0 ]] || { echo "请使用：sudo bash scripts/install-from-zero.sh" >&2; exit 1; }

install_base_tools() {
  command -v curl >/dev/null && command -v git >/dev/null && command -v openssl >/dev/null && return
  if command -v apt-get >/dev/null; then apt-get update && apt-get install -y ca-certificates curl git openssl
  elif command -v dnf >/dev/null; then dnf install -y ca-certificates curl git openssl
  elif command -v yum >/dev/null; then yum install -y ca-certificates curl git openssl
  else echo "不支持自动安装基础工具，请先安装 curl、git 与 openssl。" >&2; exit 1; fi
}

install_base_tools
if ! command -v docker >/dev/null; then
  echo "未检测到 Docker，开始使用 Docker 官方安装脚本安装…"
  curl -fsSL https://get.docker.com | sh
fi
command -v systemctl >/dev/null || { echo "未检测到 systemctl；请先按 Docker 官方文档启动 Docker 服务。" >&2; exit 1; }
systemctl enable --now docker
if ! docker compose version >/dev/null 2>&1; then
  if command -v apt-get >/dev/null; then apt-get install -y docker-compose-plugin
  elif command -v dnf >/dev/null; then dnf install -y docker-compose-plugin
  elif command -v yum >/dev/null; then yum install -y docker-compose-plugin
  fi
fi
docker compose version >/dev/null 2>&1 || { echo "Docker Compose 插件安装失败，请按 Docker 官方文档处理。" >&2; exit 1; }
[[ ! -e "$INSTALL_DIR/compose.yml" ]] || { echo "$INSTALL_DIR 已存在 Compose 配置；为保护已有数据，已停止。" >&2; exit 1; }

mkdir -p "$INSTALL_DIR"
if [[ ! -d "$REPO_DIR/.git" ]]; then git clone "$REPO_URL" "$REPO_DIR"; else git -C "$REPO_DIR" pull --ff-only; fi

umask 077
ENCRYPTION_KEY="$(openssl rand -hex 32)"
DATABASE_PASS="$(openssl rand -base64 24 | tr -d '\n')"
GRAFANA_PASSWORD="$(openssl rand -base64 18 | tr -d '\n')"
cat > "$INSTALL_DIR/.env" <<EOF
ENCRYPTION_KEY=${ENCRYPTION_KEY}
DATABASE_PASS=${DATABASE_PASS}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
EOF

cat > "$INSTALL_DIR/compose.yml" <<'EOF'
services:
  teslamate:
    image: teslamate/teslamate:4.5.0
    restart: always
    environment:
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      DATABASE_USER: teslamate
      DATABASE_PASS: ${DATABASE_PASS}
      DATABASE_NAME: teslamate
      DATABASE_HOST: database
      MQTT_HOST: mosquitto
    ports: ["4000:4000"]
    volumes: ["./import:/opt/app/import"]
    cap_drop: [all]
  database:
    image: postgres:18-trixie
    restart: always
    environment:
      POSTGRES_USER: teslamate
      POSTGRES_PASSWORD: ${DATABASE_PASS}
      POSTGRES_DB: teslamate
    volumes: ["teslamate-db:/var/lib/postgresql"]
  grafana:
    image: teslamate/grafana:latest
    restart: always
    environment:
      DATABASE_USER: teslamate
      DATABASE_PASS: ${DATABASE_PASS}
      DATABASE_NAME: teslamate
      DATABASE_HOST: database
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    ports: ["3000:3000"]
    volumes: ["teslamate-grafana-data:/var/lib/grafana"]
  mosquitto:
    image: eclipse-mosquitto:2
    restart: always
    command: mosquitto -c /mosquitto-no-auth.conf
    volumes: ["mosquitto-conf:/mosquitto/config", "mosquitto-data:/mosquitto/data"]
volumes:
  teslamate-db:
  teslamate-grafana-data:
  mosquitto-conf:
  mosquitto-data:
EOF

cd "$INSTALL_DIR"
docker compose up -d
echo "等待 Grafana 就绪…"
grafana_ready=0
for _ in $(seq 1 60); do
  if curl -fsS --max-time 2 http://127.0.0.1:3000/api/health >/dev/null 2>&1; then
    grafana_ready=1
    break
  fi
  sleep 2
done
if [[ "$grafana_ready" != "1" ]]; then
  echo "Grafana 在 120 秒内未就绪。为保护安装过程，已停止；请执行：docker compose logs --tail=100 grafana" >&2
  exit 1
fi
GRAFANA_PASSWORD="$GRAFANA_PASSWORD" bash "$REPO_DIR/scripts/install-integrated.sh" --yes --compose-file "$INSTALL_DIR/compose.yml"

cat <<EOF

安装完成。请妥善保存以下信息（不会再次显示）：
  TeslaMate: http://服务器IP:4000
  Grafana:    http://服务器IP:3000
  Grafana 用户名: admin
  Grafana 密码: ${GRAFANA_PASSWORD}
  密钥文件: ${INSTALL_DIR}/.env （权限 600）

下一步：打开 TeslaMate 页面，按官方流程填写 Tesla access token 与 refresh token。
未配置 HTTPS 反向代理前，请不要将 4000、3000 端口直接暴露到公网。
EOF
