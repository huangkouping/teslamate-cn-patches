# Grafana 补丁使用说明

以下命令在 Grafana 所在服务器执行。运行前请为 `GRAFANA_PASSWORD` 设置 Grafana 管理员密码；密码不会写入补丁文件。

```bash
export GRAFANA_PASSWORD='你的 Grafana 管理员密码'
python3 scripts/tag_grafana_categories.py --backup-dir ./backups
python3 scripts/patch_overview_empty_state.py --backup-dir ./backups
python3 scripts/sync_grafana_navigation.py --backup-dir ./backups --include-drivo-link
```

## 说明文档菜单

`sync_grafana_navigation.py` 将“说明文档”作为无跳转的菜单触发器。`assets/grafana-nav-order.js` 负责展开以下外部链接：

- TeslaMate官方
- Grafana 中文版仪表盘
- 全中文版补丁

## 分类标签

共享菜单按 `nav_common`、`nav_vehicle`、`nav_drive`、`nav_charge`、`nav_analysis` 标签聚合。`tag_grafana_categories.py` 适配中文版仪表盘 v1.13 的已知页面；不同版本新增页面会默认归入“分析与工具”，之后可按使用逻辑调整标签。
