#!/usr/bin/env python3
"""TeslaMate 中文导航的唯一权威定义（分组、静音面板、顶栏链接）。

所有需要“分类标签 / 顶栏导航”的脚本都从这里取数据，避免多处写死结构后
彼此漂移：镜像重启或升级后自愈脚本会按这里的定义把导航写回去。

分类（6 个一级菜单，另加首页与帮助两个链接）：
  车况        nav_common   6 项（状态 / 胎压 / 多车对比 / 系统更新 / 数据库信息）
  行程轨迹    nav_trip     9 项
  驾驶与能耗  nav_drive    14 项
  充电统计    nav_charge   12 项（充电 7 项 + 费用 5 项，长菜单内分两列）
  电池        nav_battery  4 项
  帮助        link（前端补丁展开三个外部链接）
"""
import base64
import json
import os
from urllib.request import Request, urlopen

# 车况
COMMON = {
    "jchmo4BNRkZz", "jchmkOuP_Fggz", "q4YF9XA4k", "vehicle-comparison",
    "IiC07mgWz", "jchmDbInfo",
}
# 行程与轨迹
TRIP = {
    "Y8upc6ZRk", "zm7wN6Zgz", "_7WkNSyWk", "1EZnXszMk", "FkUpJpQZk", "jchmY8upc6ZRk",
    "SUBgwtigz", "ZzhF-aRWz", "RG_DxSmgk",
}
# 驾驶与能耗
DRIVE = {
    "driving-score", "jchmX8upc6ZRk", "driving-patterns-cn", "regen-braking-cn",
    "annual-summary-cn", "fu4SiQgWz", "jchm_9z40b", "jchmfu4SiQgWz",
    "NjtMTFggz", "jchmNjtMTFx", "weather-efficiency", "sentry-drain-cn",
    "teslamate-temperatures", "zhHx2Fggk",
}
# 充电统计（充电 7 项 + 费用 5 项）
CHARGE = {
    "jchm9RxutVS7a", "TSmNYvRRk", "BHhxFeZRz", "-pkIkhmRz", "charging-health-cn",
    "jchmXpkIkhmRz", "jchmXpkcccIkh",
    "jchmDdLe5uFVk", "station-ranking", "cost-savings-cn", "tou-config", "jchmAdd4SiQgWa",
}
# 电池
BATTERY = {"jchmRiqUfXgTM", "WopVO_mgz", "riqUfXgRz", "range_degrad_cn"}

GROUPS = {
    "nav_common": COMMON,
    "nav_trip": TRIP,
    "nav_drive": DRIVE,
    "nav_charge": CHARGE,
    "nav_battery": BATTERY,
}

# 以下面板不进任何二级菜单（概览是首页面板、首页/状态为旧版页面、不完整的数据为排障页）
MUTED = {"kOuP_Fggz", "be2m9kga7b8qoc", "xo4BNRkZz", "jchmIDopVO_mgz"}

# 顶栏链接顺序：首页 → 车况 → 行程轨迹 → 驾驶与能耗 → 充电统计 → 电池 → 帮助
NAV_LINKS = [
    {"type": "link", "title": "首页", "tooltip": "最近车辆状态", "icon": "home",
     "url": "/grafana/d/jchmo4BNRkZz", "targetBlank": False, "includeVars": False, "keepTime": False},
    {"type": "dashboards", "title": "车况", "icon": "dashboard", "tags": ["nav_common"], "asDropdown": True},
    {"type": "dashboards", "title": "行程轨迹", "icon": "road", "tags": ["nav_trip"], "asDropdown": True},
    {"type": "dashboards", "title": "驾驶与能耗", "icon": "trending-up", "tags": ["nav_drive"], "asDropdown": True},
    {"type": "dashboards", "title": "充电统计", "icon": "bolt", "tags": ["nav_charge"], "asDropdown": True},
    {"type": "dashboards", "title": "电池", "icon": "battery-bolt", "tags": ["nav_battery"], "asDropdown": True},
    {"type": "link", "title": "帮助", "icon": "doc", "url": "#",
     "targetBlank": False, "includeVars": False, "keepTime": False},
]


def category(uid):
    """返回面板对应的分类标签；静音面板返回 None（会清掉已有 nav_* 标签）。"""
    if uid in MUTED:
        return None
    for tag, uids in GROUPS.items():
        if uid in uids:
            return tag
    return None


def build_links(home_uid="jchmo4BNRkZz"):
    """生成写回 Grafana dashboard 的 links 列表（首页链接可替换 home_uid）。"""
    links = [dict(link) for link in NAV_LINKS]
    links[0] = dict(links[0], url="/grafana/d/" + home_uid)
    return links


def basic_auth(user, password):
    return base64.b64encode(f"{user}:{password}".encode()).decode()


def request_json(url, auth, payload=None, method="GET"):
    request = Request(
        url,
        data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode(),
        method=method,
        headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"},
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310 - 固定为本机 Grafana
        return json.load(response)


def fetch_dashboards(url, auth):
    return request_json(url.rstrip("/") + "/api/search?type=dash-db", auth)


def fetch_dashboard(url, auth, uid):
    return request_json(url.rstrip("/") + "/api/dashboards/uid/" + uid, auth)


def save_dashboard(url, auth, record, dashboard, message):
    payload = {
        "dashboard": dashboard,
        "overwrite": True,
        "message": message,
        "folderUid": (record.get("meta") or {}).get("folderUid"),
    }
    return request_json(url.rstrip("/") + "/api/dashboards/db", auth, payload, "POST")
