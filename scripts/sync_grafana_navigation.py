#!/usr/bin/env python3
"""Apply the shared Grafana navigation links to every dashboard, with backups."""
import argparse
import base64
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--url", default=os.getenv("GRAFANA_URL", "http://127.0.0.1:3000"))
parser.add_argument("--user", default=os.getenv("GRAFANA_USER", "admin"))
parser.add_argument("--home-uid", default=os.getenv("GRAFANA_HOME_DASHBOARD_UID", "jchmo4BNRkZz"))
parser.add_argument("--backup-dir", default="./backups")
parser.add_argument("--include-drivo-link", action="store_true", help="Add the optional App Store video-editor link")
args = parser.parse_args()
password = os.environ["GRAFANA_PASSWORD"]
auth = base64.b64encode(f"{args.user}:{password}".encode()).decode()

def api(path, method="GET", payload=None):
    request = Request(args.url.rstrip("/") + path,
                      data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode(),
                      method=method,
                      headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"})
    with urlopen(request, timeout=20) as response:
        return json.load(response)

links = [
  {"type":"link", "title":"首页", "tooltip":"最近车辆状态", "icon":"home", "url":"/grafana/d/" + args.home_uid, "targetBlank":False, "includeVars":False, "keepTime":False},
  {"type":"dashboards", "title":"概况", "icon":"dashboard", "tags":["nav_common"], "asDropdown":True},
  {"type":"dashboards", "title":"车辆", "icon":"car", "tags":["nav_vehicle"], "asDropdown":True},
  {"type":"dashboards", "title":"行驶与能耗", "icon":"road", "tags":["nav_drive"], "asDropdown":True},
  {"type":"dashboards", "title":"充电与电池", "icon":"bolt", "tags":["nav_charge"], "asDropdown":True},
  {"type":"dashboards", "title":"分析与工具", "icon":"apps", "tags":["nav_analysis"], "asDropdown":True},
  {"type":"link", "title":"说明文档", "icon":"doc", "url":"#", "targetBlank":False, "includeVars":False, "keepTime":False},
]
if args.include_drivo_link:
    links.append({"type":"link", "title":"行车视频编辑", "icon":"external link", "url":"https://apps.apple.com/cn/app/drivo-%E8%BD%A6%E8%AE%B0/id6773553521", "targetBlank":True, "includeVars":False, "keepTime":False})

backup = Path(args.backup_dir) / f"grafana-navigation-{datetime.now():%Y%m%d-%H%M%S}"
backup.mkdir(parents=True, exist_ok=True)
items = api("/api/search?type=dash-db")
for item in items:
    record = api("/api/dashboards/uid/" + item["uid"])
    (backup / f'{item["uid"]}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    dashboard = record["dashboard"]
    dashboard["links"] = links
    api("/api/dashboards/db", "POST", {"dashboard": dashboard, "folderUid": record.get("meta", {}).get("folderUid"), "overwrite": True, "message": "Sync shared navigation"})
print(f"updated={len(items)} backup={backup}")
