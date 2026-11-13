// 第 3 期封面组件。cover.html（出封面图）和 S01（开头的片头）都调它，封面只有这一份源。
//
//   Cover(root, { mode: 'main' | 'text' | 'p34' | 'l43', base: 'cover 目录的相对路径/', brand: 'logo.svg 的相对路径' })
//
// 往 root 里填封面内容，按 data-r 摆好倾角，返回一个 Promise：中文大字和 logo 都加载完才 resolve，
// 放进 Stage 的 init 里，渲染器就不会拍到字体或图还没出来的帧。
// base 留着和第 2 期同一个调用方式；本期两个工具都没有 logo，不用它。
// 文案、样式说明见 cover.css。
(function () {
  // 七个评审角度，同 S08。src：g = gstack 原有，s = SDFlow 加的；同 S08 用奶白底 / 墨底区分，不借颜色。
  var LENSES = [
    ['前提和范围', 'g'], ['工程', 'g'], ['开发体验', 'g'], ['另一个模型', 'g'],
    ['读代码', 's'], ['领域', 's'], ['找茬', 's']
  ];

  function Cover(root, opt) {
    var mode = opt.mode || 'main';
    root.className = 'cv' + (mode === 'main' ? '' : ' ' + mode);

    var chips = LENSES.map(function (l) {
      return '<div class="cv-lens ' + l[1] + '">' + l[0] + '</div>';
    }).join('');

    root.innerHTML =
      // 问题句同平台标题。
      '<div class="cv-abs cv-q"><span class="cv-ai">AI</span>写的 Spec，<br>能直接生成代码吗？</div>' +
      // 两个工具，取自平台副标题「gstack 加 SDFlow，……」。两个都没有 logo，只放字。
      '<div class="cv-abs cv-tools">' +
        '<div class="cv-tool l" data-r="-1.5"><span>gstack</span></div>' +
        '<div class="cv-plus">+</div>' +
        '<div class="cv-tool r" data-r="1.5"><span>SDFlow</span></div>' +
      '</div>' +
      '<div class="cv-abs cv-sub">怎么审，怎么拍板，值不值得</div>' +
      '<div class="cv-abs cv-badge"><img src="' + opt.brand + '" alt="老刀Cheney"></div>' +
      // 右栏：后面一张评审角度卡（S08 缩略），前面一张深色评审报告卡，盖「批准 · 锁住」章。倾角一左一右。
      '<div class="cv-abs cv-side">' +
        '<div class="card cv-lenses" data-r="2.5">' +
          '<div class="tab ink" data-r="2">评审角度</div>' +
          '<div class="cv-chips">' + chips + '</div>' +
        '</div>' +
        '<div class="card dark cv-report" data-r="-2">' +
          '<div class="tab" data-r="-2">评审报告</div>' +
          '<div class="cv-lines">' +
            '<div class="cv-line" style="width:420px"></div>' +
            '<div class="cv-line" style="width:330px"></div>' +
            '<div class="cv-line" style="width:380px"></div>' +
          '</div>' +
          '<div class="cv-stamp" data-r="-8">批准 · 锁住</div>' +
        '</div>' +
      '</div>';

    // 只摆封面自己的元素，不碰调用页里别的 data-r（S01 的元素由它自己的动画摆）。
    Array.prototype.forEach.call(root.querySelectorAll('[data-r]'), function (el) {
      el.style.transform = 'rotate(' + el.getAttribute('data-r') + 'deg)';
    });

    var images = Array.prototype.map.call(root.querySelectorAll('img'), function (img) {
      return img.complete ? Promise.resolve() : new Promise(function (ok) { img.onload = img.onerror = ok; });
    });
    var glyphs = document.fonts.load('900 44px "SHS Heavy"', 'AI写的Spec，能直接生成代码吗？怎么审拍板成本控评审角度报告批准锁住前提和范围工程开发体验另一个模型读代码领域找茬');
    return Promise.all(images.concat([glyphs])).then(function () { return document.fonts.ready; });
  }
  window.Cover = Cover;
})();
