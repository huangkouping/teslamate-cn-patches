(() => {
  "use strict";
  const priority = [
    "首页", "概览", "最近车辆状态", "当前驾驶状态", "当前充电状态", "状态", "时间线", "访问过的地点", "足迹地图",
    "行程列表", "行程详情", "行程统计（汇总)", "行程统计（汇总）", "行程统计（年月日）", "行程统计（时间段）", "行程统计（每次充电）", "车辆里程（曲线图）", "车辆里程统计", "最近车速统计", "能效", "速度与温度", "动能回收分析", "驾驶评分", "驾驶记录追踪", "出行规律分析", "年度驾驶报告", "天气-能耗关联", "🌡️ 天气-能耗关联", "停车电量消耗",
    "电池健康度", "电池容量曲线图", "续航曲线图", "续航退化分析", "充电健康管理", "当前充电状态", "充电记录", "充电详情", "充电统计（汇总）", "充电费用统计", "快充曲线统计", "快充曲线图(按运营商)", "充电桩性价比榜", "🏆 充电桩性价比榜",
    "胎压", "多车对比", "数据库信息", "系统更新", "不完整的数据",
    "分时电价配置", "⚡ 分时电价配置", "行车 vs 停车耗电（月度）", "⚡ 行车 vs 停车耗电（月度）", "省钱分析", "回本分析"
  ];
  const rank = new Map(priority.map((title, index) => [title, index]));
  function installStyle() {
    if (document.getElementById("teslamate-grafana-nav-layout")) return;
    const style = document.createElement("style");
    style.id = "teslamate-grafana-nav-layout";
    style.textContent = ".teslamate-grafana-nav-large{width:540px!important;max-width:calc(100vw - 24px)!important}.teslamate-grafana-nav-large-grid{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:8px}.teslamate-grafana-nav-large-grid>a{min-width:0}@media(max-width:620px){.teslamate-grafana-nav-large{width:calc(100vw - 20px)!important}.teslamate-grafana-nav-large-grid{grid-template-columns:1fr}}";
    document.head.appendChild(style);
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
      const ordered = [...links].sort((a, b) => {
        const left = rank.get(a.textContent.trim()) ?? 9999;
        const right = rank.get(b.textContent.trim()) ?? 9999;
        return left - right || a.textContent.localeCompare(b.textContent, "zh-Hans-CN");
      });
      if (!ordered.every((link, index) => link === links[index])) ordered.forEach(link => parent.appendChild(link));
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
    return node && node.textContent.trim() === "说明文档" ? node : null;
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
    [["TeslaMate 官方文档", "https://docs.teslamate.org/"], ["Grafana 中文版仪表盘", "https://github.com/wjsall/teslamate-chinese-dashboards"], ["全中文版补丁", "https://github.com/huangkouping/teslamate-cn-patches"]].forEach(([label, href]) => {
      const item = document.createElement("a");
      item.href = href; item.target = "_blank"; item.rel = "noopener noreferrer"; item.textContent = label;
      menu.appendChild(item);
    });
    document.body.appendChild(menu);
  }
  function documentationMenu() {
    document.querySelectorAll("a,button,[role=link]").forEach(node => {
      if (node.textContent.trim() === "说明文档") node.dataset.cnDocMenu = "1";
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
  new MutationObserver(() => { placeNavigationFirst(); sortMenus(); documentationMenu(); }).observe(document.documentElement, {childList: true, subtree: true});
  placeNavigationFirst();
  sortMenus();
  documentationMenu();
})();
