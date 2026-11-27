#!/usr/bin/env python3
"""导出 / 恢复 Grafana 面板快照（不碰数据库，只走 Grafana API）。

用途：
1. 在改动 Grafana 的面板提供器（provisioning）之前先存一份，出事可直接恢复；
2. 如果镜像自带的文件提供器把面板当成“文件已删除”清空了，用它一次补回来。

快照格式：每个面板一个 <uid>.json，内容就是 Grafana API 返回的记录（dashboard + meta）。
所以文件夹、面板内的链接与标签都会被原样带回。

用法：
    GRAFANA_PASSWORD=... python3 scripts/restore_dashboards.py --export backups/xxx
    GRAFANA_PASSWORD=... python3 scripts/restore_dashboards.py --import backups/xxx
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--url", default=os.getenv("GRAFANA_URL", "http://127.0.0.1:3000"))
parser.add_argument("--user", default=os.getenv("GRAFANA_USER", "admin"))
parser.add_argument("--export", metavar="DIR", help="导出当前全部面板到目录 DIR")
parser.add_argument("--import", dest="import_dir", metavar="DIR", help="从目录 DIR 导入面板")
args = parser.parse_args()

if bool(args.export) == bool(args.import_dir):
    parser.error("需要且只能指定一个参数：--export 或 --import")

password = os.environ["GRAFANA_PASSWORD"]
auth = base64.b64encode(f"{args.user}:{password}".encode()).decode()


def api(path, method="GET", payload=None):
    request = Request(args.url.rstrip("/") + path,
                    data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode(),
                    method=method,
                    headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"})
    with urlopen(request, timeout=20) as response:
        return json.load(response)


if args.export:
    target = Path(args.export)
    target.mkdir(parents=True, exist_ok=True)
    items = api("/api/search?type=dash-db&limit=500")
    for item in items:
        record = api("/api/dashboards/uid/" + item["uid"])
        (target / f"{item['uid']}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"exported={len(items)} dir={target}")
    sys.exit(0)

source = Path(args.import_dir)
files = sorted(source.glob("*.json"))
if not files:
    sys.exit(f"目录里没有 JSON 快照：{source}")

ok = 0
failed = []
for path in files:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failed.append((path.name, f"JSON 解析失败：{exc}"))
        continue
    dashboard = record.get("dashboard", record)
    folder_uid = (record.get("meta") or {}).get("folderUid")
    attempts = [folder_uid, None] if folder_uid else [None]
    for attempt in attempts:
        payload = {"dashboard": dashboard, "overwrite": True, "message": "Restore from snapshot"}
        if attempt:
            payload["folderUid"] = attempt
        try:
            api("/api/dashboards/db", "POST", payload)
            ok += 1
            if folder_uid and attempt != folder_uid:
                failed.append((path.name, "原文件夹不存在，已导入 General"))
            break
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:160]
            if attempt is None or folder_uid is None:
                failed.append((path.name, f"HTTP {exc.code}: {detail}"))
print(f"imported={ok} failed={len(failed)} from={source}")
for name, why in failed[:10]:
    print(f"  ! {name}: {why}")
