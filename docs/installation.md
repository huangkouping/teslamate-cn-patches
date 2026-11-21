# 安装说明

## 前提

- TeslaMate 与 Grafana 已通过 Nginx 对外提供服务。
- 已备份现有 Nginx 配置。
- 前端资源存放在容器外的持久化目录，避免容器升级时被覆盖。

## 放置资源

```bash
sudo install -d -m 0755 /opt/teslamate-cn-patches/assets
sudo install -m 0644 assets/teslamate-cn-ui.js /opt/teslamate-cn-patches/assets/
sudo install -m 0644 assets/grafana-nav-order.js /opt/teslamate-cn-patches/assets/
```

## 合并 Nginx 片段

打开当前 TeslaMate 的 HTTPS server 配置，参考 `nginx/teslamate-cn-patches.conf.example`：

- 增加两个静态 JavaScript 文件的 `location =` 块；
- 在 TeslaMate 的 `location /` 内注入 `teslamate-cn-ui.js`；
- 在 Grafana 的 `location /grafana/` 内注入 `grafana-nav-order.js`。

不要直接用示例文件覆盖现有配置，尤其不要替换 `server_name`、证书、认证或代理地址。

完成后：

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 验证

- TeslaMate 原生控制台：控制台菜单显示中文分组，车辆位置图标跳转到高德。
- Grafana：导航按钮位于车/地图等变量之前；较长的下拉导航应为两列。
- 浏览器开发者工具 Network：两个脚本返回 HTTP 200。

若没有生效，请先用无痕窗口或硬刷新排除缓存。
