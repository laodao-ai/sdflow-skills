// 第 7 期封面组件：首页片头与 cover.html 共用（visual-v4 第七节「片头」）。文案按 storyboard.md「封面文案」（作者 2026-11-22 定）。
// 左栏：主标题、两张贴纸（左蓝 sdflow-spec、右琥珀 sdflow-ship；蓝表示规格，琥珀表示执行。作者 2026-11-22 晚由三张改为两张）、副标。
// 右栏：两张卡错位叠放（同第 6 期）：奶白卡「人来定」需求 → 规格 → 设计门；深色卡「AI 自动推进」实现 → 评审 → 归档（2026-11-22 改）。
(function(){
  window.Cover=function(root,opt){
    var mode=opt.mode||'main';
    root.className='cv'+(mode==='main'?'':' '+mode);
    root.innerHTML=
      '<div class="cv-abs cv-q">AI 全程写代码，<br>人还要管什么？</div>'+
      '<div class="cv-abs cv-tools"><div class="cv-tool l" data-r="-1.5">sdflow-spec</div><div class="cv-tool r" data-r="1.5">sdflow-ship</div></div>'+
      '<div class="cv-abs cv-sub">SDFlow 总览：人来掌舵，AI 执行</div>'+
      '<div class="cv-abs cv-badge"><img src="'+opt.brand+'" alt="老刀Cheney"></div>'+
      '<div class="cv-abs cv-side"><div class="card cv-split" data-r="2.5"><div class="tab ink" data-r="2">人来定</div><div class="cv-note-title">需求 → 规格 → 设计门</div><div class="cv-note-lines">目标、取舍、风险</div></div><div class="card dark cv-all" data-r="-2"><div class="tab" data-r="-2">AI 自动推进</div><div class="cv-note-title">实现 → 评审 → 归档</div><div class="cv-note-lines">人最后看交接报告</div></div></div>';
    root.querySelectorAll('[data-r]').forEach(function(el){el.style.transform='rotate('+el.dataset.r+'deg)';});
    return Promise.all([
      document.fonts.load('900 100px "SHS Heavy"','AI全程写代码人还要管什么SDFlow全流程总览人来掌舵执行定需求规格设计门目标取舍风险自动推进实现评审归档最后看交接报告'),
      document.fonts.load('800 40px "SHS Heavy"','AI全程写代码人还要管什么SDFlow全流程总览人来掌舵执行定需求规格设计门目标取舍风险自动推进实现评审归档最后看交接报告')
    ].concat(Array.from(root.querySelectorAll('img')).map(function(i){return i.decode();}))).then(function(){return document.fonts.ready;});
  };
})();
