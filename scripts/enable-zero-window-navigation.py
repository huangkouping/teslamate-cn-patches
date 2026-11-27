#!/usr/bin/env python3
"""让 Grafana 导航在重启后“零等待”保持补丁状态。

原理：面板镜像自带的 /etc/grafana/provisioning/dashboards/dashboards.yml 把 /dashboards
当作文件提供器，每次启动都按文件重新导入面板，把 API 改过的 links / tags 覆盖回默认值。
本脚本用一个空目录顶掉这个提供器，让面板只以数据库为准，启动即可用补丁导航。

执行顺序（每步可回滚）：
  1. 导出全部面板快照到 <compose 目录>/backups/provisioning-off-<时间>/
  2. 备份 Compose，在 grafana 服务的 volumes 里加入只读挂载
  3. 重建 grafana 容器（--force-recreate --no-deps）
  4. 等 /api/health 就绪
  5. 从快照恢复面板——提供器消失时 Grafana 可能把面板当作“文件已删除”清空（实测会发生），这步补回来
  6. 重新应用导航补丁

注意：从此以后镜像升级不会再导入新的官方仪表盘；想恢复官方视图，
删掉该挂载条目并重跑 scripts/install-integrated.sh 即可。

用法：
    sudo GRAFANA_PASSWORD='***' python3 scripts/enable-zero-window-navigation.py --compose-file /opt/teslamate/compose.yml
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--compose-file", required=True, help="TeslaMate 的 Compose 文件路径")
parser.add_argument("--service", default="grafana", help="Grafana 在 Compose 中的服务名（默认 grafana）")
parser.add_argument("--url", default=os.getenv("GRAFANA_URL", "http://127.0.0.1:3000"))
parser.add_argument("--timeout", type=int, default=180, help="等待 Grafana 就绪的秒数")
parser.add_argument("--dry-run", action="store_true", help="只打印将要做的改动，不落盘、不重启")
args = parser.parse_args()

compose = Path(args.compose_file).resolve()
if not compose.is_file():
    sys.exit(f"找不到 Compose 文件：{compose}")
workdir = compose.parent
mount_src = workdir / "grafana-provisioning" / "dashboards"
mount_line = "- ./grafana-provisioning/dashboards:/etc/grafana/provisioning/dashboards:ro"
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
snapshot = workdir / "backups" / f"provisioning-off-{stamp}"


def indent_level(line):
    return len(line) - len(line.lstrip(" "))


def inject_mount(text, service, line):
    lines = text.splitlines(True)
    start = None
    for i, raw in enumerate(lines):
        if re.match(rf"^  {re.escape(service)}\s*:\s*$", raw):
            start = i
            break
    if start is None:
        raise SystemExit(f"Compose 里找不到服务：{service}")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].strip() and indent_level(lines[j]) <= 2:
            end = j
            break
    block = lines[start:end]
    vol_idx = next((k for k, raw in enumerate(block) if re.match(r"^    volumes\s*:\s*$", raw)), None)
    if vol_idx is None:
        raise SystemExit(f"服务 {service} 没有 volumes 段，请手动加一行：{line}")
    last_item = vol_idx
    for k in range(vol_idx + 1, len(block)):
        if re.match(r"^      - ", block[k]):
            last_item = k
        elif block[k].strip() and indent_level(block[k]) <= 4:
            break
    # 兼容用户自己已经做过的手工挂载（目录名不必相同）
    if any("/etc/grafana/provisioning/dashboards" in raw and raw.lstrip().startswith("- ")
           for raw in block):
        return text, False
    new_block = block[: last_item + 1] + [f"      {mount_line}\n"] + block[last_item + 1 :]
    return "".join(lines[:start] + new_block + lines[end:]), True


text = compose.read_text(encoding="utf-8")
new_text, changed = inject_mount(text, args.service, mount_line)
if changed:
    print(f"将向 {compose} 的 {args.service} 服务添加只读挂载：\n  {mount_line}")
else:
    print("Compose 里已经存在 provisioning/dashboards 挂载，跳过修改。")

if args.dry_run:
    print("\n--dry-run：不执行导出、写入、重建与恢复。")
    sys.exit(0)

if os.geteuid() != 0:
    sys.exit("需要 root（挂载目录与 docker compose 都要写权限），请用 sudo 执行。")

# 1) 导出快照
env = dict(os.environ)
if not env.get("GRAFANA_PASSWORD"):
    import getpass
    env["GRAFANA_PASSWORD"] = getpass.getpass("Grafana 管理员密码（不会显示）：")
os.environ["GRAFANA_PASSWORD"] = env["GRAFANA_PASSWORD"]
here = Path(__file__).resolve().parent
subprocess.run([sys.executable, str(here / "restore_dashboards.py"), "--url", args.url,
                "--export", str(snapshot)], check=True)
if not any(snapshot.glob("*.json")):
    sys.exit(f"快照为空（{snapshot}），已停止，未做任何改动。")

# 2) 写 Compose（先备份）
if changed:
    backup = compose.with_suffix(compose.suffix + f".bak-nav-{stamp}")
    shutil.copy2(compose, backup)
    compose.write_text(new_text, encoding="utf-8")
    print(f"Compose 已备份到 {backup}")
mount_src.mkdir(parents=True, exist_ok=True)

# 3) 重建容器
subprocess.run(["docker", "compose", "-f", str(compose), "up", "-d",
                "--force-recreate", "--no-deps", args.service], cwd=str(workdir), check=True)

# 4) 等就绪
print("等待 Grafana 就绪…")
deadline = time.time() + args.timeout
while True:
    try:
        with urllib.request.urlopen(args.url.rstrip("/") + "/api/health", timeout=5) as resp:
            if json.load(resp).get("database") == "ok":
                break
    except Exception:
        pass
    if time.time() > deadline:
        sys.exit("Grafana 未在规定时间内就绪；容器状态请用 docker logs 检查。快照仍在，可手动恢复。")
    time.sleep(2)
print("Grafana 已就绪。")

# 5) 恢复快照（提供器消失可能已经把面板删掉）
subprocess.run([sys.executable, str(here / "restore_dashboards.py"), "--url", args.url,
                "--import", str(snapshot)], check=True)

# 6) 重新应用导航
subprocess.run([sys.executable, str(here / "reapply_grafana_customizations.py"), "--url", args.url],
               check=True, env=dict(os.environ, GRAFANA_PASSWORD=os.environ["GRAFANA_PASSWORD"]))

print(f"\n完成。面板快照：{snapshot}")
print("回滚方法：删掉 Compose 里以 grafana-provisioning 开头的那行挂载，再"
      "docker compose up -d --force-recreate --no-deps grafana，然后重跑 install-integrated.sh。")
