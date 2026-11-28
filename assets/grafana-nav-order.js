(() => {
  "use strict";
  const priority = [
    "最近车辆状态",
    "当前驾驶状态",
    "胎压",
    "多车对比",
    "数据库信息",
    "系统更新",
    "行程列表",
    "行程详情",
    "行程统计（汇总)",
    "行程统计（年月日）",
    "行程统计（时间段）",
    "行程统计（每次充电）",
    "时间线",
    "访问过的地点",
    "足迹地图",
    "驾驶评分",
    "驾驶记录追踪",
    "出行规律分析",
    "动能回收分析",
    "年度驾驶报告",
    "能效",
    "速度与温度",
    "最近车速统计",
    "🌡️ 天气-能耗关联",
    "⚡ 行车 vs 停车耗电（月度）",
    "停车电量消耗",
    "历史温度",
    "车辆里程（曲线图）",
    "车辆里程统计",
    "当前充电状态",
    "充电记录",
    "充电详情",
    "充电统计（汇总）",
    "充电健康管理",
    "快充曲线统计",
    "快充曲线图(按运营商)",
    "充电费用统计",
    "🏆 充电桩性价比榜",
    "省钱分析",
    "回本分析",
    "⚡ 分时电价配置",
    "电池健康度",
    "电池容量曲线图",
    "续航曲线图",
    "续航退化分析"
  ];
  const DOC_LABEL = "帮助";
  const DOC_LEGACY_LABEL = "说明文档";
  const rank = new Map(priority.map((title, index) => [title, index]));

  // 长菜单内部分段（仅视觉分组，标题不可点）
  const NAV_SECTIONS = new Map([
    ["驾驶评分", "驾驶"], ["驾驶记录追踪", "驾驶"], ["出行规律分析", "驾驶"],
    ["动能回收分析", "驾驶"], ["年度驾驶报告", "驾驶"],
    ["能效", "能耗"], ["速度与温度", "能耗"], ["最近车速统计", "能耗"],
    ["🌡️ 天气-能耗关联", "能耗"], ["⚡ 行车 vs 停车耗电（月度）", "能耗"],
    ["停车电量消耗", "能耗"], ["历史温度", "能耗"],
    ["车辆里程（曲线图）", "里程"], ["车辆里程统计", "里程"],
    ["当前充电状态", "充电"], ["充电记录", "充电"], ["充电详情", "充电"],
    ["充电统计（汇总）", "充电"], ["充电健康管理", "充电"],
    ["快充曲线统计", "充电"], ["快充曲线图(按运营商)", "充电"],
    ["充电费用统计", "费用"], ["🏆 充电桩性价比榜", "费用"],
    ["省钱分析", "费用"], ["回本分析", "费用"], ["⚡ 分时电价配置", "费用"],
  ]);

  function installStyle() {
    if (document.getElementById("teslamate-grafana-nav-layout")) return;
    const style = document.createElement("style");
    style.id = "teslamate-grafana-nav-layout";
    style.textContent = ".teslamate-nav-section{font-size:11px;letter-spacing:.06em;color:#8b94a3;font-weight:600;padding:8px 12px 2px;pointer-events:none;user-select:none}.teslamate-grafana-nav-large{width:auto!important;min-width:200px!important;max-width:calc(100vw - 24px)!important}.teslamate-grafana-nav-large.teslamate-grafana-nav-single{width:auto!important}.teslamate-grafana-nav-large-grid{display:grid!important;grid-auto-flow:row dense!important;grid-template-columns:repeat(2,max-content);column-gap:8px;row-gap:2px}.teslamate-grafana-nav-large-grid>a{min-width:0;width:100%;white-space:nowrap}.teslamate-grafana-nav-large-grid{column-gap:20px!important}@media(max-width:680px){.teslamate-grafana-nav-large{width:fit-content!important;min-width:0!important;max-width:calc(100vw - 32px)!important;max-height:calc(100vh - 220px)!important;overflow-y:auto!important;overscroll-behavior:contain}.teslamate-grafana-nav-large-grid{display:block!important}.teslamate-grafana-nav-large-grid>a,.teslamate-grafana-nav-large-grid>[data-cn-nav-section]{grid-column:auto!important;white-space:normal!important;width:auto!important}}";
    document.head.appendChild(style);
  }
  function layoutMenu(parent, links, menu) {
    const entries = [];
    let lastSec = null;
    for (const link of links) {
      const sec = NAV_SECTIONS.get(link.textContent.trim()) || null;
      if (sec && sec !== lastSec) entries.push({ sec, link: null, col: 0 });
      lastSec = sec;
      entries.push({ sec: null, link, col: 0 });
    }
    const hasSec = entries.some(e => e.sec);
    if (hasSec) {
      const blocks = [];
      let cur = null;
      for (const e of entries) {
        if (e.sec) { cur = { sec: e.sec, items: [] }; blocks.push(cur); }
        else if (cur) cur.items.push(e.link);
      }
      // 按原始顺序把整块分组切到左右两列：只允许在两块之间断开
      const total = blocks.reduce((sum, b) => sum + b.items.length + 1, 0);
      let split = blocks.length;
      if (blocks.length > 1) {
        let best = null;
        let left = 0;
        for (let k = 1; k < blocks.length; k += 1) {
          left += blocks[k - 1].items.length + 1;
          const diff = Math.abs(left - (total - left));
          if (best === null || diff < best) { best = diff; split = k; }
        }
      }
      blocks.forEach((b, i) => { b.col = i < split ? 1 : 2; });
      let col = 1;
      for (const e of entries) {
        if (e.sec) {
          const b = blocks.find(x => x.sec === e.sec);
          e.col = b.col;
          col = b.col;
        } else {
          e.col = col;
        }
      }
    } else if (links.length >= 9) {
      const half = Math.ceil(links.length / 2);
      let index = 0;
      for (const e of entries) {
        if (!e.link) continue;
        e.col = index < half ? 1 : 2;
        index += 1;
      }
    } else {
      entries.forEach(e => { e.col = 1; });
    }

    const desired = entries.map(e => e.sec ? "S:" + e.sec + ":" + e.col : "L:" + e.link.textContent.trim() + ":" + e.col);
    const known = new Set(links);
    const current = [...parent.children].filter(n => known.has(n) || n.dataset.cnNavSection === "1");
    const extras = [...parent.children].filter(n => !known.has(n) && n.dataset.cnNavSection !== "1");
    const actual = current.map(n => n.dataset.cnNavSection === "1"
      ? "S:" + n.textContent.trim() + ":" + (n.style.gridColumn || "")
      : "L:" + n.textContent.trim() + ":" + (n.style.gridColumn || ""));
    if (!extras.length && desired.length === actual.length && desired.every((d, i) => d === actual[i])) return;
    if (extras.length) return;

    parent.querySelectorAll("[data-cn-nav-section]").forEach(n => n.remove());
    const fragment = document.createDocumentFragment();
    const heads = new Map();
    for (const e of entries) {
      let node;
      if (e.sec) {
        if (!heads.has(e.sec)) {
          const header = document.createElement("div");
          header.className = "teslamate-nav-section";
          header.dataset.cnNavSection = "1";
          header.textContent = e.sec;
          heads.set(e.sec, header);
        }
        node = heads.get(e.sec);
      } else {
        node = e.link;
      }
      node.style.gridColumn = String(e.col);
      fragment.appendChild(node);
    }
    parent.appendChild(fragment);
    menu.classList.add("teslamate-grafana-nav-large");
    const usedCols = new Set(entries.map(e => e.col)).size;
    menu.classList.toggle("teslamate-grafana-nav-single", usedCols === 1);
    parent.classList.toggle("teslamate-grafana-nav-large-grid", usedCols > 1);
  }

  // 窄屏或第二排按钮时，Grafana 会把过高的下拉翻到页面顶部；
  // 这里把菜单重新贴到触发按钮下方，并按剩余高度限高。
  const NAV_TRIGGER_LABELS = ["车况", "行程轨迹", "驾驶与能耗", "充电统计", "电池", "费用",
    "概况", "车辆", "行驶与能耗", "充电与电池", "分析与工具"];
  function anchorMenu(menu) {
    if (!menu.isConnected) return;
    const mr = menu.getBoundingClientRect();
    if (!mr.height) return;
    let best = null;
    document.querySelectorAll('a,button,[role="button"],[role="link"]').forEach(el => {
      if (menu.contains(el)) return;
      const txt = (el.textContent || "").replace(/\s+/g, "");
      const label = NAV_TRIGGER_LABELS.find(l => txt === l || txt.endsWith(l));
      if (!label || txt.length > label.length + 4) return;
      const r = el.getBoundingClientRect();
      if (r.width < 24 || r.height < 16) return;
      const dist = Math.abs(r.left - mr.left) + Math.abs(r.bottom - mr.top) / 4;
      if (!best || dist < best.dist) best = { rect: r, dist };
    });
    if (!best) return;
    const dy = Math.round(best.rect.bottom + 4 - mr.top);
    if (dy > 0) {
      menu.style.translate = "0 " + dy + "px";
      menu.style.maxHeight = Math.max(180, Math.round(window.innerHeight - best.rect.bottom - 14)) + "px";
      menu.style.overflowY = "auto";
    } else {
      menu.style.translate = "";
    }
  }
  function sortMenus() {
    document.querySelectorAll('[role="menu"]').forEach(menu => {
      const links = [...menu.querySelectorAll('a[data-testid="data-testid Dashboard link"]')];
      if (links.length < 2) return;
      const parent = links[0].parentElement;
      if (!parent || !links.every(link => link.parentElement === parent)) return;
      if (links.length >= 9) {
        menu.classList.add("teslamate-grafana-nav-large");
        parent.classList.add("teslamate-grafana-nav-large-grid");
      }
      anchorMenu(menu);
      const ordered = [...links].sort((a, b) => {
        const left = rank.get(a.textContent.trim()) ?? 9999;
        const right = rank.get(b.textContent.trim()) ?? 9999;
        return left - right || a.textContent.localeCompare(b.textContent, "zh-Hans-CN");
      });
      if (!ordered.every((link, index) => link === links[index])) ordered.forEach(link => parent.appendChild(link));
      layoutMenu(parent, ordered, menu);
    });
  }
  function placeNavigationFirst() {
    document.querySelectorAll('div[class*="dashboard-links-controls"]').forEach(nav => {
      const toolbar = nav.parentElement;
      if (toolbar && toolbar.firstElementChild !== nav) toolbar.insertBefore(nav, toolbar.firstElementChild);
    });
  }
  function installDocumentationMenu() {
    if (document.getElementById("teslamate-doc-menu-style")) return;
    const style = document.createElement("style");
    style.id = "teslamate-doc-menu-style";
    style.textContent = ".teslamate-doc-menu{position:fixed;z-index:10000;min-width:240px;padding:7px;background:#20252b;border:1px solid rgba(255,255,255,.12);border-radius:6px;box-shadow:0 8px 24px rgba(0,0,0,.45)}.teslamate-doc-menu a{display:block;padding:10px 12px;border-radius:4px;color:#c8d1dd;text-decoration:none;font-size:14px}.teslamate-doc-menu a:hover{background:rgba(91,155,213,.16);color:#e7f1ff}";
    document.head.appendChild(style);
    document.addEventListener("click", event => {
      const menu = document.getElementById("teslamate-doc-menu");
      if (menu && !menu.contains(event.target) && !event.target.closest('[data-cn-doc-menu="1"]')) menu.remove();
    });
  }
  function docsTrigger(target) {
    const node = target && target.closest && target.closest("a,button,[role=link]");
    if (!node) return null;
    const hit = labelCarrier(node, [DOC_LABEL, DOC_LEGACY_LABEL]);
    return hit ? node : null;
  }
  function openDocumentationMenu(anchor) {
    const old = document.getElementById("teslamate-doc-menu");
    if (old) old.remove();
    const rect = anchor.getBoundingClientRect();
    const menu = document.createElement("div");
    menu.id = "teslamate-doc-menu";
    menu.className = "teslamate-doc-menu";
    menu.style.left = `${Math.max(8, rect.left)}px`;
    menu.style.top = `${Math.min(window.innerHeight - 150, rect.bottom + 6)}px`;
    [["TeslaMate官方", "https://github.com/teslamate-org/teslamate"], ["Grafana 中文版仪表盘", "https://github.com/wjsall/teslamate-chinese-dashboards"], ["全中文版补丁", "https://github.com/huangkouping/teslamate-cn-patches"]].forEach(([label, href]) => {
      const item = document.createElement("a");
      item.href = href; item.target = "_blank"; item.rel = "noopener noreferrer"; item.textContent = label;
      menu.appendChild(item);
    });
    document.body.appendChild(menu);
  }
  function labelCarrier(node, labels) {
    const child = [...node.querySelectorAll("*")].find(el => el.children.length === 0 && labels.includes(el.textContent.trim()));
    if (child) {
      const remainder = node.textContent.replace(child.textContent, "").replace(/\s+/g, "");
      if (!/[\u4e00-\u9fa5A-Za-z0-9]/.test(remainder)) return { label: child.textContent.trim(), carrier: child };
    }
    const direct = node.textContent.trim();
    if (labels.includes(direct)) return { label: direct, carrier: node };
    return null;
  }
  function documentationMenu() {
    document.querySelectorAll("a,button,[role=link]").forEach(node => {
      const hit = labelCarrier(node, [DOC_LABEL, DOC_LEGACY_LABEL, "行车视频编辑"]);
      if (!hit) return;
      if (hit.label === "行车视频编辑") {
        node.style.display = "none";
        return;
      }
      if (hit.label === DOC_LEGACY_LABEL) hit.carrier.textContent = DOC_LABEL;
      node.dataset.cnDocMenu = "1";
    });
    document.querySelectorAll('[role="menu"] a').forEach(node => {
      if (node.textContent.trim() === "首页") node.style.display = "none";
    });
  }
  // 面板列表是异步拉取的，Grafana 会在首帧先渲染“未找到数据面板”空态再填上，造成闪现。
  const EMPTY_LABELS = ["未找到数据面板", "未找到仪表板", "No dashboards found"];
  function emptyTarget(node, label) {
    let target = node;
    const emptyRoot = node.parentElement && node.parentElement.closest(".empty-state");
    if (emptyRoot) target = emptyRoot;
    let hops = 0;
    while (target.parentElement && target.parentElement !== document.body && hops < 3) {
      const parent = target.parentElement;
      if (parent.textContent.trim() !== label) break;
      target = parent;
      hops += 1;
    }
    return target;
  }
  function hideEmptyBlock(node, label) {
    const target = emptyTarget(node, label);
    target.style.visibility = "hidden";
    target.dataset.cnEmptyHidden = "1";
    target.dataset.cnEmptyLabel = label;
  }
  function restoreHidden() {
    document.querySelectorAll('[data-cn-empty-hidden="1"]').forEach(el => {
      const label = el.dataset.cnEmptyLabel || "";
      if (label && el.textContent.trim() === label) return;
      delete el.dataset.cnEmptyHidden;
      delete el.dataset.cnEmptyLabel;
      el.style.visibility = "";
    });
  }
  function blankEmptyState(node) {
    if (!node || node.nodeType !== 1) return;
    if (node.dataset && node.dataset.cnEmptyHidden === "1") return;
    if (!node.children.length) {
      const text = node.textContent.trim();
      if (EMPTY_LABELS.includes(text)) hideEmptyBlock(node, text);
      return;
    }
    if (typeof node.querySelectorAll !== "function") return;
    node.querySelectorAll("span,p,div,h4,td,li").forEach(child => {
      if (child.children.length) return;
      if (child.dataset.cnEmptyHidden === "1") return;
      const text = child.textContent.trim();
      if (EMPTY_LABELS.includes(text)) hideEmptyBlock(child, text);
    });
  }
  installStyle();
  installDocumentationMenu();
  document.addEventListener("pointerdown", event => {
    const anchor = docsTrigger(event.target);
    if (!anchor) return;
    event.preventDefault(); event.stopImmediatePropagation();
    openDocumentationMenu(anchor);
  }, true);
  new MutationObserver(records => {
    for (const record of records) {
      for (const added of record.addedNodes) blankEmptyState(added);
      if (record.type === "characterData") blankEmptyState(record.target.parentNode);
    }
    restoreHidden();
    placeNavigationFirst(); sortMenus(); documentationMenu();
  }).observe(document.documentElement, {childList: true, subtree: true, characterData: true});
  blankEmptyState(document.body);
  placeNavigationFirst();
  sortMenus();
  documentationMenu();
})();
