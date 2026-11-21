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
  installStyle();
  new MutationObserver(() => { placeNavigationFirst(); sortMenus(); }).observe(document.documentElement, {childList: true, subtree: true});
  placeNavigationFirst();
  sortMenus();
})();
