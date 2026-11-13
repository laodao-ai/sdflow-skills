// 第 4 期封面组件。cover.html（出封面图）和 S01（开头的片头）都调它，封面只有这一份源。
//
//   Cover(root, { mode: 'main' | 'text' | 'p34' | 'l43', base: 'cover 目录的相对路径/', brand: 'logo.svg 的相对路径' })
//
// 往 root 里填封面内容，按 data-r 摆好倾角，返回一个 Promise：中文大字和 logo 都加载完才 resolve，
// 放进 Stage 的 init 里，渲染器就不会拍到字体或图还没出来的帧。
// base 留着和前几期同一个调用方式；本期三个工具都没有 logo，不用它。
// 文案、样式说明见 cover.css。
(function () {
  // 拆成 ticket 的一排小格：1–5 加「收尾」，同 S13 的「3–6 个 + 1 个收尾」。
  var CELLS = ['1', '2', '3', '4', '5', '收尾'];

  function Cover(root, opt) {
    var mode = opt.mode || 'main';
    root.className = 'cv' + (mode === 'main' ? '' : ' ' + mode);

    var cells = CELLS.map(function (c) {
      return '<div class="cv-cell' + (c === '收尾' ? ' last' : '') + '">' + c + '</div>';
    }).join('');

    // 验收项一行：勾选框 + 灰条。前两行勾上。
    function row(w, done) {
      return '<div class="cv-row"><div class="cv-box' + (done ? ' on' : '') + '"></div>' +
             '<div class="cv-line" style="width:' + w + 'px"></div></div>';
    }

    root.innerHTML =
      // 问题句同平台标题（2026-10-31 作者定缩短），断在「规格写好了，」后面。
      '<div class="cv-abs cv-q">Spec 写好了，<br>为什么不一口气生成代码？</div>' +
      // 三个工具，取自平台副标题。都没有 logo，只放字。
      '<div class="cv-abs cv-tools">' +
        '<div class="cv-tool l" data-r="-1.5"><span>Superpowers</span></div>' +
        '<div class="cv-plus">+</div>' +
        '<div class="cv-tool m" data-r="1"><span>Matt Pocock</span></div>' +
        '<div class="cv-plus">+</div>' +
        '<div class="cv-tool r" data-r="-1"><span>SDFlow</span></div>' +
      '</div>' +
      '<div class="cv-abs cv-sub">怎么拆开发任务，怎么生成代码</div>' +
      '<div class="cv-abs cv-badge"><img src="' + opt.brand + '" alt="老刀Cheney"></div>' +
      // 右栏：后面一张奶白卡（拆成 ticket），前面一张深色卡（ticket 2，S12 缩略）。倾角一右一左。
      '<div class="cv-abs cv-side">' +
        '<div class="card cv-split" data-r="2.5">' +
          '<div class="tab ink" data-r="2">拆成 ticket</div>' +
          '<div class="cv-cells">' + cells + '</div>' +
        '</div>' +
        '<div class="card dark cv-t2" data-r="-2">' +
          '<div class="tab" data-r="-2">ticket 2</div>' +
          '<div class="cv-rows">' + row(400, true) + row(320, true) + row(360, false) + '</div>' +
          '<div class="cv-result" data-r="-1">' +
            '<span class="cv-res fail">FAIL</span><span class="cv-arrow">→</span><span class="cv-res pass">PASS</span>' +
          '</div>' +
        '</div>' +
      '</div>';

    // 只摆封面自己的元素，不碰调用页里别的 data-r（S01 的元素由它自己的动画摆）。
    Array.prototype.forEach.call(root.querySelectorAll('[data-r]'), function (el) {
      el.style.transform = 'rotate(' + el.getAttribute('data-r') + 'deg)';
    });

    var images = Array.prototype.map.call(root.querySelectorAll('img'), function (img) {
      return img.complete ? Promise.resolve() : new Promise(function (ok) { img.onload = img.onerror = ok; });
    });
    var glyphs = document.fonts.load('900 44px "SHS Heavy"', '写好了，为什么不一口气生成代码？怎么拆开发任务ticket收尾');
    return Promise.all(images.concat([glyphs])).then(function () { return document.fonts.ready; });
  }
  window.Cover = Cover;
})();
