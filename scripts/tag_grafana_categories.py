#!/usr/bin/env python3
"""Tag teslamate-chinese-dashboards v1.13 dashboard UIDs for grouped navigation."""
import argparse
import base64
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

GROUPS = {
  "nav_common": {"kOuP_Fggz", "jchmo4BNRkZz", "SUBgwtigz", "RG_DxSmgk", "ZzhF-aRWz", "be2m9kga7b8qoc"},
  "nav_vehicle": {"xo4BNRkZz", "jchmkOuP_Fggz", "IiC07mgWz", "q4YF9XA4k", "vehicle-comparison", "jchmDbInfo", "jchmIDopVO_mgz"},
  "nav_charge": {"jchmRiqUfXgTM", "WopVO_mgz", "TSmNYvRRk", "-pkIkhmRz", "BHhxFeZRz", "jchmDdLe5uFVk", "charging-health-cn", "jchm9RxutVS7a", "jchmXpkcccIkh", "jchmXpkIkhmRz", "zhHx2Fggk", "station-ranking"},
  "nav_drive": {"Y8upc6ZRk", "1EZnXszMk", "FkUpJpQZk", "_7WkNSyWk", "jchmY8upc6ZRk", "zm7wN6Zgz", "jchmNjtMTFx", "NjtMTFggz", "fu4SiQgWz", "jchmfu4SiQgWz", "jchm_9z40b", "sentry-drain-cn", "driving-patterns-cn", "regen-braking-cn", "annual-summary-cn", "jchmX8upc6ZRk", "driving-score", "weather-efficiency"},
}

parser = argparse.ArgumentParser()
parser.add_argument("--url", default=os.getenv("GRAFANA_URL", "http://127.0.0.1:3000"))
parser.add_argument("--user", default=os.getenv("GRAFANA_USER", "admin"))
parser.add_argument("--backup-dir", default="./backups")
args = parser.parse_args()
auth = base64.b64encode(f"{args.user}:{os.environ['GRAFANA_PASSWORD']}".encode()).decode()

def api(path, method="GET", payload=None):
    request = Request(args.url.rstrip("/") + path, data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode(), method=method, headers={"Authorization":"Basic " + auth, "Content-Type":"application/json"})
    with urlopen(request, timeout=20) as response: return json.load(response)

def category(uid):
    for tag, uids in GROUPS.items():
        if uid in uids: return tag
    return "nav_analysis"

backup = Path(args.backup_dir) / f"grafana-category-tags-{datetime.now():%Y%m%d-%H%M%S}"
backup.mkdir(parents=True, exist_ok=True)
items = api("/api/search?type=dash-db")
for item in items:
    record = api("/api/dashboards/uid/" + item["uid"])
    (backup / f'{item["uid"]}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    dashboard = record["dashboard"]
    dashboard["tags"] = [tag for tag in dashboard.get("tags", []) if not tag.startswith("nav_")] + [category(item["uid"])]
    api("/api/dashboards/db", "POST", {"dashboard":dashboard, "folderUid":record.get("meta", {}).get("folderUid"), "overwrite":True, "message":"Tag dashboard navigation category"})
print(f"updated={len(items)} backup={backup}")
