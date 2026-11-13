// 第 5 期封面组件。cover.html（出封面图）和 S01（开头的片头）都调它，封面只有这一份源。
//
//   Cover(root, { mode: 'main' | 'text' | 'p34' | 'l43', base: 'cover 目录的相对路径/', brand: 'logo.svg 的相对路径' })
//
// 往 root 里填封面内容，按 data-r 摆好倾角，返回一个 Promise：中文大字和 logo 都加载完才 resolve，
// 放进 Stage 的 init 里，渲染器就不会拍到字体或图还没出来的帧。
// base 留着和前几期同一个调用方式；本期的工具贴纸没有 logo，不用它。
// 文案、样式说明见 cover.css。
(function () {
  // 7 个 ticket，和 S01 的七个 ticket 卡数量一致。每格下面一个墨色勾（审过）和一个绿点（测试通过）。
  var CELLS = ['1', '2', '3', '4', '5', '6', '7'];

  function Cover(root, opt) {
    var mode = opt.mode || 'main';
    root.className = 'cv' + (mode === 'main' ? '' : ' ' + mode);

    var cells = CELLS.map(function (c) {
      return '<div class="cv-col">' +
               '<div class="cv-cell">' + c + '</div>' +
               '<div class="cv-ok"></div>' +
               '<div class="cv-dot"></div>' +
             '</div>';
    }).join('');

    // 工作区 + 锁 + 三条操作线。「打开」直线穿过锁，「新建」「删除」从锁的上、下绕过去。
    // 勾、点、锁都用图形画，不依赖字体里有没有对应字符。
    var lockSvg =
      '<svg class="cv-lock-svg" width="520" height="150" viewBox="0 0 520 150" fill="none" stroke="#f2efe6" stroke-linecap="round" stroke-linejoin="round">' +
        // 工作区方块：外框 + 十字分格。
        '<rect x="4" y="30" width="84" height="84" rx="6" stroke-width="6"/>' +
        '<path d="M46 30 V114 M4 72 H88" stroke="#a09d97" stroke-width="3"/>' +
        // 锁：锁梁 + 锁身，锁身填深色，让「打开」那条线压在上面穿过去。
        '<path d="M236 58 V46 a14 14 0 0 1 28 0 V58" stroke-width="6"/>' +
        '<rect x="226" y="58" width="48" height="46" rx="6" fill="#262626" stroke-width="6"/>' +
        // 三条操作线，从右往左指向工作区。
        '<path d="M410 72 H100" stroke-width="8"/>' +
        '<path d="M410 20 H190 L100 44" stroke-width="5" stroke-dasharray="12 9"/>' +
        '<path d="M410 126 H190 L100 100" stroke-width="5" stroke-dasharray="12 9"/>' +
        '<text x="424" y="32" fill="#f2efe6" stroke="none" class="cv-op">新建</text>' +
        '<text x="424" y="84" fill="#f2efe6" stroke="none" class="cv-op">打开</text>' +
        '<text x="424" y="138" fill="#f2efe6" stroke="none" class="cv-op">删除</text>' +
      '</svg>';

    root.innerHTML =
      // 问题句同平台标题，断在「测试全过了，」后面。
      '<div class="cv-abs cv-q">测试全过了，<br>为什么还要代码评审？</div>' +
      // 两张贴纸：SDFlow 放左位（左蓝），Code Review 放右位（右琥珀），按位置不按工具（同第 3 期）。
      // Code Review 是这期的主题不是工具，所以中间不放「+」（2026-11-09 作者定加这张）。
      '<div class="cv-abs cv-tools">' +
        '<div class="cv-tool l" data-r="-1.5"><span>SDFlow</span></div>' +
        '<div class="cv-tool r" data-r="1.5"><span>Code Review</span></div>' +
      '</div>' +
      '<div class="cv-abs cv-sub">审什么，怎么审，审出问题以后怎么改</div>' +
      '<div class="cv-abs cv-badge"><img src="' + opt.brand + '" alt="老刀Cheney"></div>' +
      // 右栏：后面一张奶白卡（7 个 ticket），前面一张深色卡（合起来再审）。倾角一右一左。
      '<div class="cv-abs cv-side">' +
        '<div class="card cv-split" data-r="2.5">' +
          '<div class="tab ink" data-r="2">7 个 ticket</div>' +
          '<div class="cv-cells">' + cells + '</div>' +
        '</div>' +
        '<div class="card dark cv-all" data-r="-2">' +
          '<div class="tab" data-r="-2">合起来再审</div>' +
          '<div class="cv-lock">' + lockSvg + '</div>' +
          '<div class="cv-sevs">' +
            '<span class="cv-sev" data-r="-3">严重</span><span class="cv-sev" data-r="2">严重</span>' +
            '<span class="cv-sev" data-r="-2">严重</span><span class="cv-sev" data-r="3">严重</span>' +
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
    var glyphs = document.fonts.load('900 44px "SHS Heavy"', '测试全过了，为什么还要代码评审？审什么怎么审出问题以后改个合起来再打开新建删除严重SDFlowCode Review');
    return Promise.all(images.concat([glyphs])).then(function () { return document.fonts.ready; });
  }
  window.Cover = Cover;
})();
