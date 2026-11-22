# 从零开始：官方 TeslaMate + 中文优化

本页给完全新用户使用。顺序固定：**先启动官方 TeslaMate，再运行本仓库的一次整合安装**。以下示例适配本仓库当前验证组合：TeslaMate 4.5.0 与中文版仪表盘 v1.13.0。

## 最简单：一条命令

直接执行即可。脚本会先检测 Docker、Docker Compose 与 Git；缺少时使用系统包管理器补齐基础工具，并使用 Docker 官方安装脚本安装 Docker。

```bash
curl -fsSL https://raw.githubusercontent.com/huangkouping/teslamate-cn-patches/main/scripts/install-from-zero.sh | sudo bash
```

脚本自动创建 `/opt/teslamate`、生成高强度随机密钥、启动官方 TeslaMate 4.5.0、安装中文版与本补丁。它会在结尾显示 Grafana 初始密码，并把所有密钥安全保存在 `/opt/teslamate/.env`（仅 root 可读）。完成后只需打开 TeslaMate 网页填写 Tesla access token 与 refresh token。

> 不要把 4000、3000、1883 直接暴露到公网。官方也建议公网访问使用 VPN、Cloudflare Tunnel 或经过加固的 HTTPS 反向代理。请先完成服务器防火墙与 Nginx/域名配置，再对外开放。

## 1. 准备 Docker

安装 Docker Engine 与 Docker Compose 插件后确认：

```bash
docker --version
docker compose version
```

服务器建议至少 2 GB 内存并保持持续运行。Docker 官方安装方式因系统不同而异，请按 [Docker 官方文档](https://docs.docker.com/engine/install/) 完成，不要安装来历不明的一键脚本。

## 2. 创建官方基础服务

```bash
sudo mkdir -p /opt/teslamate
cd /opt/teslamate
openssl rand -hex 32
openssl rand -base64 24
```

将上面生成的第一段填入 `ENCRYPTION_KEY`，第二段填入两个数据库密码位置；然后创建 `compose.yml`：

```yaml
services:
  teslamate:
    image: teslamate/teslamate:4.5.0
    restart: always
    environment:
      ENCRYPTION_KEY: 请替换为第一段随机值
      DATABASE_USER: teslamate
      DATABASE_PASS: 请替换为第二段随机值
      DATABASE_NAME: teslamate
      DATABASE_HOST: database
      MQTT_HOST: mosquitto
    ports:
      - "4000:4000"
    volumes:
      - ./import:/opt/app/import
    cap_drop: [all]

  database:
    image: postgres:18-trixie
    restart: always
    environment:
      POSTGRES_USER: teslamate
      POSTGRES_PASSWORD: 请替换为第二段随机值
      POSTGRES_DB: teslamate
    volumes:
      - teslamate-db:/var/lib/postgresql

  grafana:
    image: teslamate/grafana:latest
    restart: always
    environment:
      DATABASE_USER: teslamate
      DATABASE_PASS: 请替换为第二段随机值
      DATABASE_NAME: teslamate
      DATABASE_HOST: database
    ports:
      - "3000:3000"
    volumes:
      - teslamate-grafana-data:/var/lib/grafana

  mosquitto:
    image: eclipse-mosquitto:2
    restart: always
    command: mosquitto -c /mosquitto-no-auth.conf
    volumes:
      - mosquitto-conf:/mosquitto/config
      - mosquitto-data:/mosquitto/data

volumes:
  teslamate-db:
  teslamate-grafana-data:
  mosquitto-conf:
  mosquitto-data:
```

启动并确认四个服务均为运行状态：

```bash
sudo docker compose up -d
sudo docker compose ps
```

首次访问 `http://服务器IP:4000`，按 [TeslaMate 官方授权说明](https://docs.teslamate.org/docs/installation/tokens/) 填写 Tesla access token 与 refresh token。Grafana 默认入口为 `http://服务器IP:3000`，首次账号密码均为 `admin`，登录后立即改成强密码。

## 3. 一次安装中文版与本补丁

基础服务正常后，回到仓库首页的“第 1、2 步”，或直接执行：

```bash
sudo git clone https://github.com/huangkouping/teslamate-cn-patches.git /opt/teslamate-cn-patches
cd /opt/teslamate-cn-patches
sudo bash scripts/install-integrated.sh --compose-file /opt/teslamate/compose.yml
```

它会将官方 Grafana 迁移到中文版并应用导航优化；标准单站点 Nginx 会自动安全配置。随后按首页验收清单检查。
