// Stage clock for one storyboard frame (<ID>.html).
//
// Contract with huashu-design's scripts/render-video-seek.js:
//   - window.__ready = true once the page can be seeked.
//   - window.__seek(t) draws the frame at t seconds. It returns a Promise,
//     and page.evaluate() awaits it, so async drawing (asciinema-player
//     seek, <video> seeked) finishes before the screenshot.
// The renderer sets window.__seekRender before load; then the clock never
// self-drives. Without it (opening the file in a browser) the clock plays
// in real time for preview: plays once and holds the last frame; Space
// pauses and resumes (replays from the end), ←/→ step 1 s back or forward.
// Add ?t=3.5 to the URL to freeze at 3.5 s.
//
// ?embed=1 is for design-demos/player.js, which plays frames back to back
// in iframes. Pages run from file://, so the parent cannot touch the
// iframe's window; the two sides talk by postMessage instead:
//   frame -> parent  {type:'stage-ready', id, title, duration}  after init
//   parent -> frame  'stage-play' | 'stage-pause' | 'stage-resume'
//   frame -> parent  {type:'stage-end', id}  once t reaches duration
// In this mode the clock plays once and holds the last state.
//
// `duration` is the natural length of the animation. The timeline decides
// how long the frame stays on screen; past `duration` the last state holds.

(function () {
  function clamp(x, lo, hi) {
    return Math.min(hi, Math.max(lo, x));
  }

  // Progress of a step that starts at `start` and lasts `length` seconds, 0..1.
  function progress(t, start, length) {
    if (length <= 0) return t >= start ? 1 : 0;
    return clamp((t - start) / length, 0, 1);
  }

  // Ease-out cubic: fast start, soft landing. Used for entrances.
  function easeOut(p) {
    return 1 - Math.pow(1 - p, 3);
  }

  function Stage(options) {
    var duration = options.duration;
    var render = options.render;
    var init = options.init || function () { return Promise.resolve(); };

    function drawAt(t) {
      return Promise.resolve(render(clamp(t, 0, duration)));
    }

    // Preview only: the stage is a fixed 1920x1080 box, so scale it to fit
    // the window and center it. Render mode skips this; the renderer's
    // viewport is exactly 1920x1080.
    function fitToWindow() {
      var stage = document.getElementById('stage');
      if (!stage) return;
      document.documentElement.style.overflow = 'hidden';
      document.body.style.overflow = 'hidden';
      function fit() {
        var scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
        var left = (window.innerWidth - 1920 * scale) / 2;
        var top = (window.innerHeight - 1080 * scale) / 2;
        stage.style.transformOrigin = '0 0';
        stage.style.transform =
          'translate(' + left + 'px,' + top + 'px) scale(' + scale + ')';
      }
      fit();
      window.addEventListener('resize', fit);
    }

    function startPreview() {
      fitToWindow();
      var frozen = new URLSearchParams(location.search).get('t');
      if (frozen !== null) {
        drawAt(parseFloat(frozen));
        return;
      }
      // Same clock shape as startEmbedded: played time is `elapsed` plus the
      // current run. Plays once and holds the last frame. Space pauses and
      // resumes (from the end it replays), so the author can hold a frame
      // while talking over it; arrow keys step by STEP seconds.
      var STEP = 1;
      var elapsed = 0;
      var runStart = performance.now();  // null = paused
      var busy = false;
      function now() {
        return runStart === null ? elapsed : elapsed + (performance.now() - runStart) / 1000;
      }
      function tick() {
        if (runStart === null) return;
        var t = now();
        if (t >= duration) {
          elapsed = duration;
          runStart = null;
          drawAt(duration);
          return;
        }
        if (!busy) {
          busy = true;
          drawAt(t).then(function () { busy = false; });
        }
        requestAnimationFrame(tick);
      }
      document.addEventListener('keydown', function (e) {
        if (e.key === ' ') {
          e.preventDefault();
          if (runStart === null) {
            if (elapsed >= duration) elapsed = 0;
            runStart = performance.now();
            requestAnimationFrame(tick);
          } else {
            elapsed = now();
            runStart = null;
            // The last tick drew a few ms earlier; draw the paused time so
            // the picture matches the clock that the arrow keys step from.
            drawAt(elapsed);
          }
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
          // Step 1 s back or forward. Works while paused, so the author can
          // line the picture up with what they are saying.
          e.preventDefault();
          var step = e.key === 'ArrowLeft' ? -STEP : STEP;
          elapsed = clamp(now() + step, 0, duration);
            if (runStart !== null) {
            runStart = performance.now();
          } else {
            drawAt(elapsed);
          }
        }
      });
      requestAnimationFrame(tick);
    }

    // Embedded in the player: wait for 'stage-play', play once, report the end.
    function startEmbedded() {
      fitToWindow();
      var id = document.documentElement.getAttribute('data-frame-id') || '';
      var elapsed = 0;      // seconds played before the current run
      var runStart = null;  // performance.now() of the current run; null = paused
      var busy = false;
      var ended = false;

      function now() {
        return runStart === null ? elapsed : elapsed + (performance.now() - runStart) / 1000;
      }
      function tick() {
        if (runStart === null) return;
        var t = now();
        if (!busy) {
          busy = true;
          drawAt(t).then(function () { busy = false; });
        }
        if (t >= duration) {
          // Draw the exact last state once more, then stop the clock.
          elapsed = duration;
          runStart = null;
          drawAt(duration).then(function () {
            if (ended) return;
            ended = true;
            window.parent.postMessage({ type: 'stage-end', id: id }, '*');
          });
          return;
        }
        requestAnimationFrame(tick);
      }

      window.addEventListener('message', function (e) {
        if (e.source !== window.parent) return;
        if ((e.data === 'stage-play' || e.data === 'stage-resume') && runStart === null && !ended) {
          runStart = performance.now();
          requestAnimationFrame(tick);
        } else if (e.data === 'stage-pause' && runStart !== null) {
          elapsed = now();
          runStart = null;
        }
      });
      window.parent.postMessage({
        type: 'stage-ready', id: id, title: document.title, duration: duration
      }, '*');
    }

    var embedded = !window.__seekRender &&
      new URLSearchParams(location.search).get('embed') === '1';

    init().then(function () {
      return drawAt(0);
    }).then(function () {
      if (window.__seekRender) {
        window.__seek = drawAt;
        window.__ready = true;
      } else if (embedded) {
        startEmbedded();
      } else {
        startPreview();
      }
    });
  }

  window.Stage = Stage;
  window.StageMath = { clamp: clamp, progress: progress, easeOut: easeOut };
})();
