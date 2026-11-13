// E-a 主题的动画小工具。放在 stage.js 之后、帧脚本之前加载：
//   <script src="lib/stage.js"></script>
//   <script src="theme.js"></script>
// 加载时往 #stage 最底层插一张纸底（点阵 + 颗粒 + 斑驳）。
// 两套主题（E-a / H2）的 window.T 接口相同，帧脚本可以照搬结构。

(function () {
  var M = window.StageMath;

  var PAPER =
    '<svg class="paper" viewBox="0 0 1920 1080" aria-hidden="true">' +
    '<defs><pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse">' +
    '<circle cx="18" cy="18" r="1.6" fill="rgba(255,255,255,.10)"/></pattern></defs>' +
    '<filter id="grain" x="0" y="0" width="100%" height="100%">' +
    '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="7" stitchTiles="stitch"/>' +
    '<feColorMatrix type="matrix" values="0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0 0 0 0 0.30"/></filter>' +
    '<filter id="mottle" x="0" y="0" width="100%" height="100%">' +
    '<feTurbulence type="fractalNoise" baseFrequency="0.006" numOctaves="4" seed="3"/>' +
    '<feColorMatrix type="matrix" values="0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0 0 0 0 0.24"/></filter>' +
    '<filter id="fiber" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="11"/><feColorMatrix type="matrix" values="0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0 0 0 0 0.10"/></filter>' +
    '<rect width="1920" height="1080" filter="url(#mottle)"/>' +
    '<rect width="1920" height="1080" filter="url(#fiber)"/>' +
    '<rect width="1920" height="1080" fill="url(#grid)"/>' +
    '</svg>';

  var stage = document.getElementById('stage');
  if (stage) stage.insertAdjacentHTML('afterbegin', PAPER);

  // 自动倾角（visual-v4 §4.3，第 2 期起）。没写 data-r 的组件，按「帧 ID + 页内序号」算出倾角，
  // 同一页重渲结果不变；相邻两个一左一右；没定的（.guess .mock .tag）3–5°，定下来的（.card .tab .chip）1–2°。
  // 终端、命令卡、录像窗口里的元素不倾斜。算好写回 data-r，并先摆好静止角度，进场动画照常从 data-r 读。
  var LOOSE = '.guess,.mock,.tag', FIRM = '.card,.tab,.chip';
  function hash(s) {
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  var frameId = document.documentElement.getAttribute('data-frame-id') || location.pathname;
  var k = 0;
  Array.prototype.slice.call(document.querySelectorAll(LOOSE + ',' + FIRM)).forEach(function (el) {
    if (el.hasAttribute('data-r') || el.closest('.window,.cmd')) return;
    var loose = el.matches(LOOSE);
    var lo = loose ? 3 : 1, hi = loose ? 5 : 2;
    var mag = lo + (hash(frameId + '#' + k) % 1000) / 1000 * (hi - lo);
    var r = (k % 2 ? 1 : -1) * mag;
    el.setAttribute('data-r', r.toFixed(1));
    el.style.transform = 'rotate(' + r.toFixed(1) + 'deg)';
    k++;
  });

  var CREAM = [242, 239, 230];

  function $(id) { return document.getElementById(id); }
  function all(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }

  function mix(a, b, p) {
    return 'rgb(' + [0, 1, 2].map(function (i) { return Math.round(a[i] + (b[i] - a[i]) * p); }).join(',') + ')';
  }
  function tiltOf(el) { return parseFloat(el.getAttribute('data-r') || '0'); }

  // 贴纸落下：淡入、下落 dy，倾角从两倍收到自己的 data-r。
  function enter(el, p, dy, dx) {
    var e = M.easeOut(p);
    var r = tiltOf(el);
    el.style.opacity = e;
    el.style.transform = 'translate(' + ((1 - e) * (dx || 0)) + 'px,' + ((1 - e) * (dy === undefined ? 14 : dy)) + 'px) rotate(' + (r + (1 - e) * r * 2) + 'deg)';
  }
  // 一组元素依次进场。
  function items(sel, start, gap, t, dy) {
    var els = all(sel);
    for (var i = 0; i < els.length; i++) enter(els[i], M.progress(t, start + i * gap, 0.4), dy);
  }
  // 当前 = 被选中：黄色描边留空隙 + 外发光；墨色硬投影保留。g 取 0..1。
  function current(el, g, size) {
    var s = size || parseFloat(el.getAttribute('data-shadow') || '10');
    el.style.outline = '7px solid rgba(245,207,74,' + g + ')';
    el.style.outlineOffset = '10px';
    el.style.boxShadow = '0 0 0 10px rgba(138,147,157,' + g + '), ' + s + 'px ' + s + 'px 0 #161616, 0 0 60px rgba(245,207,74,' + (0.5 * g) + ')';
  }
  // 从起点方向擦出：x 从左到右，y 从上到下（y-up 从下到上）。
  function wipe(el, p, axis) {
    var e = M.easeOut(p);
    var k = (1 - e) * 100;
    el.style.clipPath = axis === 'y' ? 'inset(0 0 ' + k + '% 0)' : axis === 'y-up' ? 'inset(' + k + '% 0 0 0)' : 'inset(0 ' + k + '% 0 0)';
  }
  // 底色从奶白渐变到目标色（红 = 现在失败，绿 = 现在通过）。
  function fill(el, to, p, from) { el.style.background = mix(from || CREAM, to, M.easeOut(p)); }
  // 划掉：一条墨线从左往右划过。el 是线本身（.abs 定位好的 div / svg）。
  function strike(el, p) { wipe(el, p, 'x'); }
  // 等本地黑体加载完再画第 0 帧，避免回退字体闪一下。text 填本帧用到的中文大字。
  function fonts(text) {
    return document.fonts.load('900 44px "SHS Heavy"', text || '中').then(function () { return document.fonts.ready; });
  }
  // 静止状态下按 data-r 摆好倾角（不做进场动画的元素用）。
  function tilt() {
    all('[data-r]').forEach(function (el) { el.style.transform = 'rotate(' + tiltOf(el) + 'deg)'; });
  }

  // 元素在舞台坐标里的矩形 {x, y, w, h}。预览时舞台整体缩放，这里除掉缩放。
  function rect(el) {
    var sr = stage.getBoundingClientRect(), k = sr.width / 1920, r = el.getBoundingClientRect();
    return { x: (r.left - sr.left) / k, y: (r.top - sr.top) / k, w: r.width / k, h: r.height / k };
  }
  function corners(r) { return [[r.x, r.y], [r.x + r.w, r.y], [r.x, r.y + r.h], [r.x + r.w, r.y + r.h]]; }
  // 放大卡引线（visual-v4 4.7）：每张放大卡一根，黄色 2px，不加箭头，
  // 从黄框离卡最近的角连到卡离黄框最近的角。box、card 是 rect() 量出的矩形，要在卡没有位移、没有缩放时量。
  // 线画在 #leads 层：页面自己有 <svg id="leads"> 就用它（页面定层次），没有就新建一层，z-index 20。
  // 层次要求：在实录与压暗层之上，在放大卡之下，所以放大卡的 z-index 要高于这一层。
  function lead(box, card) {
    var NS = 'http://www.w3.org/2000/svg', layer = $('leads');
    if (!layer) {
      layer = document.createElementNS(NS, 'svg');
      layer.setAttribute('id', 'leads');
      layer.setAttribute('viewBox', '0 0 1920 1080');
      layer.setAttribute('aria-hidden', 'true');
      layer.style.cssText = 'position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:20;pointer-events:none';
      stage.appendChild(layer);
    }
    var best = null;
    corners(box).forEach(function (p) {
      corners(card).forEach(function (q) {
        var d = Math.hypot(p[0] - q[0], p[1] - q[1]);
        if (!best || d < best.d) best = { d: d, p: p, q: q };
      });
    });
    var line = document.createElementNS(NS, 'line');
    line.setAttribute('x1', best.p[0]); line.setAttribute('y1', best.p[1]);
    line.setAttribute('x2', best.q[0]); line.setAttribute('y2', best.q[1]);
    line.setAttribute('stroke', '#f5cf4a'); line.setAttribute('stroke-width', 2);
    // pathLength=1：dashoffset 1 → 0 就是从黄框一端擦出到卡
    line.setAttribute('pathLength', 1);
    line.setAttribute('stroke-dasharray', 1); line.setAttribute('stroke-dashoffset', 1);
    layer.appendChild(line);
    return line;
  }
  // 引线画到第几：p 0 = 没有，1 = 连到卡。随卡展开传卡的展开进度，卡收起时传收起进度，线缩回黄框。
  function leadDraw(line, p) { line.setAttribute('stroke-dashoffset', 1 - M.clamp(p, 0, 1)); }

  window.T = {
    $: $, all: all, mix: mix, enter: enter, items: items, current: current,
    wipe: wipe, fill: fill, strike: strike, fonts: fonts, tilt: tilt,
    rect: rect, lead: lead, leadDraw: leadDraw,
    p: M.progress, ease: M.easeOut
  };
})();
