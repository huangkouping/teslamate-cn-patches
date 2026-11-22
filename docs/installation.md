# 安装说明

本仓库是对 TeslaMate 官方与 Grafana 中文版仪表盘的补丁层，不包含完整部署。顺序必须是：**TeslaMate 官方 → 中文版仪表盘 → 本补丁**。

安装前先阅读 [兼容性与版本策略](compatibility.md)，确认自己的版本在支持范围内。

## 0. 安装前检查

- TeslaMate 与 Grafana 已正常运行，且通过 Nginx 对外提供服务。
- 服务器具备 `git`、`python3`、Nginx；若要使用高德底图补丁，还需要 Docker Compose。
- 先备份当前 Nginx 配置。不要把域名、证书、密码、令牌或数据库备份提交到本仓库。

## 1. 获取补丁

```bash
sudo git clone https://github.com/huangkouping/teslamate-cn-patches.git /opt/teslamate-cn-patches
cd /opt/teslamate-cn-patches
```

以后更新本补丁：

```bash
cd /opt/teslamate-cn-patches
sudo git pull
```

仓库中的 `assets/` 文件已经在目标目录内，**不需要再次用 `install` 复制同名文件**。

## 2. 注入浏览器补丁

在现有 HTTPS `server` 块中按 [Nginx 示例](../nginx/teslamate-cn-patches.conf.example) 合并两部分：

1. 两个静态 JavaScript 路由；
2. TeslaMate 的 `location /` 以及 Grafana 的 `location /grafana/` 中的 `sub_filter` 注入片段。

不要直接覆盖你的 `server_name`、TLS 证书、Basic Auth、`proxy_pass` 或访问控制。保存后：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

浏览器强制刷新后，TeslaMate 的控制台菜单应中文分组，车辆位置图标应跳转高德地图；Grafana 应显示分组导航。

## 3. 整理 Grafana 分类和导航

脚本会调用 Grafana API，并在 `./backups` 生成运行前备份。以下命令假设 Grafana 在宿主机 `127.0.0.1:3000`。如果不是，请通过 `GRAFANA_URL` 指定可访问的 Grafana 地址。

```bash
cd /opt/teslamate-cn-patches
export GRAFANA_PASSWORD='你的 Grafana 管理员密码'
# 如有需要，例如：export GRAFANA_URL='http://127.0.0.1:3000'

python3 scripts/tag_grafana_categories.py --backup-dir ./backups
python3 scripts/sync_grafana_navigation.py --backup-dir ./backups
python3 scripts/patch_overview_empty_state.py --backup-dir ./backups
```

需要额外展示“行车视频编辑”时，仅在第二条命令增加 `--include-drivo-link`。该链接不是补丁正常运行的必需项。

## 4. 可选：TeslaMate 4.5.0 高德底图

仅适用于 [兼容性说明](compatibility.md)中列出的 TeslaMate **4.5.0**。脚本先校验官方前端资源的 SHA-256；不匹配时会拒绝执行。

在 Docker Compose 项目目录执行（服务名按官方 compose 文件的 `teslamate`）：

```bash
cd /opt/teslamate-cn-patches
docker compose cp teslamate:/opt/app/lib/teslamate-4.5.0/priv/static/assets/app-50251e2ae44831f4771df63f9253c265.js ./assets/app-50251e2ae44831f4771df63f9253c265-original.js
python3 scripts/patch_teslamate_amap.py \
  ./assets/app-50251e2ae44831f4771df63f9253c265-original.js \
  ./assets/app-50251e2ae44831f4771df63f9253c265-amap.js
```

接着把 [高德地图 Nginx 示例](../nginx/teslamate-amap-4.5.0.conf.example)中的单个 `location` 合并进相同 HTTPS `server` 块，检查并重载 Nginx：

```bash
sudo nginx -t && sudo systemctl reload nginx
```

不要上传 `app-*-original.js` 或生成的 `app-*-amap.js` 到 GitHub；它们属于上游编译资源。升级 TeslaMate 后，应删除生成文件、移除该 Nginx `location`，然后等待新的兼容 Release。

## 5. 验收清单

1. TeslaMate 控制台：中文分组、双列菜单正常；位置图标进入高德地图且定位无偏移。
2. TeslaMate 地图（若执行第 4 步）：右下角显示“高德地图”，放大后的地图仍为高德。
3. Grafana：导航在车/地图/时间等筛选器之前；长下拉菜单为两列。
4. 点击“说明文档”：显示三个外部链接；按钮自身不直接跳转。
5. 概览页在选定时间范围无行程时，三张卡片显示“暂无行驶数据”。

若未生效，先使用无痕窗口或强制刷新；随后检查 Nginx 错误日志，以及 `/teslamate-cn-ui.js`、`/grafana-nav-order.js` 是否返回 HTTP 200。
