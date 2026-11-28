#!/usr/bin/env python3
"""把 scripts/nav_definition.py 定义的共享顶栏链接写到每个面板（一次性安装用）。

与 reapply_grafana_customizations.py 的区别：本脚本不判断差异，直接全量写回并备份；
日常与重启后的自愈由 reapply 脚本负责。
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import nav_definition as nav

parser = argparse.ArgumentParser()
parser.add_argument("--url", default=os.getenv("GRAFANA_URL", "http://127.0.0.1:3000"))
parser.add_argument("--user", default=os.getenv("GRAFANA_USER", "admin"))
parser.add_argument("--home-uid", default=os.getenv("GRAFANA_HOME_DASHBOARD_UID", "jchmo4BNRkZz"))
parser.add_argument("--backup-dir", default="./backups")
args = parser.parse_args()

auth = nav.basic_auth(args.user, os.environ["GRAFANA_PASSWORD"])
links = nav.build_links(args.home_uid)
backup = Path(args.backup_dir) / f"grafana-navigation-{datetime.now():%Y%m%d-%H%M%S}"
backup.mkdir(parents=True, exist_ok=True)

items = nav.fetch_dashboards(args.url, auth)
for item in items:
    record = nav.fetch_dashboard(args.url, auth, item["uid"])
    (backup / f'{item["uid"]}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    dashboard = record["dashboard"]
    dashboard["links"] = [dict(link) for link in links]
    nav.save_dashboard(args.url, auth, record, dashboard, "Sync shared navigation")
print(f"updated={len(items)} backup={backup}")
