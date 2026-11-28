#!/usr/bin/env python3
"""幂等地重新应用 Grafana 中文导航（分类标签 + 共享导航链接）。

分类结构、静音面板与顶栏顺序都来自 scripts/nav_definition.py（唯一权威定义），
本脚本只负责“读 → 对比 → 只在有差异时写回”，因此可以安全地交给 systemd
定时器每 5 分钟跑一次（见 scripts/install-navigation-selfheal.sh）。

- 与 tag_grafana_categories.py / sync_grafana_navigation.py 的关系：那两支适合
  一次性安装；本脚本把两件事合并成一次遍历并做幂等判断，供自愈使用。
- 写回时带 folderUid，避免面板从原文件夹掉回 General。
- 静音面板（概览 / 首页 / 状态 / 不完整的数据）会被清掉 nav_* 标签，不进菜单。

用法：
    GRAFANA_PASSWORD=... python3 scripts/reapply_grafana_customizations.py --backup-dir ./backups
"""
import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import nav_definition as nav

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--url", default=os.getenv("GRAFANA_URL", "http://127.0.0.1:3000"))
parser.add_argument("--user", default=os.getenv("GRAFANA_USER", "admin"))
parser.add_argument("--home-uid", default=os.getenv("GRAFANA_HOME_DASHBOARD_UID", "jchmo4BNRkZz"))
parser.add_argument("--backup-dir", default="./backups")
parser.add_argument("--keep-backups", type=int, default=5, help="保留最近几个备份目录（0 表示不清理）")
parser.add_argument("--dry-run", action="store_true", help="只报告差异，不写回")
parser.add_argument("--quiet", action="store_true", help="只在有改动时输出")
args = parser.parse_args()

auth = nav.basic_auth(args.user, os.environ["GRAFANA_PASSWORD"])
links = nav.build_links(args.home_uid)

backup = None


def ensure_backup():
    global backup
    if backup is not None:
        return backup
    backup = Path(args.backup_dir) / f"grafana-reapply-{datetime.now():%Y%m%d-%H%M%S}"
    backup.mkdir(parents=True, exist_ok=True)
    if args.keep_backups > 0:
        for stale in sorted(p for p in Path(args.backup_dir).glob("grafana-reapply-*") if p.is_dir())[:-args.keep_backups]:
            shutil.rmtree(stale, ignore_errors=True)
    return backup


changed = 0
counts = {}
for item in nav.fetch_dashboards(args.url, auth):
    uid = item["uid"]
    record = nav.fetch_dashboard(args.url, auth, uid)
    dashboard = record["dashboard"]
    original = json.dumps({k: dashboard.get(k) for k in ("tags", "links")}, ensure_ascii=False, sort_keys=True)

    tag = nav.category(uid)
    counts[tag or "(无菜单)"] = counts.get(tag or "(无菜单)", 0) + 1
    tags = [t for t in dashboard.get("tags", []) if not t.startswith("nav_")]
    if tag:
        tags.append(tag)
    dashboard["tags"] = tags
    dashboard["links"] = [dict(link) for link in links]

    if json.dumps({k: dashboard.get(k) for k in ("tags", "links")}, ensure_ascii=False, sort_keys=True) == original:
        continue
    if args.dry_run:
        changed += 1
        continue
    (ensure_backup() / f"{uid}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    nav.save_dashboard(args.url, auth, record, dashboard, "Reapply shared navigation")
    changed += 1

summary = "changed={} total={} ".format(changed, sum(counts.values()))
summary += " ".join(f"{k[4:] if k.startswith('nav_') else k}={v}" for k, v in sorted(counts.items()))
if changed or not args.quiet:
    print(summary + (f" backup={backup}" if backup else (" (dry-run)" if args.dry_run else "")))
