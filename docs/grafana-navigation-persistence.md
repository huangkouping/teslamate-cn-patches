# 重启后导航为什么回退，以及怎么彻底解决

> 适用：`teslamate-chinese-dashboards` 这类“面板以文件形式随镜像提供”的部署。
> 对应脚本：`scripts/reapply_grafana_customizations.py`、`scripts/install-navigation-selfheal.sh`、`scripts/enable-zero-window-navigation.py`、`scripts/restore_dashboards.py`。

## 现象

按仓库安装后导航是正常的（首页 / 概况 / 车辆 / 行驶与能耗 / 充电与电池 / 分析与工具 / 说明文档），但 **只要重启过 Grafana 容器，就又变回镜像自带的几个按钮**。

## 原因

面板镜像里有一份 `/etc/grafana/provisioning/dashboards/dashboards.yml`：

```yaml
providers:
  - name: 'teslamate-zh-cn'
    folder: 'TeslaMate'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /dashboards
```

它是 Grafana 的“文件提供器”：镜像启动时按 `/dashboards` 里的 JSON 重新导入面板，面板的 `links`（导航）和 `tags`（分类）就被文件内容覆盖回默认值。本仓库的补丁是通过 API 写进数据库的，因此每次启动都会被抹掉。

这跟本仓库的脚本无关，是上游镜像的设计：文件是真理，数据库只是副本。

## 两种解法

| 方案 | 效果 | 代价 |
| --- | --- | --- |
| A. 自愈定时器 | 重启后最多等一轮（默认 5 分钟）恢复；期间会看到默认导航 | 不碰镜像，风险最低；有窗口期 |
| B. 关闭文件提供器 | **零窗口**，Grafana 一起来就是补丁导航 | 以后镜像升级不会再带来新的官方面板 |

先 A 后 B 也可以：A 随时能装，B 想清楚代价再做。

---

## 方案 A：自愈定时器（推荐先做这一步）

```bash
cd /opt/teslamate-cn-patches
sudo GRAFANA_PASSWORD='你的密码' bash scripts/install-navigation-selfheal.sh \
  --compose-file /opt/teslamate/compose.yml
```

它装两个单元：

- `teslamate-cn-nav.service`：执行 `reapply_grafana_customizations.py`，合并“分类标签 + 导航链接”一次遍历，**内容没变就不写库、不建备份**，所以定时跑不会弄乱数据
- `teslamate-cn-nav.timer`：开机 2 分钟后首跑，之后默认每 5 分钟一轮；`--interval 2` 可改成 2 分钟

验收：

```bash
systemctl list-timers 'teslamate-cn-nav*'
journalctl -u teslamate-cn-nav.service -n 20 --no-pager   # 当前已是补丁状态时应看到 changed=0
```

卸载：`sudo bash scripts/install-navigation-selfheal.sh --uninstall`

---

## 方案 B：零窗口（关掉文件提供器）

### 先理解那个坑

直接把 `/etc/grafana/provisioning/dashboards` 换成空目录时，提供器连同 `disableDeletion: false` 一起消失，Grafana 会把“文件里已经不存在的面板”当作**已删除**，把所有由该提供器导入的面板一并清掉（实测会全部消失）。

所以顺序必须是：**先导出快照 → 再关提供器 → 重启 → 从快照把面板导回（此时它们属于数据库面板，不受文件影响）→ 重新应用导航**。`scripts/enable-zero-window-navigation.py` 把这几步串成了一条命令，每一部都可回滚：

```bash
cd /opt/teslamate-cn-patches
sudo GRAFANA_PASSWORD='你的密码' python3 scripts/enable-zero-window-navigation.py \
  --compose-file /opt/teslamate/compose.yml
```

它会做：

1. 把全部面板导出到 `<compose 目录>/backups/provisioning-off-<时间>/`
2. 备份 Compose，在 grafana 服务的 `volumes` 里加一行只读挂载（空目录顶掉提供器）
3. `docker compose up -d --force-recreate --no-deps grafana`
4. 等 `/api/health` 就绪
5. 从快照导入全部面板（带原文件夹）
6. 重跑导航补丁

### 验收

```bash
docker inspect <grafana 容器> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
# 应看到 .../grafana-provisioning/dashboards -> /etc/grafana/provisioning/dashboards

docker restart <grafana 容器>
# 重启后立刻打开 Grafana：导航应直接是补丁版，面板数量与重启前一致
```

### 代价

- 镜像升级（换 `teslamate-chinese-dashboards` 标签）**不会**再导入新的官方面板；需要新版本面板时，先临时去掉这个挂载跑一次，再关回去。
- 面板从此以数据库为准，建议同时保留方案 A 的定时器作双保险（无改动时它是空跑）。

### 回滚到官方提供器

```bash
# 1) 删掉 Compose 里以 grafana-provisioning 开头的那行挂载
# 2) 重建容器，镜像会重新导入官方文件
# 3) 重跑整合安装，把导航覆盖成补丁版
sudo bash scripts/install-integrated.sh --compose-file /opt/teslamate/compose.yml
```

---

## 万一面板真的被清空了

快照就在 `<compose 目录>/backups/` 下。手动恢复只要一条：

```bash
sudo GRAFANA_PASSWORD='你的密码' python3 scripts/restore_dashboards.py \
  --import /opt/teslamate/backups/provisioning-off-<时间>
```

导入时会带原 `folderUid`，所以面板会回到原来的文件夹（`TeslaMate` / `Internal`）；若原文件夹不存在，会退到 General 并打印提醒。

---

## 边界情况

- **只看健不看窗口**：能接受重启后有几分钟默认导航，装方案 A 就够了。
- **你自己 `docker compose restart` 只重启 Grafana**：文件提供器同样会重新导入，所以两种方案都要提前装好。
- **升级后导航又变了**：新版本可能改面板 UID 或标题。先 `git pull`，重跑 `install-integrated.sh`，再确认分类脚本里的 UID 列表是否需要补充（见 `docs/upgrading.md`）。
- **手动删掉的面板不会自己长回来**：导航是幂等的，但面板本身不会自动重建。
