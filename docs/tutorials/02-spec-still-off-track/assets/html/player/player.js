// Plays the episode's frames back to back, with a hideable table of contents.
// Entry page: play.html next to this file (assets/html/player/). Open it from file://.
// Template copy (video-lib/templates/episode); every episode keeps this file
// byte-identical to the template. The frame list lives in ../frames.js, which
// play.html loads first: window.PLAYER_SET is the set name, window.PLAYER_FRAMES
// is [[ID, title], …] following storyboard.md's 分镜表.
//
// Each frame is loaded as ../<ID>.html?embed=1; stage.js then waits for
// 'stage-play' and reports 'stage-end' (protocol in assets/html/lib/stage.js).
// Two iframes take turns: one plays, the other preloads the next frame, so
// the cut is instant even for frames that load a cast or a video.
//
// Keys: T show/hide contents · Space pause/resume · ←/→ previous/next frame.

(function () {
  // Seconds a frame holds its last state before the next one starts.
  // Matches the 1 s hold of the single-frame preview loop.
  var HOLD = 1;
  // A frame that has not reported ready by then is skipped in the contents view.
  var READY_TIMEOUT = 15000;

  // [[ID, title], …] from ../frames.js.
  var FRAMES = window.PLAYER_FRAMES || [];

  var CSS = [
    'html,body{margin:0;height:100%;background:#1b1b1b;color:#e8e6e1;',
    '  font-family:"PingFang SC",system-ui,sans-serif;overflow:hidden}',
    '#app{display:flex;height:100%}',
    '#toc{flex:0 0 260px;display:flex;flex-direction:column;background:#232323;',
    '  border-right:1px solid #333;transition:margin-left .2s}',
    '#app.toc-hidden #toc{margin-left:-261px}',
    '#toc header{padding:14px 16px 10px;border-bottom:1px solid #333}',
    '#toc h1{margin:0 0 10px;font-size:16px;font-weight:600}',
    '#toc .ctl{display:flex;gap:6px}',
    '#toc button{flex:1;padding:6px 0;background:#2f2f2f;color:#e8e6e1;border:1px solid #444;',
    '  border-radius:6px;font:inherit;font-size:13px;cursor:pointer}',
    '#toc button:hover{background:#3a3a3a}',
    '#toc .hint{margin-top:8px;font-size:12px;color:#8a8780}',
    '#toc ol{list-style:none;margin:0;padding:6px 0;overflow-y:auto;flex:1}',
    '#toc li{display:flex;gap:10px;padding:5px 16px;font-size:14px;cursor:pointer;color:#c9c6bf}',
    '#toc li:hover{background:#2c2c2c}',
    '#toc li .id{flex:0 0 32px;color:#8a8780;font-variant-numeric:tabular-nums}',
    '#toc li.on{background:#3a3424;color:#f5cf4a}',
    '#toc li.on .id{color:#f5cf4a}',
    '#toc li.bad{color:#d06a5a}',
    '#screen{position:relative;flex:1;background:#000}',
    // Frames take no clicks, so keyboard focus never moves into an iframe.
    '#screen iframe{position:absolute;inset:0;width:100%;height:100%;border:0;',
    '  opacity:0;pointer-events:none;z-index:0}',
    // The preloading buffer stays full size: display:none would make the
    // frame fit itself to a 0x0 window.
    '#screen iframe.live{opacity:1;z-index:1}',
    '#toggle{position:absolute;left:12px;top:12px;z-index:3;padding:6px 12px;background:rgba(20,20,20,.7);',
    '  color:#e8e6e1;border:1px solid #555;border-radius:6px;font:inherit;font-size:13px;cursor:pointer;',
    '  transition:opacity .3s}',
    '#status{position:absolute;right:12px;top:12px;z-index:3;padding:6px 12px;background:rgba(20,20,20,.7);',
    '  border-radius:6px;font-size:13px;transition:opacity .3s}',
    // Both overlays fade out while the mouse is idle, so a screen capture stays clean.
    '#screen.idle #toggle,#screen.idle #status{opacity:0}'
  ].join('\n');

  var setName = window.PLAYER_SET || '';
  // Frames sit one folder up from the player page.
  var BASE = '../';
  var current = -1;      // index of the frame on screen
  var wanted = -1;       // index we are waiting to show
  var paused = false;
  var endedAt = null;    // index whose frame reported stage-end, during the hold
  var holdTimer = null;

  document.head.insertAdjacentHTML('beforeend', '<style>' + CSS + '</style>');
  document.body.innerHTML =
    '<div id="app">' +
    '  <nav id="toc"><header><h1>' + setName + ' · ' + FRAMES.length + ' 帧连播</h1>' +
    '    <div class="ctl"><button id="prev">上一帧</button><button id="pause">暂停</button>' +
    '    <button id="next">下一帧</button></div>' +
    '    <div class="hint">T 目录 · 空格 暂停 · ←/→ 切帧</div></header><ol id="list"></ol></nav>' +
    '  <main id="screen"><iframe id="bufA"></iframe><iframe id="bufB"></iframe>' +
    '    <button id="toggle">目录</button><div id="status"></div></main>' +
    '</div>';

  function $(id) { return document.getElementById(id); }

  var list = $('list');
  FRAMES.forEach(function (f, i) {
    var li = document.createElement('li');
    li.innerHTML = '<span class="id">' + f[0] + '</span><span>' + f[1] + '</span>';
    li.addEventListener('click', function () { go(i); });
    list.appendChild(li);
  });

  // Each buffer remembers which frame it holds and whether that frame is ready.
  var buffers = [$('bufA'), $('bufB')].map(function (el) {
    return { el: el, index: -1, ready: false, timer: null };
  });

  function liveBuffer() { return buffers.filter(function (b) { return b.el.classList.contains('live'); })[0]; }
  function spareBuffer() { return buffers.filter(function (b) { return !b.el.classList.contains('live'); })[0]; }

  function load(buf, i) {
    clearTimeout(buf.timer);
    buf.index = i;
    buf.ready = false;
    buf.el.src = BASE + FRAMES[i][0] + '.html?embed=1';
    buf.timer = setTimeout(function () {
      if (buf.index === i && !buf.ready) {
        list.children[i].classList.add('bad');
        console.error('player: ' + FRAMES[i][0] + ' did not report ready');
        if (wanted === i) setStatus(FRAMES[i][0] + ' 加载失败');
      }
    }, READY_TIMEOUT);
  }

  function send(buf, msg) {
    if (buf && buf.el.contentWindow) buf.el.contentWindow.postMessage(msg, '*');
  }

  function setStatus(text) { $('status').textContent = text; }

  function updateStatus() {
    if (current < 0) return;
    var f = FRAMES[current];
    var tail = current === FRAMES.length - 1 && endedAt === current ? ' · 播完' : '';
    setStatus(f[0] + ' ' + f[1] + ' · ' + (current + 1) + '/' + FRAMES.length + (paused ? ' · 已暂停' : '') + tail);
  }

  // Show frame i: use the spare buffer if it already holds i, otherwise load it there.
  function go(i) {
    if (i < 0 || i >= FRAMES.length) return;
    clearTimeout(holdTimer);
    endedAt = null;
    wanted = i;
    var spare = spareBuffer();
    if (spare.index !== i) load(spare, i);
    if (spare.ready) activate(spare);
    else setStatus(FRAMES[i][0] + ' 加载中…');
  }

  function activate(buf) {
    var old = liveBuffer();
    buf.el.classList.add('live');
    if (old && old !== buf) {
      old.el.classList.remove('live');
      old.index = -1;
      old.ready = false;
    }
    current = buf.index;
    wanted = -1;
    if (!paused) send(buf, 'stage-play');
    markToc();
    updateStatus();
    // Reuse the retired buffer to preload the next frame.
    var spare = spareBuffer();
    if (current + 1 < FRAMES.length) load(spare, current + 1);
    else spare.el.src = 'about:blank';
  }

  function markToc() {
    for (var k = 0; k < list.children.length; k++) list.children[k].classList.toggle('on', k === current);
    var on = list.children[current];
    if (on) on.scrollIntoView({ block: 'nearest' });
  }

  function scheduleNext() {
    clearTimeout(holdTimer);
    if (current + 1 >= FRAMES.length) { updateStatus(); return; }
    holdTimer = setTimeout(function () { go(current + 1); }, HOLD * 1000);
  }

  window.addEventListener('message', function (e) {
    var d = e.data;
    if (!d || typeof d !== 'object') return;
    // contentWindow survives navigation, so also check the frame ID: a late
    // message from the page a buffer held before must not count.
    var buf = buffers.filter(function (b) {
      return b.el.contentWindow === e.source && b.index >= 0 && FRAMES[b.index][0] === d.id;
    })[0];
    if (!buf) return;
    if (d.type === 'stage-ready') {
      buf.ready = true;
      clearTimeout(buf.timer);
      if (wanted === buf.index && !buf.el.classList.contains('live')) activate(buf);
    } else if (d.type === 'stage-end' && buf.el.classList.contains('live')) {
      endedAt = buf.index;
      if (!paused) scheduleNext();
      updateStatus();
    }
  });

  function togglePause() {
    paused = !paused;
    $('pause').textContent = paused ? '继续' : '暂停';
    var live = liveBuffer();
    if (paused) {
      clearTimeout(holdTimer);
      send(live, 'stage-pause');
    } else if (endedAt === current) {
      scheduleNext();
    } else {
      // A frame activated while paused never got 'stage-play'; resume starts it.
      send(live, 'stage-resume');
    }
    updateStatus();
  }

  function toggleToc() {
    var hidden = $('app').classList.toggle('toc-hidden');
    try { localStorage.setItem('player-toc-hidden', hidden ? '1' : '0'); } catch (err) { /* storage blocked */ }
  }

  $('prev').addEventListener('click', function () { go(current - 1); });
  $('next').addEventListener('click', function () { go(current + 1); });
  $('pause').addEventListener('click', togglePause);
  $('toggle').addEventListener('click', toggleToc);

  document.addEventListener('keydown', function (e) {
    if (e.key === 't' || e.key === 'T') toggleToc();
    else if (e.key === ' ') { e.preventDefault(); togglePause(); }
    else if (e.key === 'ArrowLeft') go(current - 1);
    else if (e.key === 'ArrowRight') go(current + 1);
  });

  var idleTimer = null;
  $('screen').addEventListener('mousemove', function () {
    $('screen').classList.remove('idle');
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function () { $('screen').classList.add('idle'); }, 2000);
  });

  try {
    if (localStorage.getItem('player-toc-hidden') === '1') $('app').classList.add('toc-hidden');
  } catch (err) { /* storage blocked: start with contents shown */ }

  var start = parseInt(new URLSearchParams(location.search).get('from') || '1', 10) - 1;
  go(isNaN(start) ? 0 : Math.max(0, Math.min(FRAMES.length - 1, start)));
})();
