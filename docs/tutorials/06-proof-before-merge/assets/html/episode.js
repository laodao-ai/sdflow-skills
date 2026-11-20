/* 各页提供自己的句子节点，避免固定间隔逐卡播放。 */
(function(){
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
    document.querySelectorAll('.hl[data-current]').forEach(function(el){var a=Number(el.dataset.current),end=Number(el.dataset.until||9999);el.style.opacity=T.ease(T.p(t,a,.4))*(1-T.ease(T.p(t,end,.4)));});
    document.querySelectorAll('[data-current]:not(.hl)').forEach(function(el){var a=Number(el.dataset.current),end=Number(el.dataset.until||9999);T.current(el,T.ease(T.p(t,a,.4))*(1-T.ease(T.p(t,end,.4))),8);});
    if(intro){var ce=window.COVER_END||2;intro.style.opacity=1-T.p(t,ce,.35);intro.style.visibility=t>=ce+.35?'hidden':'visible';}
    if(window.frameRender)window.frameRender(t);
  }});
})();
