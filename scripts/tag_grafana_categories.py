#!/usr/bin/env python3
"""按 scripts/nav_definition.py 的分类给面板打 nav_* 标签（一次性安装用）。

导航结构的权威定义在 nav_definition.py；本脚本只写标签，不碰顶栏链接。
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
parser.add_argument("--backup-dir", default="./backups")
args = parser.parse_args()

auth = nav.basic_auth(args.user, os.environ["GRAFANA_PASSWORD"])
backup = Path(args.backup_dir) / f"grafana-category-tags-{datetime.now():%Y%m%d-%H%M%S}"
backup.mkdir(parents=True, exist_ok=True)

items = nav.fetch_dashboards(args.url, auth)
for item in items:
    record = nav.fetch_dashboard(args.url, auth, item["uid"])
    (backup / f'{item["uid"]}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    dashboard = record["dashboard"]
    tags = [tag for tag in dashboard.get("tags", []) if not tag.startswith("nav_")]
    tag = nav.category(item["uid"])
    if tag:
        tags.append(tag)
    dashboard["tags"] = tags
    nav.save_dashboard(args.url, auth, record, dashboard, "Tag dashboard navigation category")
print(f"updated={len(items)} backup={backup}")
