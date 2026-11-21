#!/usr/bin/env python3
"""Clarify selected-time-range cards and their empty state on the overview dashboard."""
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
parser.add_argument("--dashboard-uid", default="kOuP_Fggz")
parser.add_argument("--backup-dir", default="./backups")
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

record = api("/api/dashboards/uid/" + args.dashboard_uid)
backup = Path(args.backup_dir)
backup.mkdir(parents=True, exist_ok=True)
(backup / f"overview-before-empty-state-{datetime.now():%Y%m%d-%H%M%S}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

titles = {
    14: "平均能耗（净值，当前时段）",
    22: "平均能耗（总计，当前时段）",
    24: "本时段行驶里程",
}
changed = []
def walk(panels):
    for panel in panels:
        if panel.get("id") in titles:
            panel["title"] = titles[panel["id"]]
            panel.setdefault("fieldConfig", {}).setdefault("defaults", {})["noValue"] = "暂无行驶数据"
            changed.append(panel["id"])
        walk(panel.get("panels", []))

dashboard = record["dashboard"]
walk(dashboard.get("panels", []))
if set(changed) != set(titles):
    raise SystemExit(f"Expected panel IDs {sorted(titles)}, found {sorted(changed)}. Stop without saving.")
api("/api/dashboards/db", "POST", {"dashboard": dashboard, "folderUid": record.get("meta", {}).get("folderUid"), "overwrite": True, "message": "Clarify time-range empty state"})
print("updated panels:", ", ".join(map(str, changed)))
