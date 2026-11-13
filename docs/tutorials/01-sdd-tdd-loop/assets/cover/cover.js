// 首期封面组件。cover.html（出封面图）和 S01（开头的片头）都调它，封面只有这一份源。
//
//   Cover(root, { mode: 'main' | 'text', base: 'cover 目录的相对路径/', brand: 'logo.svg 的相对路径' })
//
// 往 root 里填封面内容，按 data-r 摆好倾角，返回一个 Promise：中文大字和三张图都加载完才 resolve，
// 放进 Stage 的 init 里，渲染器就不会拍到字体或图还没出来的帧。
// base 和 brand 由调用页给，因为 cover.html 在 assets/cover/，S01 在 assets/html/（重渲时在 render/tmp/）。
// 文案、样式说明见 cover.css。
(function () {
  function Cover(root, opt) {
    var mode = opt.mode || 'main';
    root.className = 'cv' + (mode === 'main' ? '' : ' ' + mode);
    root.innerHTML =
      '<div class="cv-abs cv-q"><span class="cv-ai">AI</span>写代码<br>总跑偏？</div>' +
      '<div class="cv-abs cv-tools">' +
        '<div class="cv-tool os" data-r="-1.5"><img src="' + opt.base + 'openspec_pixel_light.svg" alt="OpenSpec"></div>' +
        '<div class="cv-plus">+</div>' +
        '<div class="cv-tool sp" data-r="1.5"><img src="' + opt.base + 'superpowers-small.svg" alt=""><span>Superpowers</span></div>' +
      '</div>' +
      '<div class="cv-abs cv-sub">搭一个最小的开发循环</div>' +
      '<div class="cv-abs cv-badge"><img src="' + opt.brand + '" alt="老刀Cheney"></div>' +
      '<div class="card dark cv-chat">' +
        '<div class="tab ink">对话</div>' +
        '<div class="cv-who me">你</div>' +
        '<div class="cv-bubble" data-r="-1.5">加一个超温告警</div>' +
        '<div class="cv-who ai">AI</div>' +
        '<div class="cv-code">' +
          '<div class="cv-bar" style="width:58%"></div>' +
          '<div class="cv-bar" style="width:84%;margin-left:36px"></div>' +
          '<div class="cv-bar" style="width:66%;margin-left:36px"></div>' +
          '<div class="cv-bar" style="width:76%;margin-left:72px"></div>' +
          '<div class="cv-bar" style="width:40%;margin-left:36px"></div>' +
          '<div class="cv-bar" style="width:22%"></div>' +
        '</div>' +
        '<div class="guess cv-g1" data-r="-5"><b>猜</b></div>' +
        '<div class="guess cv-g2" data-r="4"><b>猜</b></div>' +
        '<div class="guess cv-g3" data-r="-3"><b>猜</b></div>' +
        '<div class="cv-fail" data-r="5">FAIL</div>' +
      '</div>';

    // 只摆封面自己的元素，不碰调用页里别的 data-r（S01 的元素由它自己的动画摆）。
    Array.prototype.forEach.call(root.querySelectorAll('[data-r]'), function (el) {
      el.style.transform = 'rotate(' + el.getAttribute('data-r') + 'deg)';
    });

    var images = Array.prototype.map.call(root.querySelectorAll('img'), function (img) {
      return img.complete ? Promise.resolve() : new Promise(function (ok) { img.onload = img.onerror = ok; });
    });
    var glyphs = document.fonts.load('900 44px "SHS Heavy"', 'AI写代码总跑偏？搭一个最小的开发循环对话你加超温告警猜');
    return Promise.all(images.concat([glyphs])).then(function () { return document.fonts.ready; });
  }
  window.Cover = Cover;
})();
