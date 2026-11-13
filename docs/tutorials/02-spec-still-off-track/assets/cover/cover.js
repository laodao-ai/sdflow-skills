// 第 2 期封面组件。cover.html（出封面图）和 S01（开头的片头）都调它，封面只有这一份源。
//
//   Cover(root, { mode: 'main' | 'text' | 'p34' | 'l43', base: 'cover 目录的相对路径/', brand: 'logo.svg 的相对路径' })
//
// 往 root 里填封面内容，按 data-r 摆好倾角，返回一个 Promise：中文大字和 logo 都加载完才 resolve，
// 放进 Stage 的 init 里，渲染器就不会拍到字体或图还没出来的帧。
// base 和 brand 由调用页给，因为 cover.html 在 assets/cover/，S01 在 assets/html/（重渲时在 render/tmp/）。
// base 用来找 OpenSpec 的像素 logo（openspec_pixel_light.svg，许可见 LOGOS.LICENSE.txt）。
// 文案、样式说明见 cover.css。
(function () {
  // 十三种设计图的缩略图（照 S25a 的画法简化：只留几个框几条线，不写名字）。
  // 顺序同 S25a：结构 5（上下文 / 容器 / 组件 / 模块关系 / 部署）、行为 5（状态机 / 数据流 / 决策 / 时序 / 竞态时序）、
  // 验证与决策 3（测试覆盖 / 对比表 / 任务依赖）。
  var DIAGRAMS = [
    '<circle class="b" cx="32" cy="36" r="13"/><path class="s" d="M12 86 Q32 50 52 86 Z"/><rect class="os" x="92" y="30" width="80" height="58" rx="6"/><rect class="b" x="204" y="38" width="46" height="42" rx="5" stroke-dasharray="7 6"/><line class="a" x1="58" y1="60" x2="88" y2="60"/><line class="a" x1="176" y1="59" x2="200" y2="59"/>',
    '<rect class="d" x="6" y="6" width="248" height="108" rx="8"/><rect class="b" x="22" y="36" width="58" height="44" rx="5"/><rect class="b" x="106" y="36" width="58" height="44" rx="5"/><path class="b" d="M190 34 v44 a20 7 0 0 0 40 0 v-44"/><ellipse class="b" cx="210" cy="34" rx="20" ry="7"/><line class="a" x1="82" y1="58" x2="102" y2="58"/><line class="a" x1="166" y1="58" x2="186" y2="58"/>',
    '<rect class="b" x="10" y="6" width="240" height="108" rx="8"/><rect class="os" x="30" y="22" width="70" height="32" rx="4"/><rect class="b" x="160" y="22" width="70" height="32" rx="4"/><rect class="b" x="30" y="70" width="70" height="32" rx="4"/><rect class="b" x="160" y="70" width="70" height="32" rx="4"/><line class="a" x1="102" y1="38" x2="156" y2="38"/><line class="a" x1="102" y1="86" x2="156" y2="86"/>',
    '<rect class="os" x="10" y="44" width="56" height="32" rx="4"/><rect class="b" x="102" y="8" width="56" height="32" rx="4"/><rect class="b" x="102" y="80" width="56" height="32" rx="4"/><rect class="b" x="194" y="44" width="56" height="32" rx="4"/><line class="a" x1="66" y1="52" x2="98" y2="32"/><line class="a" x1="66" y1="68" x2="98" y2="88"/><line class="a" x1="158" y1="32" x2="190" y2="52"/><line class="a" x1="158" y1="88" x2="190" y2="68"/>',
    '<rect class="b" x="14" y="24" width="80" height="78"/><rect class="os" x="30" y="46" width="48" height="32" rx="3"/><rect class="b" x="166" y="24" width="80" height="78"/><rect class="b" x="182" y="46" width="48" height="32" rx="3"/><line class="s" x1="96" y1="63" x2="164" y2="63"/>',
    '<circle class="k" cx="12" cy="66" r="8"/><circle class="b" cx="62" cy="66" r="24"/><circle class="os" cx="140" cy="66" r="24"/><circle class="b" cx="218" cy="66" r="24"/><line class="a" x1="88" y1="66" x2="112" y2="66"/><line class="a" x1="166" y1="66" x2="190" y2="66"/><path class="a" d="M206 44 Q140 -4 74 44"/>',
    '<rect class="b" x="6" y="22" width="56" height="40" rx="4"/><circle class="os" cx="130" cy="42" r="26"/><rect class="b" x="198" y="22" width="56" height="40" rx="4"/><line class="a" x1="64" y1="42" x2="98" y2="42"/><line class="a" x1="158" y1="42" x2="194" y2="42"/><path class="s" d="M96 96 h68 M96 116 h68"/>',
    '<path class="os" d="M130 8 L170 46 L130 84 L90 46 Z"/><rect class="b" x="6" y="80" width="62" height="34" rx="4"/><rect class="b" x="192" y="80" width="62" height="34" rx="4"/><path class="a" d="M90 46 H37 V76"/><path class="a" d="M170 46 H223 V76"/>',
    '<rect class="b" x="12" y="2" width="56" height="24" rx="3"/><rect class="os" x="102" y="2" width="56" height="24" rx="3"/><rect class="b" x="192" y="2" width="56" height="24" rx="3"/><line class="d" x1="40" y1="28" x2="40" y2="118"/><line class="d" x1="130" y1="28" x2="130" y2="118"/><line class="d" x1="220" y1="28" x2="220" y2="118"/><line class="a" x1="40" y1="48" x2="124" y2="48"/><line class="a" x1="130" y1="72" x2="214" y2="72"/><line class="a" x1="220" y1="98" x2="46" y2="98"/>',
    '<rect class="b" x="6" y="2" width="56" height="24" rx="3"/><rect class="os" x="102" y="2" width="56" height="24" rx="3"/><rect class="b" x="198" y="2" width="56" height="24" rx="3"/><line class="d" x1="34" y1="28" x2="34" y2="118"/><line class="d" x1="226" y1="28" x2="226" y2="118"/><rect class="b" x="122" y="40" width="16" height="74"/><line class="a" x1="34" y1="54" x2="116" y2="54"/><line class="a" x1="226" y1="62" x2="144" y2="62"/>',
    '<rect class="b" x="6" y="6" width="70" height="26" rx="3"/><rect class="b" x="6" y="47" width="70" height="26" rx="3"/><rect class="b" x="6" y="88" width="70" height="26" rx="3"/><rect class="os" x="184" y="10" width="70" height="26" rx="13"/><rect class="b" x="184" y="84" width="70" height="26" rx="13"/><line class="a" x1="78" y1="19" x2="180" y2="23"/><line class="a" x1="78" y1="60" x2="180" y2="27"/><line class="a" x1="78" y1="101" x2="180" y2="97"/>',
    '<rect class="b" x="6" y="6" width="248" height="108" rx="4"/><rect class="os" x="6" y="6" width="248" height="30" rx="4"/><path class="s" d="M6 72 H254 M84 6 V114 M170 6 V114"/>',
    '<circle class="b" cx="40" cy="20" r="16"/><circle class="b" cx="40" cy="60" r="16"/><circle class="b" cx="40" cy="100" r="16"/><circle class="os" cx="214" cy="60" r="20"/><line class="a" x1="58" y1="24" x2="190" y2="54"/><line class="a" x1="58" y1="60" x2="188" y2="60"/><line class="a" x1="58" y1="96" x2="190" y2="66"/>'
  ];

  function Cover(root, opt) {
    var mode = opt.mode || 'main';
    root.className = 'cv' + (mode === 'main' ? '' : ' ' + mode);

    var tiles = DIAGRAMS.map(function (d) {
      return '<div class="cv-dg"><svg viewBox="0 0 260 120">' + d + '</svg></div>';
    }).join('');

    root.innerHTML =
      // 缩略图共用的箭头头部。id 带 cv- 前缀，不和调用页里的 id 冲突。
      '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>' +
        '<marker id="cv-ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">' +
        '<path d="M0 0 L10 5 L0 10 Z" fill="#161616"/></marker></defs></svg>' +
      '<div class="cv-abs cv-q">Spec 怎么写，<br><span class="cv-ai">AI</span>才不会跑偏？</div>' +
      // 两个工具，照首期写法；取自平台副标题「OpenSpec 加 grill-me，先问到底再写」。grill-me 没有 logo，只放字。
      '<div class="cv-abs cv-tools">' +
        '<div class="cv-tool os" data-r="-1.5"><img src="' + opt.base + 'openspec_pixel_light.svg" alt="OpenSpec"></div>' +
        '<div class="cv-plus">+</div>' +
        '<div class="cv-tool gm" data-r="1.5"><span>grill-me</span></div>' +
      '</div>' +
      '<div class="cv-abs cv-sub">怎么问，怎么写，写成什么样</div>' +
      '<div class="cv-abs cv-badge"><img src="' + opt.brand + '" alt="老刀Cheney"></div>' +
      // 右栏：后面一张设计图网格，前面一张清单塔，倾角一左一右。
      '<div class="cv-abs cv-side">' +
        '<div class="card cv-grid" data-r="2.5">' +
          '<div class="tab ink" data-r="2">设计图</div>' +
          '<div class="cv-tiles">' + tiles + '</div>' +
        '</div>' +
        '<div class="card dark cv-tower" data-r="-2">' +
          '<div class="tab" data-r="-2">领域清单</div>' +
          '<div class="cv-stack">' +
          '<div class="cv-blk top" style="left:0;top:0">Go</div>' +
          '<div class="cv-blk top" style="left:182px;top:0">ESP32</div>' +
          '<div class="cv-blk top" style="left:364px;top:0">React</div>' +
          '<div class="cv-blk mid" style="left:0;top:80px">后端</div>' +
          '<div class="cv-blk mid" style="left:182px;top:80px">嵌入式</div>' +
          '<div class="cv-blk mid" style="left:364px;top:80px">前端</div>' +
          '<div class="cv-blk base" style="left:0;top:160px">通用</div>' +
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
    var glyphs = document.fonts.load('900 44px "SHS Heavy"', 'Spec怎么写，AI才不会跑偏？问成什么样设计图领域清单通用后端嵌入式前端');
    return Promise.all(images.concat([glyphs])).then(function () { return document.fonts.ready; });
  }
  window.Cover = Cover;
})();
