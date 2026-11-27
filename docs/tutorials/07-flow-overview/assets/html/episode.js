/* 第 7 期共用脚本。
   先按页面里的声明建好共用组件，再启动舞台时钟：
   - 六步条 <div class="sixbar" data-seq="3:0">：第 4 版 S11–S17、S19、S19a、S24、S25a、S28 等画面上部，位置与样式固定。
   - 四格演进条 <div class="tline" data-seq="1:0,2:17.4">：第 4 版 S06–S09、S38 画面上部。
     data-seq 写「第几步:从第几秒起是当前」，0 表示不再高亮；data-done="all" 表示六步都已讲过。
   - 箭头 <i class="arr cue" data-at="3" data-d="M..."></i>：换成墨色 svg 线，data-dash 画虚线，data-nohead 不画箭头。
   - 角色图标 <div class="who human"></div> / <div class="who agent"></div>：visual-v4 第五节的人与 Agent。
   - 原文里的黄框 <span class="mk" data-current="22" data-until="25">：深色原文窗里不留纸底空隙，框线贴着文字。
   各页提供自己的句子节点，避免固定间隔逐卡播放。 */
(function(){
  var NS='http://www.w3.org/2000/svg';
  var SIX=['需求明确','规格编写','规格评审','代码实现','代码评审','收尾归档'];
  // 第 4 版：与分镜 S06 的四格演进条文字一致。
  var FOUR=['用现成工具','提示词衔接','用 skill 编排','吸收方法，自己维护'];
  // 六步条每格 272 宽、间距约 33；时间线每格 380 宽、间距 40，右侧留 160 给 S27 的「还在改」。
  var GEO={six:{w:272,step:305.6},four:{w:380,step:420}};

  function svgEl(tag,attrs){var e=document.createElementNS(NS,tag);for(var k in attrs)e.setAttribute(k,attrs[k]);return e;}
  function parseSeq(s){return (s||'').split(',').filter(Boolean).map(function(p){var a=p.split(':');return [Number(a[0]),Number(a[1])];});}

  function buildNav(el,names,kind){
    var g=GEO[kind];
    names.forEach(function(n,i){
      var d=document.createElement('div');
      d.className='nav-step '+kind;d.setAttribute('data-r','0');d.setAttribute('data-shadow','7');
      d.style.left=(i*g.step)+'px';
      d.innerHTML='<span class="num">'+(i+1)+'</span><span class="big">'+n+'</span>';
      el.appendChild(d);
    });
    var s=svgEl('svg',{'class':'nav-arrows',viewBox:'0 0 1800 92',width:1800,height:92});
    for(var i=0;i<names.length-1;i++){
      var x1=i*g.step+g.w+8,x2=(i+1)*g.step-8;
      s.appendChild(svgEl('path',{d:'M'+x1+' 46 L'+x2+' 46 M'+(x2-8)+' 38 L'+x2+' 46 L'+(x2-8)+' 54',fill:'none',stroke:'#161616','stroke-width':5,'stroke-linecap':'round','stroke-linejoin':'round'}));
    }
    el.appendChild(s);
    el._seq=parseSeq(el.getAttribute('data-seq'));
  }
  document.querySelectorAll('.sixbar').forEach(function(el){buildNav(el,SIX,'six');});
  document.querySelectorAll('.tline').forEach(function(el){buildNav(el,FOUR,'four');});

  // 箭头：一条路径，末端一个折线箭头头。
  var ak=0;
  document.querySelectorAll('i.arr').forEach(function(el){
    var s=svgEl('svg',{viewBox:'0 0 1920 1080'});
    s.setAttribute('class','wire '+el.className.replace(/\barr\b/,'').trim());
    Array.prototype.forEach.call(el.attributes,function(a){if(/^data-/.test(a.name)||a.name==='id'||a.name==='style')s.setAttribute(a.name,a.value);});
    var id='ah'+(ak++);
    var defs=svgEl('defs',{});
    var m=svgEl('marker',{id:id,viewBox:'0 0 12 12',refX:10,refY:6,markerWidth:4.2,markerHeight:4.2,orient:'auto',markerUnits:'strokeWidth'});
    m.appendChild(svgEl('path',{d:'M2 1 L10 6 L2 11',fill:'none',stroke:'#161616','stroke-width':2.2,'stroke-linecap':'round','stroke-linejoin':'round'}));
    defs.appendChild(m);s.appendChild(defs);
    var p=svgEl('path',{d:el.getAttribute('data-d'),fill:'none',stroke:el.getAttribute('data-color')||'#161616','stroke-width':el.getAttribute('data-w')||5,'stroke-linecap':'round','stroke-linejoin':'round'});
    if(el.hasAttribute('data-dash'))p.setAttribute('stroke-dasharray','14 12');
    if(!el.hasAttribute('data-nohead'))p.setAttribute('marker-end','url(#'+id+')');
    s.appendChild(p);
    el.parentNode.replaceChild(s,el);
  });

  // 角色图标：只用几何图形（visual-v4 第五节）。
  document.querySelectorAll('.who').forEach(function(el){
    var svg=el.classList.contains('agent')
      ?'<svg viewBox="0 0 100 100"><polygon points="50,6 90,28 90,72 50,94 10,72 10,28" fill="none" stroke="#f2efe6" stroke-width="8"/><polygon points="50,34 66,43 66,61 50,70 34,61 34,43" fill="#f29b50"/></svg>'
      :'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="38" fill="none" stroke="#f2efe6" stroke-width="9"/><circle cx="50" cy="50" r="15" fill="#f2efe6"/></svg>';
    el.insertAdjacentHTML('afterbegin',svg);
  });

  // 导航条状态：讲过 = 奶白底；当前 = 讲过 + 黄框；没讲到 = 透明底淡墨（visual-v4 4.9）。
  function navRender(el,t){
    var sq=el._seq,all=el.getAttribute('data-done')==='all',reached=0;
    sq.forEach(function(p){if(t>=p[1])reached=Math.max(reached,p[0]);});
    Array.prototype.forEach.call(el.querySelectorAll('.nav-step'),function(s,i){
      var n=i+1,done=all||n<=reached,g=0;
      sq.forEach(function(p,j){if(p[0]!==n)return;var end=sq[j+1]?sq[j+1][1]:1e9;g=Math.max(g,T.ease(T.p(t,p[1]+.1,.4))*(1-T.ease(T.p(t,end,.3))));});
      s.classList.toggle('notyet',!done);
      if(done)T.current(s,g,7);else{s.style.outline='none';s.style.boxShadow='none';}
    });
  }

  var cfg=window.FRAME_TIMING,cues=Array.from(document.querySelectorAll('.cue')),geo=[];
  var intro=document.getElementById('intro-cover');
  Stage({duration:cfg.duration,init:function(){
    var waits=[T.fonts(document.getElementById('stage').textContent)];
    Array.from(document.images).forEach(function(im){waits.push(im.decode());});
    if(intro)waits.push(Cover(intro,{mode:'main',brand:'../../../shared/logo.svg'}));
    return Promise.all(waits).then(function(){
      (window.FRAME_LINKS||[]).forEach(function(l){var box=T.$(l.box),card=T.$(l.card);card.style.transform='none';var a=T.rect(box),b=T.rect(card);geo.push({line:T.lead(a,b),box:box,card:card,at:Math.max(1.65,l.at),dx:a.x+a.w/2-b.x-b.w/2,dy:a.y+a.h/2-b.y-b.h/2});});
    });
  },render:function(t){
    T.tilt();
    var heading=document.querySelector('.frame-title');
    cues.forEach(function(el){var start=Number(el.dataset.at);if(heading&&el!==heading)start=Math.max(1.1,start);T.enter(el,T.p(t,start,.55),14);});
    if(heading){var mv=T.ease(T.p(t,.35,.6));var scale=1.25-.25*mv;heading.style.left=(60+(960-heading.offsetWidth*1.25/2-60)*(1-mv))+'px';heading.style.top=(48+(450-heading.offsetHeight*1.25/2-48)*(1-mv))+'px';heading.style.transformOrigin='0 0';heading.style.transform+=' scale('+scale+')';}
    geo.forEach(function(g){var p=T.ease(T.p(t,g.at,.4)),k=T.ease(T.p(t,g.at+.3,.6));g.box.style.opacity=p;g.card.style.opacity=k;g.card.style.transform='translate('+((1-k)*g.dx)+'px,'+((1-k)*g.dy)+'px) scale('+(.45+.55*k)+')';T.leadDraw(g.line,k);});
    document.querySelectorAll('.sixbar,.tline').forEach(function(el){navRender(el,t);});
    document.querySelectorAll('.hl[data-current]').forEach(function(el){var a=Number(el.dataset.current),end=Number(el.dataset.until||9999);el.style.opacity=T.ease(T.p(t,a,.4))*(1-T.ease(T.p(t,end,.4)));});
    // 原文窗里的黄框：5px 黄线贴字，外发光，不加纸底空隙。
    document.querySelectorAll('.mk[data-current]').forEach(function(el){var a=Number(el.dataset.current),end=Number(el.dataset.until||9999),g=T.ease(T.p(t,a,.4))*(1-T.ease(T.p(t,end,.4)));el.style.outline='5px solid rgba(245,207,74,'+g+')';el.style.outlineOffset='3px';el.style.boxShadow='0 0 18px rgba(245,207,74,'+(.55*g)+')';});
    document.querySelectorAll('[data-current]:not(.hl):not(.mk)').forEach(function(el){var a=Number(el.dataset.current),end=Number(el.dataset.until||9999);T.current(el,T.ease(T.p(t,a,.4))*(1-T.ease(T.p(t,end,.4))),Number(el.getAttribute('data-shadow')||8));});
    if(intro){var ce=window.COVER_END||2;intro.style.opacity=1-T.p(t,ce,.35);intro.style.visibility=t>=ce+.35?'hidden':'visible';}
    if(window.frameRender)window.frameRender(t);
  }});
})();
