#!/usr/bin/env python3
"""幂等地重新应用 Grafana 中文导航（分类标签 + 共享导航链接）。

与 tag_grafana_categories.py / sync_grafana_navigation.py 的关系：
- 这两支脚本各扫一遍面板、各写一次库，适合一次性安装；
- 本脚本把两件事合并成一次遍历，并且只在内容真的变化时才写回，
  因此可以安全地交给 systemd 定时器每 5 分钟跑一次（见 install-navigation-selfheal.sh）；
- 写回时带 folderUid，避免面板从原文件夹掉回 General。

用法：
    GRAFANA_PASSWORD=... python3 scripts/reapply_grafana_customizations.py --backup-dir ./backups
"""
import argparse
import base64
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

GROUPS = {
    "nav_common": {"kOuP_Fggz", "jchmo4BNRkZz", "SUBgwtigz", "RG_DxSmgk", "ZzhF-aRWz", "be2m9kga7b8qoc"},
    "nav_vehicle": {"xo4BNRkZz", "jchmkOuP_Fggz", "IiC07mgWz", "q4YF9XA4k", "vehicle-comparison", "jchmDbInfo", "jchmIDopVO_mgz"},
    "nav_charge": {"jchmRiqUfXgTM", "WopVO_mgz", "TSmNYvRRk", "-pkIkhmRz", "BHhxFeZRz", "jchmDdLe5uFVk", "charging-health-cn", "jchm9RxutVS7a", "jchmXpkcccIkh", "jchmXpkIkhmRz", "zhHx2Fggk", "station-ranking"},
    "nav_drive": {"Y8upc6ZRk", "1EZnXszMk", "FkUpJpQZk", "_7WkNSyWk", "jchmY8upc6ZRk", "zm7wN6Zgz", "jchmNjtMTFx", "NjtMTFggz", "fu4SiQgWz", "jchmfu4SiQgWz", "jchm_9z40b", "sentry-drain-cn", "driving-patterns-cn", "regen-braking-cn", "annual-summary-cn", "jchmX8upc6ZRk", "driving-score", "weather-efficiency"},
}

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--url", default=os.getenv("GRAFANA_URL", "http://127.0.0.1:3000"))
parser.add_argument("--user", default=os.getenv("GRAFANA_USER", "admin"))
parser.add_argument("--home-uid", default=os.getenv("GRAFANA_HOME_DASHBOARD_UID", "jchmo4BNRkZz"))
parser.add_argument("--backup-dir", default="./backups")
parser.add_argument("--keep-backups", type=int, default=5, help="保留最近几个备份目录（0 表示不清理）")
parser.add_argument("--include-drivo-link", action="store_true", help="追加可选的 App Store 行车视频编辑入口")
parser.add_argument("--dry-run", action="store_true", help="只报告差异，不写回")
parser.add_argument("--quiet", action="store_true", help="只在有改动时输出")
args = parser.parse_args()

links = [
    {"type": "link", "title": "首页", "tooltip": "最近车辆状态", "icon": "home",
     "url": "/grafana/d/" + args.home_uid, "targetBlank": False, "includeVars": False, "keepTime": False},
    {"type": "dashboards", "title": "概况", "icon": "dashboard", "tags": ["nav_common"], "asDropdown": True},
    {"type": "dashboards", "title": "车辆", "icon": "car", "tags": ["nav_vehicle"], "asDropdown": True},
    {"type": "dashboards", "title": "行驶与能耗", "icon": "road", "tags": ["nav_drive"], "asDropdown": True},
    {"type": "dashboards", "title": "充电与电池", "icon": "bolt", "tags": ["nav_charge"], "asDropdown": True},
    {"type": "dashboards", "title": "分析与工具", "icon": "apps", "tags": ["nav_analysis"], "asDropdown": True},
    {"type": "link", "title": "说明文档", "icon": "doc", "url": "#",
     "targetBlank": False, "includeVars": False, "keepTime": False},
]
if args.include_drivo_link:
    links.append({"type": "link", "title": "行车视频编辑", "icon": "external link",
                  "url": "https://apps.apple.com/cn/app/drivo-%E8%BD%A6%E8%AE%B0/id6773553521",
                  "targetBlank": True, "includeVars": False, "keepTime": False})

password = os.environ["GRAFANA_PASSWORD"]
auth = base64.b64encode(f"{args.user}:{password}".encode()).decode()


def api(path, method="GET", payload=None):
    request = Request(args.url.rstrip("/") + path,
                      data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode(),
                      method=method,
                      headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"})
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def category(uid):
    for tag, uids in GROUPS.items():
        if uid in uids:
            return tag
    return "nav_analysis"


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
for item in api("/api/search?type=dash-db"):
    uid = item["uid"]
    record = api("/api/dashboards/uid/" + uid)
    dashboard = record["dashboard"]
    original = json.dumps({k: dashboard.get(k) for k in ("tags", "links")}, ensure_ascii=False, sort_keys=True)

    tag = category(uid)
    counts[tag] = counts.get(tag, 0) + 1
    tags = [t for t in dashboard.get("tags", []) if not t.startswith("nav_")]
    dashboard["tags"] = tags + [tag]
    dashboard["links"] = [dict(link) for link in links]

    if json.dumps({k: dashboard.get(k) for k in ("tags", "links")}, ensure_ascii=False, sort_keys=True) == original:
        continue
    if args.dry_run:
        changed += 1
        continue
    (ensure_backup() / f"{uid}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    api("/api/dashboards/db", "POST", {
        "dashboard": dashboard,
        "folderUid": record.get("meta", {}).get("folderUid"),
        "overwrite": True,
        "message": "Reapply shared navigation",
    })
    changed += 1

summary = "changed={} total={} " .format(changed, sum(counts.values()))
summary += " ".join(f"{k[4:]}={v}" for k, v in sorted(counts.items()))
if changed or not args.quiet:
    print(summary + (f" backup={backup}" if backup else (" (dry-run)" if args.dry_run else "")))
