# TeslaMate CN Patches

一组可复用的 TeslaMate 中国使用体验补丁。它不替代 [TeslaMate](https://github.com/teslamate-org/teslamate) 或 [teslamate-chinese-dashboards](https://github.com/wjsall/teslamate-chinese-dashboards)，而是在它们之上提供更适合中国用户的界面体验。

## 当前包含

- TeslaMate 原生界面：中文控制台菜单、分组、双列布局。
- 车辆位置：Google Maps 跳转改为高德地图，并将 WGS-84 坐标转换为 GCJ-02，避免中国境内定位偏移。
- Grafana：将导航置于变量与时间筛选器之前；长菜单自动双列显示，并按常用、行驶、充电、电池和分析的使用顺序排列。

## 明确不包含

- 任何域名、IP、私钥、令牌、数据库备份或车辆数据。
- 地址表的中文化/修复。地址文字来自每个实例自己的地理编码结果，属于数据问题，不是通用 UI 补丁。
- 已编译的 TeslaMate 前端资产；它会随 TeslaMate 版本变化，不能直接跨版本复用。

## 安装概览

1. 将 `assets/teslamate-cn-ui.js` 和 `assets/grafana-nav-order.js` 放在服务器的独立自定义目录，例如 `/opt/teslamate-cn-patches/assets/`。
2. 将 `nginx/teslamate-cn-patches.conf.example` 中相应片段合并到现有反向代理配置；不要覆盖自己的 TLS、域名或访问控制设置。
3. 检查并重载 Nginx，再以浏览器无痕窗口验证。

详见 [安装说明](docs/installation.md) 与 [升级与回归验证](docs/upgrading.md)。

## 兼容性

本仓库初始版本在 TeslaMate 4.5.x 与 `teslamate-chinese-dashboards` v1.13.0 环境验证。不同版本的 DOM 或仪表盘名称可能变化；升级后请按升级文档验证。

## 贡献

欢迎提交可复用且不含个人数据的改进。请勿提交数据库导出、截图中可识别的地址、令牌、私钥、域名或服务器配置。

## 许可证

尚未选择许可证。在添加许可证前，仓库内容仅供查看，不默认授予再分发或修改授权。
