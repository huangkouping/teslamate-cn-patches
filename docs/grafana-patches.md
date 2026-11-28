# Grafana 补丁使用说明

以下命令在 Grafana 所在服务器执行。运行前请为 `GRAFANA_PASSWORD` 设置 Grafana 管理员密码；密码不会写入补丁文件。

```bash
export GRAFANA_PASSWORD='你的 Grafana 管理员密码'
python3 scripts/tag_grafana_categories.py --backup-dir ./backups
python3 scripts/patch_overview_empty_state.py --backup-dir ./backups
python3 scripts/sync_grafana_navigation.py --backup-dir ./backups
```

## 帮助菜单

`sync_grafana_navigation.py` 将“帮助”作为无跳转的菜单触发器。`assets/grafana-nav-order.js` 负责展开以下外部链接：

- TeslaMate官方
- Grafana 中文版仪表盘
- 全中文版补丁

## 分类标签

共享菜单按 `nav_common`（车况）、`nav_trip`（行程轨迹）、`nav_drive`（驾驶与能耗）、`nav_charge`（充电统计，含费用）、`nav_battery`（电池）标签聚合，定义集中在 `scripts/nav_definition.py`。该文件同时声明了静音面板（概览 / 首页 / 状态 / 不完整的数据，不进菜单）。中文版仪表盘 v1.13 的 UID 已覆盖；新版本新增页面默认不进菜单，需要时在 `nav_definition.py` 里归类，再跑一次自愈即可。
