# 从零开始安装：TeslaMate、中文版仪表盘与中文优化补丁

这是一份给第一次部署 TeslaMate 的完整说明。按本文操作后，你会得到：

- 官方 TeslaMate 4.5.0；
- `teslamate-chinese-dashboards` v1.13.0 中文版仪表盘；
- 本仓库的高德定位跳转、中文菜单、Grafana 分组导航等优化。

本仓库不是 TeslaMate 的替代品，而是安装在 **官方 TeslaMate + 中文版仪表盘** 之上的补丁层。当前经过完整验证的组合是：TeslaMate **4.5.0**、中文版仪表盘 **v1.13.0**、本补丁 **v1.2.1**。不要把“最新版”直接替换进这套组合；有新版本时，以 [兼容性页面](compatibility.md) 和 [Releases](https://github.com/huangkouping/teslamate-cn-patches/releases) 标明的支持范围为准。

已有 TeslaMate 的用户不要重复执行本页的一键脚本，以免覆盖现有 Compose 配置；请改看 [已有系统安装与升级](installation.md)。

## 开始前：准备什么

需要一台持续在线的 Linux 服务器，使用 root 登录，或能执行 `sudo`。一键脚本支持带有 `apt-get`、`dnf` 或 `yum` 的常见发行版。建议至少 2 GB 内存、10 GB 可用磁盘空间。

服务器必须能访问 GitHub、Docker 镜像仓库和 Tesla 相关服务。中国大陆服务器若不能直连这些服务，应先按你的网络环境配置可用代理或镜像加速；网络不通时不要反复重试安装器，也不要混用不同来源或不同版本的镜像。

开始前还请确认：

1. 服务器防火墙暂时仅允许你自己的 SSH 来源；不要先把 4000、3000、1883 端口向所有公网开放。
2. 你准备好 Tesla 账号。安装完成后还需要在网页内按 [TeslaMate 官方授权流程](https://docs.teslamate.org/docs/installation/tokens/) 填入 Tesla access token 与 refresh token。
3. 如要长期从公网访问，准备好域名、HTTPS 证书和反向代理（推荐 Nginx、VPN 或 Cloudflare Tunnel）。

## 推荐方式：一条命令完成基础安装

以 root 或具备 sudo 权限的用户登录服务器，直接运行：

```bash
curl -fsSL https://raw.githubusercontent.com/huangkouping/teslamate-cn-patches/main/scripts/install-from-zero.sh | sudo bash
```

脚本会按以下顺序执行，无需先手动安装 Docker：

1. 检查 `curl`、Git、OpenSSL、Docker 和 Docker Compose；缺少基础工具时先用系统包管理器安装。
2. 没有 Docker 时，使用 [Docker 官方安装脚本](https://docs.docker.com/engine/install/) 安装 Docker，并启动 Docker 服务。
3. 在 `/opt/teslamate` 创建官方基础服务、生成数据库密码和 TeslaMate 加密密钥。
4. 启动 TeslaMate 4.5.0、PostgreSQL、Grafana 和 MQTT。
5. 自动迁移已验证的中文版仪表盘 v1.13.0，并应用本仓库的 Grafana 导航优化；若已检测到标准 Nginx 站点，也会注入原生页面优化。
6. 在终端显示 Grafana 初始密码。

安装过程会下载镜像，因此首次耗时主要取决于服务器网络。若中途因网络问题失败，先解决网络或代理问题；确认 `/opt/teslamate/compose.yml` 是否已经生成。为防止覆盖数据，一键脚本发现该文件已存在时会主动停止，而不会覆盖原部署。

## 安装完成后必须做的配置

### 1. 保存密码与密钥

脚本生成的密钥文件是：`/opt/teslamate/.env`。它仅 root 可读，包含：

- `ENCRYPTION_KEY`：TeslaMate 加密密钥；
- `DATABASE_PASS`：数据库密码；
- `GRAFANA_PASSWORD`：Grafana 的 `admin` 初始密码。

请将这三个值保存到自己的密码管理器或离线安全位置。不要把 `.env` 发给他人、贴到聊天记录、提交到 GitHub 或上传公开网盘。需要再次查看时，在服务器上执行：

```bash
sudo cat /opt/teslamate/.env
```

### 2. 完成 Tesla 账号授权

在服务器自身或已受防火墙保护的网络中打开：

```text
http://服务器IP:4000
```

按照 [官方 Token 说明](https://docs.teslamate.org/docs/installation/tokens/) 生成并填写 Tesla access token 与 refresh token。授权完成后，TeslaMate 才会开始记录车辆数据。

如果之后改用域名 HTTPS 访问，请在 TeslaMate 的 **设置 → URLs** 中填写实际的 Web App URL 和 Dashboards URL，例如 `https://tesla.example.com` 与 `https://tesla.example.com/grafana/`。这样 TeslaMate 与 Grafana 的互相跳转才会正确。

### 3. 登录 Grafana

打开：

```text
http://服务器IP:3000
```

用户名为 `admin`，密码使用刚才终端显示或 `/opt/teslamate/.env` 中的 `GRAFANA_PASSWORD`。登录后可在 Grafana 中改为自己记得住的强密码；改完后同步更新你自己的密码记录。今后单独重跑补丁安装器时，它会询问当时实际生效的 Grafana 管理员密码。

### 4. 确认服务全部运行

```bash
cd /opt/teslamate
sudo docker compose ps
```

正常时 `teslamate`、`database`、`grafana`、`mosquitto` 都应显示为运行状态。若某项没有运行，先看对应日志：

```bash
cd /opt/teslamate
sudo docker compose logs --tail=100 teslamate
sudo docker compose logs --tail=100 grafana
```

## 域名、HTTPS 与公网访问

一键脚本不会替你猜测域名、证书来源、云防火墙或访问策略。它创建的 Compose 配置包含 4000 和 3000 端口映射；如果你的云防火墙已放行这些端口，它们就可能被公网访问。因此应在安装后立即完成下面的安全配置，再对外长期使用。推荐流程是：

1. 先让域名解析到服务器公网 IP；
2. 使用你自己的 Nginx 和证书配置 HTTPS；
3. 仅由 Nginx 对外开放 80/443，Docker 的 4000、3000、1883 端口仅限内网或防火墙白名单；
4. 为 TeslaMate 和 Grafana 加上访问限制（VPN、Cloudflare Access、Basic Auth 或 IP 白名单至少选择一种）。

Nginx 已准备好以后，运行下面命令注入浏览器补丁。它只会自动处理能安全识别的单个 TeslaMate 站点，不会猜测多个站点配置：

```bash
cd /opt/teslamate-cn-patches
sudo python3 scripts/configure_nginx.py --root /opt/teslamate-cn-patches
```

脚本会备份配置、写入补丁、执行 `nginx -t` 并重载；验证不通过会自动恢复，不能验证时不要强行重载。若服务器有多个站点，脚本会列出候选文件；从输出中复制 TeslaMate 对应的那一个，再运行同一命令并加 `--config` 参数。若你的 Nginx 还没有配置，请先按自己的域名和证书方案完成它，再执行上面的命令。可对照 [Nginx 示例](../nginx/teslamate-cn-patches.conf.example)，但不要用示例覆盖自己的 `server_name`、证书、访问控制或 `proxy_pass`。

## 中国大陆服务器的网络说明

TeslaMate 需要访问 Tesla 服务；安装还会从 GitHub 和 Docker 镜像仓库下载内容。部分大陆服务器不能稳定直接访问这些外部服务，表现为 `git clone`、拉取镜像或地名反查超时。这是网络连通性问题，不是补丁安装错误。

请在安装前让服务器具备可用的外网代理或镜像加速，并确认代理对 Docker 拉取镜像同样生效。安装脚本不会保存你的代理账号、代理密码或 Telegram 等无关密钥。代理、域名和证书的具体写法取决于你的服务器环境，因此请使用你已验证可用的网络方案；不要把敏感代理凭据写进本仓库。

## 安装后的功能验收

浏览器使用无痕窗口或强制刷新后，检查：

1. TeslaMate 原生控制台显示中文菜单和分类；车辆位置图标跳转到高德地图，位置不偏移。
2. Grafana 的导航位于车辆、地图、时间等筛选器之前；“概况、车辆、行驶与能耗、充电与电池、分析与工具”分类清晰，长菜单会双列显示。
3. “说明文档”按钮本身不跳转；点击后显示 TeslaMate官方、Grafana 中文版和全中文版补丁三个链接。
4. 概览页在筛选时间范围内没有行程时，能耗和里程卡片显示“暂无行驶数据”，而不是空白。
5. 若你按 [可选高德底图步骤](installation.md#5-可选teslamate-450-高德底图) 安装了底图补丁，地图右下角显示“高德地图”，放大后仍是高德底图。

## 常见问题

### 一键脚本提示已有 Compose 配置

这是保护机制，说明 `/opt/teslamate/compose.yml` 已存在。不要删除它来强行重装。已有系统请按 [安装说明](installation.md) 或 [升级说明](upgrading.md) 操作，并先做好数据库与 Compose 配置备份。

### 拉取镜像、GitHub 下载或地图地址反查超时

先排查服务器的网络、DNS、代理或镜像加速。确认外网可用后再继续；反复切换来源会造成版本不可复现。大陆服务器尤其要确保 Docker 守护进程也能通过你的网络方案拉取镜像。

### 浏览器打开页面但菜单没有变化

先强制刷新或使用无痕窗口，排除浏览器缓存；再检查 Nginx 是否已成功注入脚本，以及 `/teslamate-cn-ui.js` 和 `/grafana-nav-order.js` 是否返回 HTTP 200。更详细排查见 [安装说明](installation.md#6-验收清单)。

### 想更新 TeslaMate 或中文版仪表盘

先看 [兼容性与版本策略](compatibility.md)，再按 [升级说明](upgrading.md) 操作。只有 Release 明确列为支持的版本组合才建议升级；升级完成后需要重新运行整合安装，以恢复仪表盘分类和导航。

## 已有系统、手动安装与高级配置

已有 TeslaMate、希望手动执行每一步，或需要单独重跑 Grafana 分类、原生地图补丁的用户，请阅读：

- [安装说明](installation.md)：已有部署的整合安装、Nginx 注入、单独补丁和验收；
- [升级说明](upgrading.md)：官方、中文版和补丁层的正确升级顺序；
- [兼容性与版本策略](compatibility.md)：当前支持版本以及版本不匹配时的处理原则；
- [TeslaMate 官方 Docker 安装文档](https://docs.teslamate.org/docs/installation/docker/)：官方服务架构和运行要求。
