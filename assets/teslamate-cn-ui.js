(() => {
  "use strict";
  const labels = {
    "Battery Health": "电池健康度", "Charge Level": "电池容量曲线图", "Charges": "充电记录",
    "Charging Stats": "充电统计（汇总）", "Database Information": "数据库信息", "Drive Stats": "行程统计（汇总）",
    "Drives": "行程列表", "Efficiency": "能效", "Locations": "访问过的地点", "Mileage": "车辆里程（曲线图）",
    "Overview": "概览", "Projected Range": "续航曲线图", "States": "状态", "Statistics": "行程统计（年月日）",
    "Temperatures": "历史温度", "Timeline": "时间线", "Trip": "行程统计（时间段）", "Updates": "系统更新",
    "Vampire Drain": "停车电量消耗", "Visited": "足迹地图"
  };
  const menuSections = [
    ["▣  常用", ["概览", "状态", "时间线", "行程列表", "充电记录", "足迹地图"]],
    ["◆  行驶", ["行程统计（年月日）", "行程统计（时间段）", "行程统计（汇总）", "车辆里程（曲线图）", "能效", "续航曲线图", "停车电量消耗"]],
    ["⚡  充电与电池", ["电池健康度", "电池容量曲线图", "充电统计（汇总）", "历史温度"]],
    ["⌖  地点与系统", ["访问过的地点", "数据库信息", "系统更新"]]
  ];
  function installMenuStyle() {
    if (document.getElementById("teslamate-cn-menu-style")) return;
    const style = document.createElement("style");
    style.id = "teslamate-cn-menu-style";
    style.textContent = ".teslamate-cn-menu-grid{display:grid!important;grid-template-columns:repeat(2,minmax(260px,1fr));gap:10px 16px;width:min(760px,calc(100vw - 28px));padding:12px!important}.teslamate-cn-group{min-width:0;padding:4px 0}.teslamate-cn-section{margin:0 0 6px;padding:8px 10px;border-left:3px solid #5b9bd5;border-radius:3px;background:rgba(91,155,213,.12);color:#dbeafe;font-size:1.05rem;font-weight:750;letter-spacing:.035em;line-height:1.25;pointer-events:none}.teslamate-cn-menu-light .teslamate-cn-section{color:#1e4f7a;background:rgba(37,99,171,.11)}.teslamate-cn-group>a{display:block;padding:.42rem 10px!important;font-size:.94rem;line-height:1.3}@media(min-width:1100px){.teslamate-cn-menu-grid{left:-180px!important}}@media(max-width:620px){.teslamate-cn-menu-grid{grid-template-columns:1fr;width:calc(100vw - 20px)}}";
    document.head.appendChild(style);
  }
  function organizeMenu() {
    const links = [...document.querySelectorAll("a[data-cn-dashboard]")];
    if (!links.length) return;
    const menu = links[0].parentElement;
    if (!menu || menu.dataset.cnMenuOrganized || !links.every(link => link.parentElement === menu)) return;
    const byLabel = new Map(links.map(link => [link.dataset.cnDashboard, link]));
    const fragment = document.createDocumentFragment();
    menuSections.forEach(([title, names]) => {
      const group = document.createElement("div");
      group.className = "teslamate-cn-group";
      const heading = document.createElement("div");
      heading.className = "teslamate-cn-section";
      heading.textContent = title;
      group.appendChild(heading);
      names.forEach(name => { const link = byLabel.get(name); if (link) group.appendChild(link); });
      fragment.appendChild(group);
    });
    menu.replaceChildren(fragment);
    menu.classList.add("teslamate-cn-menu-grid");
    const rgb = getComputedStyle(menu).backgroundColor.match(/\d+/g);
    if (rgb && (Number(rgb[0]) * 299 + Number(rgb[1]) * 587 + Number(rgb[2]) * 114) / 1000 > 160) menu.classList.add("teslamate-cn-menu-light");
    menu.dataset.cnMenuOrganized = "1";
  }
  const outOfChina = (lat, lng) => lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271;
  const transformLat = (x, y) => -100 + 2*x + 3*y + .2*y*y + .1*x*y + .2*Math.sqrt(Math.abs(x)) + (20*Math.sin(6*x*Math.PI) + 20*Math.sin(2*x*Math.PI))*2/3 + (20*Math.sin(y*Math.PI) + 40*Math.sin(y/3*Math.PI))*2/3 + (160*Math.sin(y/12*Math.PI) + 320*Math.sin(y*Math.PI/30))*2/3;
  const transformLng = (x, y) => 300 + x + 2*y + .1*x*x + .1*x*y + .1*Math.sqrt(Math.abs(x)) + (20*Math.sin(6*x*Math.PI) + 20*Math.sin(2*x*Math.PI))*2/3 + (20*Math.sin(x*Math.PI) + 40*Math.sin(x/3*Math.PI))*2/3 + (150*Math.sin(x/12*Math.PI) + 300*Math.sin(x/30*Math.PI))*2/3;
  const gcj = (lat, lng) => {
    if (outOfChina(lat, lng)) return {lat, lng};
    const dLat = transformLat(lng - 105, lat - 35), dLng = transformLng(lng - 105, lat - 35);
    const rad = lat / 180 * Math.PI, magic = 1 - 0.00669342162296594323 * Math.sin(rad) ** 2;
    const sqrtMagic = Math.sqrt(magic);
    return {lat: lat + dLat * 180 / ((6335552.717000426 * (1 - 0.00669342162296594323)) / (magic * sqrtMagic) * Math.PI), lng: lng + dLng * 180 / (6378245 / sqrtMagic * Math.cos(rad) * Math.PI)};
  };
  function patch(root = document) {
    root.querySelectorAll('a[href^="https://www.google.com/maps?q="]').forEach(a => {
      if (a.dataset.cnMapPatched) return;
      try {
        const q = new URL(a.href).searchParams.get("q").split(","); const p = gcj(Number(q[0]), Number(q[1]));
        a.href = `https://uri.amap.com/marker?position=${p.lng.toFixed(6)},${p.lat.toFixed(6)}&name=${encodeURIComponent("车辆位置")}`;
        const label = "在高德地图中查看车辆位置";
        a.dataset.tooltip = label; a.setAttribute("aria-label", label); a.dataset.cnMapPatched = "1";
        const textNodes = [...a.childNodes].filter(n => n.nodeType === 3 && n.nodeValue.trim());
        if (textNodes.length) { textNodes[0].nodeValue = label; textNodes.slice(1).forEach(n => n.remove()); }
        else if (!a.querySelector("svg,img")) a.textContent = label;
      } catch (_) {}
    });
    root.querySelectorAll('a[href*="/grafana//"]').forEach(a => { a.href = a.href.replace("/grafana//", "/grafana/"); });
    root.querySelectorAll("a").forEach(a => {
      const text = a.textContent.trim();
      if (labels[text]) { a.textContent = labels[text]; a.dataset.cnDashboard = labels[text]; }
    });
    installMenuStyle();
    organizeMenu();
  }
  const observer = new MutationObserver(() => patch());
  observer.observe(document.documentElement, {childList: true, subtree: true});
  patch();
})();
