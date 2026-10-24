'use strict';
// 评审页 DOM 回归测试（harden-review-page-followups · tasks 1.2 / 2.1–2.4）。
// 用 render-review-page.py 产出真实页面，在 Chromium 里以 file:// 打开。
// 测试全程不访问网络：mermaid CDN 地址由路由换成 node_modules 里的同版本文件，其余 http(s) 一律拦截并记账。
// 运行：node --test sdflow-init/tests/dom/review_page_dom.test.js （node 24 下必须传文件路径，不能传目录）

const { describe, test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const MERMAID_URL = 'https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js';
const MERMAID_FILE = path.join(__dirname, 'node_modules', 'mermaid', 'dist', 'mermaid.min.js');
const RENDER_SCRIPT = path.resolve(__dirname, '..', '..', 'assets', 'hack', 'render-review-page.py');
const CHECK_NOTES_PATH = path.resolve(__dirname, '..', '..', 'assets', 'hack', 'check-notes-path.py');
const PYTHON = process.env.SDFLOW_DOM_PYTHON || 'python3';

// ── 夹具：文档原文 ──────────────────────────────────────────────────────────
const FILLER = Array.from({ length: 80 }, (_, i) => `填充段落第 ${i + 1} 行，用来把后面的内容推到视口之外。`).join('\n\n');

const DOCS = [
  ['设计', 'design.md', [
    '# 设计总览',
    '',
    '## 重名节',
    '',
    '第一处正文 alpha beta gamma delta epsilon。',
    '',
    '[到另一份文档](other.md) [外链](https://example.com/page "外链标题") [脚本链](javascript:window.__pwn=1) [缺失文档](missing.md)',
    '',
    '![内嵌图](data:image/png;base64,iVBORw0KGgo=) ![远程图](https://evil.example/a.png)',
    '',
    '<div id="injected" onclick="window.__pwn=2">原始块级 HTML</div>',
    '',
    '行内 <b id="inl">粗体标签</b> 与 <!-- 被删注释 --> 之后的文字。',
    '',
    '| 列一 | 列二 |',
    '| --- | --- |',
    '| 甲 | 乙 |',
    '',
    FILLER,
    '',
    '## 重名节',
    '',
    '第二处正文 zeta eta theta iota kappa。',
    '',
    '### 子节',
    '',
    '子节正文。',
    '',
    '#### 四级标题',
    '',
    '四级正文。',
    '',
  ].join('\n')],
  ['另一份', 'other.md', '# 另一份文档\n\n另一份的正文。\n'],
  ['图', 'diagram.md', '# 图\n\n```mermaid\ngraph LR\n  A[开始] --> B[结束]\n```\n'],
  ['恶意', 'evil.md', [
    '# 恶意载荷',
    '',
    '<script>window.__pwn=3</script>',
    '',
    '<img src=x onerror="window.__pwn=4">',
    '',
    '[点我](javascript:window.__pwn=5)',
    '',
    '<!-- 未闭合注释开始',
    '</script><script>window.__pwn=6</script>',
    '',
  ].join('\n')],
  ['尾部', 'tail.md', '# 尾部 <i id="h">标题标签</i>\n\n尾部文档的正文 omega。\n'],
  ['锚点', 'anchors.md', [
    '# 锚点测试',
    '',
    '[同文档中文](#数据模型与生命周期) [同文档编码](#%E6%95%B0%E6%8D%AE%E6%A8%A1%E5%9E%8B%E4%B8%8E%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F)',
    '[重名第二个](#risks-1) [标点标题](#a--b) [缺失标题](#不存在的标题)',
    '[跨文档命中](design.md#重名节-1) [跨文档未命中](other.md#没有这个) [跨文档无片段](other.md)',
    '',
    FILLER,
    '',
    '## 数据模型与生命周期',
    '',
    '数据模型正文。',
    '',
    '## Risks',
    '',
    '第一个风险节。',
    '',
    '## Risks',
    '',
    '第二个风险节。',
    '',
    '## A & B',
    '',
    '标点标题正文。',
    '',
  ].join('\n')],
];

let browser;
let repo;
let pageFile;
let pageUrl;
let pagePathname;

// 用生成脚本把 root 下 change x 的文档渲染成 review/page.html（已有 review-notes.md 时一并读回嵌入）。
function renderPage(root, docs = DOCS) {
  const changeDir = path.join(root, 'openspec', 'changes', 'x');
  const args = [RENDER_SCRIPT, '--out', path.join(changeDir, 'review', 'page.html'), '--title', '回归测试页', '--no-open'];
  for (const [label, file] of docs) args.push('--doc', `${label}=${path.join(changeDir, file)}`);
  // 固定 epoch 与时区：修改日志的时间取自这两项，重复生成的页面才逐字节相同。
  const env = { ...process.env, SOURCE_DATE_EPOCH: '1700000000', TZ: 'UTC' };
  return execFileSync(PYTHON, args, { cwd: root, encoding: 'utf-8', env });
}

// 建一个临时 git 仓：写好 DOCS 并渲染一次；返回仓根与页面的 file URL / pathname。
function makeRepo(docs = DOCS) {
  const root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'sdflow-dom-')));
  execFileSync('git', ['init', '-q'], { cwd: root });
  const changeDir = path.join(root, 'openspec', 'changes', 'x');
  fs.mkdirSync(changeDir, { recursive: true });
  for (const [, file, text] of docs) fs.writeFileSync(path.join(changeDir, file), text, 'utf-8');
  renderPage(root, docs);
  const file = path.join(changeDir, 'review', 'page.html');
  const url = pathToFileURL(file).href;
  return { root, changeDir, notesFile: path.join(changeDir, 'review', 'review-notes.md'), url, pathname: new URL(url).pathname };
}

function makeFixtureRepo() {
  const root = makeRepo().root;
  fs.writeFileSync(path.join(root, 'other-page.html'), '<!doctype html><meta charset="utf-8"><title>other</title><p>other</p>', 'utf-8');
  return root;
}

// 用 node_modules 里的同版本文件应答 mermaid CDN 请求。
function fulfillMermaid(route) {
  return route.fulfill({
    status: 200,
    contentType: 'application/javascript',
    headers: { 'access-control-allow-origin': '*' },
    body: fs.readFileSync(MERMAID_FILE),
  });
}

// 打开一页。mermaid: 'local'（路由到本地同版本文件）| 'abort'（模拟离线）| 'hang'（一直不返回）。
async function openPage(opts = {}) {
  const mermaid = opts.mermaid || 'local';
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const hung = [];
  const seen = { mermaid: [], blocked: [] };
  await ctx.route((url) => /^https?:$/.test(url.protocol), async (route) => {
    const url = route.request().url();
    if (url !== MERMAID_URL) { seen.blocked.push(url); await route.abort(); return; }
    seen.mermaid.push(url);
    if (mermaid === 'abort') { await route.abort(); return; }
    if (mermaid === 'hang') { hung.push(route); return; }
    await fulfillMermaid(route);
  });
  const page = await ctx.newPage();
  const errors = [];
  const dialogs = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('dialog', async (d) => { dialogs.push(d.message()); await d.dismiss(); });
  for (const script of opts.initScripts || []) await page.addInitScript(script);
  if (opts.clock) await page.clock.install();
  await page.goto(opts.url || pageUrl, { waitUntil: opts.waitUntil || 'load' });
  return {
    ctx, page, errors, dialogs, seen,
    // 'hang' 模式下放行被挂住的 mermaid 请求，模拟「慢但最终加载成功」。
    async releaseMermaid() {
      for (const r of hung.splice(0)) await fulfillMermaid(r);
    },
    async close() {
      for (const r of hung) { try { await r.abort(); } catch (e) { /* 页面已关 */ } }
      await ctx.close();
    },
  };
}

async function withPage(opts, fn) {
  const h = await openPage(opts);
  try { await fn(h); } finally { await h.close(); }
}

// 注入的 <img onerror> 没有执行：window.__pwn 未被置位，也没有弹窗。
async function expectNoScriptRan(page, dialogs) {
  assert.equal(await page.evaluate(() => window.__pwn), undefined);
  assert.deepEqual(dialogs, []);
}

function rm(r) { fs.rmSync(r.root, { recursive: true, force: true }); }

// 建一个临时仓，跑完（含失败）一定删掉。make 返回 makeRepo 形态的对象。
async function withRepo(make, fn) {
  const r = make();
  try { await fn(r); } finally { rm(r); }
}

// 在某份文档的单个文本节点内划选 needle（跨节点的选区不会被高亮）。
async function selectText(page, docLabel, needle) {
  await page.evaluate(({ docLabel, needle }) => {
    const body = document.querySelector(`section.doc[data-label="${docLabel}"] .doc-body`);
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const i = node.data.indexOf(needle);
      if (i < 0) continue;
      const range = document.createRange();
      range.setStart(node, i);
      range.setEnd(node, i + needle.length);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      return;
    }
    throw new Error('找不到要划选的文字：' + needle);
  }, { docLabel, needle });
  await page.locator('#sdflow-annotate').waitFor({ state: 'visible' });
}

// 正文里全部暂存高亮：{意见 id: [各分段文字（按文档顺序）]}，用来断言每个 mark 归属到哪条意见。
function stagedMarks(page) {
  return page.locator('mark.sdflow-hl').evaluateAll((els) => {
    const out = {};
    for (const m of els) (out[m.dataset.note] = out[m.dataset.note] || []).push(m.textContent);
    return out;
  });
}

// 从 fromNeedle 所在文本节点的起点划选到 toNeedle 的末尾，可跨粗体、列表项等元素。
async function selectAcross(page, docLabel, fromNeedle, toNeedle) {
  await page.evaluate(({ docLabel, fromNeedle, toNeedle }) => {
    const body = document.querySelector(`section.doc[data-label="${docLabel}"] .doc-body`);
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
    let node, startNode = null, startAt = 0;
    const range = document.createRange();
    while ((node = walker.nextNode())) {
      if (!startNode) {
        const i = node.data.indexOf(fromNeedle);
        if (i < 0) continue;
        startNode = node; startAt = i;
        range.setStart(node, i);
      }
      const j = node.data.indexOf(toNeedle, node === startNode ? startAt : 0);
      if (j >= 0) {
        range.setEnd(node, j + toNeedle.length);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        return;
      }
    }
    throw new Error('找不到要划选的范围：' + fromNeedle + ' … ' + toNeedle);
  }, { docLabel, fromNeedle, toNeedle });
  await page.locator('#sdflow-annotate').waitFor({ state: 'visible' });
}

async function saveNote(page, comment) {
  await page.locator('#sdflow-annotate').click();
  await page.locator('#sdflow-note-text').fill(comment);
  await page.locator('#sdflow-note-dialog .sdflow-btn.primary').click();
  await page.locator('#sdflow-note-dialog').waitFor({ state: 'hidden' });
}

async function addNoteAcross(page, docLabel, fromNeedle, toNeedle, comment) {
  await selectAcross(page, docLabel, fromNeedle, toNeedle);
  await saveNote(page, comment);
}

// 已落盘高亮：{意见 id: [各分段文字]}
function savedMarksOf(page) {
  return page.locator('mark.sdflow-saved-hl').evaluateAll((els) => {
    const out = {};
    for (const m of els) (out[m.dataset.saved] = out[m.dataset.saved] || []).push(m.textContent);
    return out;
  });
}

async function addNote(page, docLabel, needle, comment) {
  await selectText(page, docLabel, needle);
  await page.locator('#sdflow-annotate').click();
  await page.locator('#sdflow-note-text').fill(comment);
  await page.locator('#sdflow-note-dialog .sdflow-btn.primary').click();
  await page.locator('#sdflow-note-dialog').waitFor({ state: 'hidden' });
}

// 把复制文本按 RVP-06 追加到 review-notes.md：先用 check-notes-path.py 校验第一行的路径（以退出码为准），通过才追加。
function appendPasted(r, text) {
  const first = text.split('\n')[0];
  const p = /`([^`]+)`/.exec(first)[1];
  const abs = execFileSync(PYTHON, [CHECK_NOTES_PATH, p], { cwd: r.root, encoding: 'utf-8' }).trim();
  assert.equal(abs, r.notesFile);
  fs.appendFileSync(abs, text, 'utf-8');
}

async function copyOnce(page) {
  await page.locator('#sdflow-copy-new').click();
  await page.waitForFunction(() => document.getElementById('sdflow-copy-status').textContent.startsWith('已复制'));
  return (await page.evaluate(() => window.__clip)).pop();
}

// 剪贴板桩：writeText 记账并成功，或按 mode 拒绝。桩替换的是浏览器 API，页面逻辑照常走。
function clipboardStub(mode) {
  return `(() => {
    window.__clip = [];
    const impl = ${mode === 'reject'}
      ? () => Promise.reject(new Error('denied'))
      : (t) => { window.__clip.push(t); return Promise.resolve(); };
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: impl } });
    ${mode === 'reject' ? "document.execCommand = () => false;" : ''}
  })();`;
}

// 预置浏览器暂存的意见（页面的 localStorage 键为 'sdflow-review:' + pathname）。调用方自己 reload。
async function seedNotes(page, notes, { key = 'sdflow-review:' + pagePathname, next = notes.length + 1 } = {}) {
  await page.evaluate(({ key, data }) => localStorage.setItem(key, data), { key, data: JSON.stringify({ next, notes }) });
}

before(async () => {
  repo = makeFixtureRepo();
  pageFile = path.join(repo, 'openspec', 'changes', 'x', 'review', 'page.html');
  pageUrl = pathToFileURL(pageFile).href;
  pagePathname = new URL(pageUrl).pathname;
  browser = await chromium.launch();
});

after(async () => {
  if (browser) await browser.close();
  if (repo) fs.rmSync(repo, { recursive: true, force: true });
});

// ── 1.2 冒烟 ────────────────────────────────────────────────────────────────
describe('冒烟', () => {
  test('页面渲染出全部文档，无脚本报错，不访问网络', async () => {
    await withPage({}, async ({ page, errors, seen }) => {
      assert.equal(await page.title(), '回归测试页');
      const labels = await page.locator('section.doc').evaluateAll((els) => els.map((e) => e.getAttribute('data-label')));
      assert.deepEqual(labels, DOCS.map((d) => d[0]));
      assert.deepEqual(errors, []);
      assert.deepEqual(seen.blocked, []);
    });
  });
});

// ── 2.1 渲染与安全 ──────────────────────────────────────────────────────────
describe('渲染与安全', () => {
  test('链接与图片按白名单改写', async () => {
    await withPage({}, async ({ page }) => {
      const body = page.locator('section.doc[data-label="设计"] .doc-body');
      // 相对 .md 链接指向页内文档，不新开窗口
      const internal = body.locator('a', { hasText: '到另一份文档' });
      assert.equal(await internal.getAttribute('href'), '#doc-1');
      assert.equal(await internal.getAttribute('target'), null);
      // 外链新开窗口并带 noopener
      const external = body.locator('a', { hasText: '外链' });
      assert.equal(await external.getAttribute('href'), 'https://example.com/page');
      assert.equal(await external.getAttribute('target'), '_blank');
      assert.equal(await external.getAttribute('rel'), 'noopener noreferrer');
      assert.equal(await external.getAttribute('title'), '外链标题');
      // javascript: 与找不到的文档只剩文字
      assert.equal(await body.locator('a', { hasText: '脚本链' }).count(), 0);
      assert.equal(await body.locator('a', { hasText: '缺失文档' }).count(), 0);
      assert.match(await body.textContent(), /脚本链/);
      assert.match(await body.textContent(), /缺失文档/);
      // data: 图片放行，远程图片换成占位文字
      const imgs = body.locator('img');
      assert.equal(await imgs.count(), 1);
      assert.match(await imgs.first().getAttribute('src'), /^data:image\/png;base64,/);
      assert.match(await body.textContent(), /\[图片：远程图\]/);
      // 表格被包进可横向滚动的容器
      assert.equal(await body.locator('.table-wrap > table').count(), 1);
    });
  });

  test('原始 HTML 一律转义成文字，注释被删', async () => {
    await withPage({}, async ({ page }) => {
      const body = page.locator('section.doc[data-label="设计"] .doc-body');
      assert.equal(await body.locator('#injected').count(), 0);
      assert.equal(await body.locator('#inl').count(), 0);
      assert.equal(await body.locator('[onclick]').count(), 0);
      const raw = await body.locator('pre.raw-html').textContent();
      assert.match(raw, /<div id="injected" onclick="window\.__pwn=2">原始块级 HTML<\/div>/);
      const text = await body.textContent();
      assert.match(text, /<b id="inl">粗体标签<\/b>/);
      assert.doesNotMatch(text, /被删注释/);
    });
  });

  test('恶意 payload 端到端不执行，后面的文档照常渲染', async () => {
    await withPage({}, async ({ page, errors, dialogs }) => {
      assert.equal(await page.evaluate(() => window.__pwn), undefined);
      assert.deepEqual(dialogs, []);
      assert.deepEqual(errors, []);
      const evil = page.locator('section.doc[data-label="恶意"] .doc-body');
      assert.equal(await evil.locator('script, img, a').count(), 0);
      // 未闭合的注释连同后面的 </script> 都当文字显示
      assert.match(await evil.locator('pre.raw-html').last().textContent(), /<\/script><script>window\.__pwn=6<\/script>/);
      assert.equal(await page.locator('section.doc').count(), DOCS.length);
      assert.match(await page.locator('section.doc[data-label="尾部"] .doc-body').textContent(), /尾部文档的正文 omega/);
    });
  });

  test('意见正文含 <img onerror> 时只作文字显示，不执行', async () => {
    await withPage({}, async ({ page, dialogs }) => {
      const payload = '<img src=x onerror="window.__pwn=7"><script>window.__pwn=8</script>';
      await addNote(page, '设计', 'alpha beta', payload);
      assert.equal(await page.locator('#sdflow-notes .note-comment').textContent(), payload);
      assert.equal(await page.locator('#sdflow-notes img, #sdflow-notes script').count(), 0);
      assert.equal(await page.evaluate(() => window.__pwn), undefined);
      assert.deepEqual(dialogs, []);
    });
  });

  test('意见栏的引用与标题含尖括号时按文字显示', async () => {
    await withPage({}, async ({ page }) => {
      await addNote(page, '设计', '<b id="inl">粗体标签</b>', '引用里有标签');
      await addNote(page, '尾部', 'omega', '标题里有标签');
      const quote = page.locator('#sdflow-notes .note-quote').first();
      assert.equal(await quote.textContent(), '<b id="inl">粗体标签</b>');
      assert.equal(await quote.locator('*').count(), 0);
      const head = page.locator('#sdflow-notes .note-head').nth(1);
      assert.equal(await head.textContent(), '#2 尾部 › 尾部 <i id="h">标题标签</i>');
      assert.equal(await head.locator('i').count(), 0);
    });
  });

  test('CSP 的 script-src 只含两个哈希加 mermaid 固定地址', async () => {
    await withPage({}, async ({ page }) => {
      const csp = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');
      const directive = csp.split(';').map((s) => s.trim()).find((s) => s.startsWith('script-src '));
      const tokens = directive.split(/\s+/).slice(1).map((t) => t.replace(/^'|'$/g, ''));
      assert.equal(tokens.length, 3);
      assert.equal(tokens.filter((t) => /^sha256-[A-Za-z0-9+/]{43}=$/.test(t)).length, 2);
      assert.ok(tokens.includes(MERMAID_URL));
      // 两个哈希分别对得上 marked 与应用脚本本身（页面能跑起来即证明；这里再直接核一次）
      const actual = await page.evaluate(async () => {
        async function h(id) {
          const buf = new TextEncoder().encode(document.getElementById(id).textContent);
          const d = await crypto.subtle.digest('SHA-256', buf);
          return 'sha256-' + btoa(String.fromCharCode(...new Uint8Array(d)));
        }
        return [await h('sdflow-marked'), await h('sdflow-app')];
      });
      assert.deepEqual(tokens.filter((t) => t.startsWith('sha256-')).sort(), actual.sort());
    });
  });
});

// ── 2.2 标题 id、目录跳转、mermaid 提示 ─────────────────────────────────────
describe('标题与 mermaid', () => {
  test('标题 id 按「文档序号-序号」生成，重名标题不冲突', async () => {
    await withPage({}, async ({ page }) => {
      const ids = await page.locator('section.doc[data-label="设计"] .doc-body :is(h1,h2,h3,h4)')
        .evaluateAll((els) => els.map((e) => [e.tagName, e.textContent, e.id]));
      assert.deepEqual(ids, [
        ['H1', '设计总览', 'd0-1'],
        ['H2', '重名节', 'd0-2'],
        ['H2', '重名节', 'd0-3'],
        ['H3', '子节', 'd0-4'],
        ['H4', '四级标题', 'd0-5'],
      ]);
      // 目录只收 1–3 级，四级标题不进目录
      const toc = await page.locator('#toc a').evaluateAll((els) => els.map((e) => [e.textContent, e.getAttribute('href')]));
      assert.ok(toc.some((t) => t[0] === '子节' && t[1] === '#d0-4'));
      assert.ok(!toc.some((t) => t[0] === '四级标题'));
    });
  });

  test('点目录条目滚到对应标题，重名标题各去各处', async () => {
    await withPage({}, async ({ page }) => {
      await page.locator('#toc a[href="#d0-3"]').click();
      await page.waitForFunction(() => {
        const r = document.getElementById('d0-3').getBoundingClientRect();
        return r.top >= 0 && r.top < window.innerHeight / 2;
      });
      assert.equal(await page.evaluate(() => location.hash), '#d0-3');
      assert.ok(await page.evaluate(() => window.scrollY) > 500);

      await page.locator('#toc a[href="#d0-2"]').click();
      await page.waitForFunction(() => {
        const r = document.getElementById('d0-2').getBoundingClientRect();
        return r.top >= 0 && r.top < window.innerHeight / 2;
      });
      assert.equal(await page.evaluate(() => location.hash), '#d0-2');

      // 文档级目录项：最后几份文档较短，滚不到视口顶部，只要求进入视口
      await page.locator('#toc a.doc-link', { hasText: '另一份' }).click();
      await page.waitForFunction(() => {
        const r = document.getElementById('doc-1').getBoundingClientRect();
        return r.top >= 0 && r.top < window.innerHeight;
      });
      assert.equal(await page.evaluate(() => location.hash), '#doc-1');
    });
  });

  test('mermaid 加载成功：走本地同版本文件并渲染出图，无提示', async () => {
    await withPage({ mermaid: 'local' }, async ({ page, seen }) => {
      await page.locator('.mermaid-fig svg').waitFor({ state: 'visible' });
      assert.deepEqual(seen.mermaid, [MERMAID_URL]);
      assert.equal(await page.locator('.mermaid-note').count(), 0);
      assert.equal(await page.locator('pre > code.language-mermaid').count(), 0);
      assert.match(await page.locator('.mermaid-fig svg').textContent(), /开始/);
    });
  });

  test('mermaid 加载失败：提示「离线，mermaid 图未渲染」', async () => {
    await withPage({ mermaid: 'abort' }, async ({ page }) => {
      const note = page.locator('.mermaid-note');
      await note.waitFor({ state: 'visible' });
      assert.equal(await note.textContent(), '离线，mermaid 图未渲染');
      assert.equal(await note.getAttribute('role'), 'status');
      // 原文代码块保留
      assert.equal(await page.locator('pre > code.language-mermaid').count(), 1);
    });
  });

  test('mermaid 10 秒未就绪：提示「mermaid 未加载（离线或网络慢）」', async () => {
    await withPage({ mermaid: 'hang', clock: true, waitUntil: 'domcontentloaded' }, async ({ page }) => {
      await page.waitForSelector('section.doc[data-label="图"]');
      await page.clock.fastForward(9000);
      assert.equal(await page.locator('.mermaid-note').count(), 0);
      await page.clock.fastForward(2000);
      const note = page.locator('.mermaid-note');
      await note.waitFor({ state: 'visible' });
      assert.equal(await note.textContent(), 'mermaid 未加载（离线或网络慢）');
      assert.equal(await note.getAttribute('role'), 'status');
    });
  });
});

describe('mermaid 加载慢但最终成功', () => {
  test('提示出现后 mermaid 又加载成功：提示清除并渲染出图', async () => {
    await withPage({ mermaid: 'hang', clock: true, waitUntil: 'domcontentloaded' }, async (h) => {
      const { page } = h;
      await page.waitForSelector('section.doc[data-label="图"]');
      await page.clock.fastForward(11000);
      await page.locator('.mermaid-note').waitFor({ state: 'visible' });
      await h.releaseMermaid();
      await page.locator('.mermaid-fig svg').waitFor({ state: 'visible' });
      assert.equal(await page.locator('.mermaid-note').count(), 0);
    });
  });
});

// ── 2.3 选区、高亮、暂存 ────────────────────────────────────────────────────
describe('选区与暂存', () => {
  test('划选后出现「写意见」，保存后高亮并列入意见栏', async () => {
    await withPage({}, async ({ page }) => {
      assert.equal(await page.locator('#sdflow-annotate').isHidden(), true);
      await addNote(page, '设计', 'alpha beta', '第一条意见');
      const item = page.locator('#sdflow-notes .note-item');
      assert.equal(await item.count(), 1);
      assert.deepEqual(await stagedMarks(page), { [await item.getAttribute('data-note')]: ['alpha beta'] });
      assert.match(await item.locator('.note-head').textContent(), /^#1 设计 › 重名节/);
      assert.equal(await item.locator('.note-quote').textContent(), 'alpha beta');
      assert.equal(await item.locator('.note-comment').textContent(), '第一条意见');
      assert.equal(await page.locator('#sdflow-notes h2').textContent(), '意见（1）');
      assert.equal(await page.locator('#sdflow-annotate').isHidden(), true);
    });
  });

  test('刷新后意见仍在，高亮重新恢复', async () => {
    await withPage({}, async ({ page }) => {
      await addNote(page, '设计', 'zeta eta', '刷新前写的');
      await page.reload();
      const items = page.locator('#sdflow-notes .note-item');
      assert.equal(await items.count(), 1);
      assert.equal(await page.locator('#sdflow-notes .note-comment').textContent(), '刷新前写的');
      const first = await items.nth(0).getAttribute('data-note');
      assert.deepEqual(await stagedMarks(page), { [first]: ['zeta eta'] });
      // 暂存里的序号接着往下排；两条意见的高亮各归各的 id
      await addNote(page, '设计', 'iota kappa', '刷新后写的');
      assert.equal(await items.nth(1).locator('.note-head').textContent().then((t) => t.slice(0, 2)), '#2');
      const second = await items.nth(1).getAttribute('data-note');
      assert.deepEqual(await stagedMarks(page), { [first]: ['zeta eta'], [second]: ['iota kappa'] });
    });
  });

  test('原文对不上的暂存意见仍列出并标「原文已对不上，仅列出」', async () => {
    await withPage({}, async ({ page }) => {
      await seedNotes(page, [
        { n: 1, doc: '设计', heading: '', quote: '这段话原文里没有', before: '', after: '', comment: '孤儿', copied: false },
      ]);
      await page.reload();
      const item = page.locator('#sdflow-notes .note-item');
      assert.equal(await item.count(), 1);
      assert.match(await item.locator('.note-badge').textContent(), /原文已对不上，仅列出/);
      assert.equal(await page.locator('mark.sdflow-hl').count(), 0);
    });
  });

  test('localStorage 写不进时，加载就提示「意见无法跨刷新保留」', async () => {
    const block = `Storage.prototype.setItem = function () { throw new Error('quota'); };`;
    await withPage({ initScripts: [block] }, async ({ page }) => {
      const warn = page.locator('.notice[role="alert"]');
      assert.equal(await warn.textContent(), '意见无法跨刷新保留，请及时复制');
      // 页面照常可用：仍能写意见
      await addNote(page, '设计', 'alpha beta', '写不进暂存');
      assert.equal(await page.locator('#sdflow-notes .note-item').count(), 1);
      assert.equal(await page.locator('.notice').count(), 1);
    });
  });

  test('读写探针通过但保存失败时，保存那刻提示', async () => {
    const block = `(() => {
      const orig = Storage.prototype.setItem;
      Storage.prototype.setItem = function (k, v) {
        if (String(k).endsWith(':probe')) return orig.call(this, k, v);
        throw new Error('quota');
      };
    })();`;
    await withPage({ initScripts: [block] }, async ({ page }) => {
      assert.equal(await page.locator('.notice').count(), 0);
      await addNote(page, '设计', 'alpha beta', '保存会失败');
      assert.equal(await page.locator('.notice[role="alert"]').textContent(), '意见无法跨刷新保留，请及时复制');
    });
  });

  test('另一 file:// 页写入含 <script> 的意见：以文本显示，不执行（RVP-15 残余）', async () => {
    await withPage({}, async ({ ctx, page, dialogs }) => {
      const key = 'sdflow-review:' + (await page.evaluate(() => location.pathname));
      const payload = '<script>window.__pwn=9</script><img src=x onerror="window.__pwn=10">';
      const other = await ctx.newPage();
      await other.goto(pathToFileURL(path.join(repo, 'other-page.html')).href);
      await seedNotes(other, [
        { n: 1, doc: '设计', heading: '', quote: 'alpha beta', before: '', after: '', comment: payload, copied: false },
      ], { key });
      await other.close();
      await page.reload();
      assert.equal(await page.locator('#sdflow-notes .note-comment').textContent(), payload);
      assert.equal(await page.locator('#sdflow-notes script, #sdflow-notes img').count(), 0);
      assert.equal(await page.evaluate(() => window.__pwn), undefined);
      assert.deepEqual(dialogs, []);
    });
  });
});

// ── 2.4 复制、清空、空意见、快捷键 ──────────────────────────────────────────
describe('复制与对话框操作', () => {
  test('复制成功：剪贴板得到带落盘指示的全文，意见标「已复制」', async () => {
    await withPage({ initScripts: [clipboardStub('ok')] }, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲意见');
      await page.locator('#sdflow-copy-new').click();
      await page.waitForFunction(() => document.getElementById('sdflow-copy-status').textContent.startsWith('已复制'));
      assert.match(await page.locator('#sdflow-copy-status').textContent(), /^已复制 1 条意见到剪贴板/);
      const clip = await page.evaluate(() => window.__clip);
      assert.equal(clip.length, 1);
      const lines = clip[0].split('\n');
      assert.equal(lines[0], '请先把下面全文原样追加到 `openspec/changes/x/review/review-notes.md`（不存在则新建），再逐条处理这些意见。');
      assert.ok(lines.includes('页面：`openspec/changes/x/review/page.html`'));
      assert.ok(lines.includes('## 1. 设计（openspec/changes/x/design.md） › 重名节'));
      assert.ok(lines.includes('> alpha beta'));
      assert.ok(lines.includes('甲意见'));
      const json = clip[0].match(/```json\n(.*)\n```\n$/)[1];
      const data = JSON.parse(json);
      assert.match(data.notes[0].id, /^[0-9a-f]{16}$/);
      assert.match(data.copied_at, /^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$/);
      assert.ok(clip[0].includes('复制于：' + data.copied_at));
      assert.deepEqual(data, {
        v: 2,
        page: 'openspec/changes/x/review/page.html',
        copied_at: data.copied_at,
        notes: [{
          n: 1, id: data.notes[0].id, doc: '设计', path: 'openspec/changes/x/design.md', heading: '重名节',
          quote: 'alpha beta', before: '设计总览\n重名节\n第一处正文 ', after: ' gamma delta epsilon。\n到另一份文档 外链 ', comment: '甲意见',
          inFigure: false,
        }],
      });
      assert.match(await page.locator('#sdflow-notes .note-badge').textContent(), /已复制/);
    });
  });

  test('剪贴板被拒：提示手动复制，全文已全选，且不自动标已复制', async () => {
    await withPage({ initScripts: [clipboardStub('reject')] }, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲意见');
      await page.locator('#sdflow-copy-new').click();
      await page.waitForFunction(() => document.getElementById('sdflow-copy-status').textContent.startsWith('自动复制失败'));
      const sel = await page.evaluate(() => {
        const t = document.getElementById('sdflow-copy-text');
        return { active: document.activeElement === t, start: t.selectionStart, end: t.selectionEnd, len: t.value.length };
      });
      assert.deepEqual(sel, { active: true, start: 0, end: sel.len, len: sel.len });
      assert.ok(sel.len > 0);
      assert.equal(await page.locator('#sdflow-notes .note-badge').count(), 0);
      // 人手动复制后点「标记为已复制」才标记
      const mark = page.locator('#sdflow-copy-dialog .sdflow-btn', { hasText: '标记为已复制' });
      await mark.click();
      assert.equal(await page.locator('#sdflow-copy-status').textContent(), '已标记为已复制。');
      assert.match(await page.locator('#sdflow-notes .note-badge').textContent(), /已复制/);
    });
  });

  test('「复制意见」只含未复制项，「复制全部」含全部', async () => {
    await withPage({ initScripts: [clipboardStub('ok')] }, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲意见');
      await addNote(page, '设计', 'zeta eta', '乙意见');
      assert.equal(await page.locator('#sdflow-copy-new').textContent(), '复制意见（2）');
      await page.locator('#sdflow-copy-new').click();
      await page.waitForFunction(() => window.__clip.length === 1);
      await page.locator('#sdflow-copy-close').click();

      assert.equal(await page.locator('#sdflow-copy-new').isDisabled(), true);
      assert.equal(await page.locator('#sdflow-copy-new').textContent(), '复制意见（0）');
      await addNote(page, '设计', 'iota kappa', '丙意见');
      assert.equal(await page.locator('#sdflow-copy-new').textContent(), '复制意见（1）');

      await page.locator('#sdflow-copy-new').click();
      await page.waitForFunction(() => window.__clip.length === 2);
      await page.locator('#sdflow-copy-close').click();
      const second = await page.evaluate(() => window.__clip[1]);
      assert.match(second, /丙意见/);
      assert.doesNotMatch(second, /甲意见|乙意见/);

      await page.locator('#sdflow-copy-all').click();
      await page.waitForFunction(() => window.__clip.length === 3);
      const third = await page.evaluate(() => window.__clip[2]);
      for (const c of ['甲意见', '乙意见', '丙意见']) assert.match(third, new RegExp(c));
      assert.match(await page.locator('#sdflow-copy-status').textContent(), /^已复制 3 条意见/);
    });
  });

  test('「清空」要点两次，4 秒内不点第二次则还原', async () => {
    await withPage({ clock: true }, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲意见');
      const clear = page.locator('#sdflow-clear');
      await clear.click();
      assert.equal(await clear.textContent(), '再点一次确认清空');
      assert.equal(await page.locator('#sdflow-notes .note-item').count(), 1);
      await page.clock.fastForward(4500);
      assert.equal(await clear.textContent(), '清空');
      assert.equal(await page.locator('#sdflow-notes .note-item').count(), 1);

      await clear.click();
      await clear.click();
      assert.equal(await page.locator('#sdflow-notes .note-item').count(), 0);
      assert.equal(await page.locator('mark.sdflow-hl').count(), 0);
      assert.equal(await page.locator('#sdflow-notes h2').textContent(), '意见（0）');
      assert.equal(await clear.isDisabled(), true);
      // 清空同步到暂存：刷新后仍是空
      await page.reload();
      assert.equal(await page.locator('#sdflow-notes .note-item').count(), 0);
    });
  });

  test('空意见：提示「意见不能为空」，对话框保持打开', async () => {
    await withPage({}, async ({ page }) => {
      await selectText(page, '设计', 'alpha beta');
      await page.locator('#sdflow-annotate').click();
      await page.locator('#sdflow-note-dialog .sdflow-btn.primary').click();
      assert.equal(await page.locator('#sdflow-note-error').textContent(), '意见不能为空');
      assert.equal(await page.locator('#sdflow-note-dialog').isVisible(), true);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'sdflow-note-text');
      // 只有空白也算空
      await page.locator('#sdflow-note-text').fill('   \n ');
      await page.keyboard.press('Control+Enter');
      assert.equal(await page.locator('#sdflow-note-error').textContent(), '意见不能为空');
      assert.equal(await page.locator('#sdflow-notes .note-item').count(), 0);
    });
  });

  test('快捷键：Ctrl+Enter 与 ⌘+Enter 保存，Esc 取消并放回选区', async () => {
    await withPage({}, async ({ page }) => {
      await selectText(page, '设计', 'alpha beta');
      await page.locator('#sdflow-annotate').click();
      await page.locator('#sdflow-note-text').fill('Ctrl 保存');
      await page.keyboard.press('Control+Enter');
      assert.equal(await page.locator('#sdflow-note-dialog').isHidden(), true);
      assert.equal(await page.locator('#sdflow-notes .note-item').count(), 1);

      await selectText(page, '设计', 'zeta eta');
      await page.locator('#sdflow-annotate').click();
      await page.locator('#sdflow-note-text').fill('Meta 保存');
      await page.keyboard.press('Meta+Enter');
      assert.equal(await page.locator('#sdflow-note-dialog').isHidden(), true);
      assert.equal(await page.locator('#sdflow-notes .note-item').count(), 2);

      // Esc：不保存，选区放回，「写意见」按钮仍在
      await selectText(page, '设计', 'iota kappa');
      await page.locator('#sdflow-annotate').click();
      await page.locator('#sdflow-note-text').fill('不会保存');
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#sdflow-note-dialog').isHidden(), true);
      assert.equal(await page.locator('#sdflow-notes .note-item').count(), 2);
      assert.equal(await page.evaluate(() => window.getSelection().toString()), 'iota kappa');
      assert.equal(await page.locator('#sdflow-annotate').isVisible(), true);
    });
  });
});

// ── 4.1 意见 id ─────────────────────────────────────────────────────────────
const ID_RE = /^[0-9a-f]{16}$/;

async function storedNotes(page, key) {
  return page.evaluate((k) => JSON.parse(localStorage.getItem(k)).notes, key);
}

describe('意见 id', () => {
  test('旧意见（无 id）加载时补 id，写回暂存，刷新后不变', async () => {
    await withPage({}, async ({ page }) => {
      const key = 'sdflow-review:' + pagePathname;
      await seedNotes(page, [
        { n: 1, doc: '设计', heading: '', quote: 'alpha beta', before: '', after: '', comment: '旧意见', copied: false },
      ]);
      await page.reload();
      const first = (await storedNotes(page, key))[0].id;
      assert.match(first, ID_RE);
      await page.reload();
      assert.equal((await storedNotes(page, key))[0].id, first);
    });
  });

  test('id 形态不合法被替换，合法的原样保留；新建意见带 id', async () => {
    await withPage({}, async ({ page }) => {
      const key = 'sdflow-review:' + pagePathname;
      const good = '0123456789abcdef';
      await seedNotes(page, [
        { id: 'ZZ-not-hex', n: 1, doc: '设计', heading: '', quote: 'alpha beta', before: '', after: '', comment: '坏 id', copied: false },
        { id: good, n: 2, doc: '设计', heading: '', quote: 'zeta eta', before: '', after: '', comment: '好 id', copied: false },
      ]);
      await page.reload();
      const notes = await storedNotes(page, key);
      assert.match(notes[0].id, ID_RE);
      assert.notEqual(notes[0].id, 'ZZ-not-hex');
      assert.equal(notes[1].id, good);
      await addNote(page, '设计', 'iota kappa', '新意见');
      const after = await storedNotes(page, key);
      assert.match(after[2].id, ID_RE);
      assert.equal(new Set(after.map((n) => n.id)).size, 3);
    });
  });
});

// ── 4.2 已落盘意见 ──────────────────────────────────────────────────────────
// 按页面复制出来的 v2 块格式拼一段 review-notes.md 内容（page 为 page.html）。
function notesBlock(notes) {
  const full = notes.map((n, i) => Object.assign({
    n: i + 1, id: '', doc: '设计', path: 'openspec/changes/x/design.md', heading: '重名节',
    quote: 'alpha beta', before: '', after: '', comment: '',
  }, n));
  return '\n## 一次粘回\n\n```json\n' +
    JSON.stringify({ v: 2, page: 'openspec/changes/x/review/page.html', copied_at: '2026-10-20 10:00:00', notes: full }) +
    '\n```\n';
}

// 建仓，写入 review-notes.md 后重新生成。
function makeRepoWithNotes(notes) {
  const r = makeRepo();
  fs.writeFileSync(r.notesFile, notesBlock(notes), 'utf-8');
  renderPage(r.root);
  return r;
}

const SAVED_ID = 'aaaaaaaaaaaaaaaa';
const savedItems = (page) => page.locator('#sdflow-notes .saved-group .note-item');
const stagedItems = (page) => page.locator('#sdflow-notes .notes-list').first().locator('.note-item');

describe('已落盘意见显示', () => {

  test('没有已落盘意见时不显示该分组', async () => {
    await withPage({}, async ({ page }) => {
      assert.equal(await page.locator('#sdflow-notes .saved-group').isHidden(), true);
    });
  });

  test('显示路径加行号、上级标题、引用与正文；正文虚线高亮；只读；不进复制文本', async () => {
    await withRepo(() => makeRepoWithNotes([{ id: SAVED_ID, comment: '已落盘的意见' }]), async (r) => {
      await withPage({ url: r.url, initScripts: [clipboardStub('ok')] }, async ({ page, errors }) => {
        assert.equal(await page.locator('#sdflow-notes .saved-group h3').textContent(), '已落盘意见（1）');
        const item = savedItems(page);
        assert.equal(await item.count(), 1);
        assert.match(await item.locator('.note-head').textContent(), /^已落盘 1 openspec\/changes\/x\/design\.md:\d+ › 重名节$/);
        assert.equal(await item.locator('.note-quote').textContent(), 'alpha beta');
        assert.equal(await item.locator('.note-comment').textContent(), '已落盘的意见');
        // 不可编辑、不可删除
        assert.equal(await item.locator('.edit-btn, .del-btn').count(), 0);
        // 正文虚线边框，不靠颜色区分
        const mark = page.locator(`mark.sdflow-saved-hl[data-saved="${SAVED_ID}"]`);
        assert.equal(await mark.textContent(), 'alpha beta');
        assert.equal(await mark.evaluate((el) => getComputedStyle(el).borderTopStyle), 'dashed');
        // 不进未复制集合：暂存为空时「复制意见」不可用
        assert.equal(await page.locator('#sdflow-copy-new').isDisabled(), true);
        assert.equal(await page.locator('#sdflow-notes h2').textContent(), '意见（0）');
        await addNote(page, '设计', 'zeta eta', '暂存的意见');
        await page.locator('#sdflow-copy-all').click();
        await page.waitForFunction(() => document.getElementById('sdflow-copy-status').textContent.startsWith('已复制'));
        const clip = (await page.evaluate(() => window.__clip))[0];
        const data = JSON.parse(clip.match(/```json\n(.*)\n```\n$/)[1]);
        assert.equal(data.notes.length, 1);
        assert.equal(data.notes[0].comment, '暂存的意见');
        assert.ok(!clip.includes('已落盘的意见'));
        assert.deepEqual(errors, []);
      });
    });
  });

  test('意见正文含 <img onerror> 时只作文字显示，不执行', async () => {
    const payload = '<img src=x onerror="window.__pwn=9">';
    await withRepo(() => makeRepoWithNotes([{ id: SAVED_ID, comment: payload, heading: '<b>标题</b>' }]), async (r) => {
      await withPage({ url: r.url }, async ({ page, dialogs }) => {
        assert.equal(await savedItems(page).locator('.note-comment').textContent(), payload);
        assert.equal(await savedItems(page).locator('img, b').count(), 0);
        await expectNoScriptRan(page, dialogs);
      });
    });
  });

  test('原文找不到标「原文已变」且不高亮；出现多处无法区分标「未在正文高亮」', async () => {
    await withRepo(() => makeRepoWithNotes([
      { id: SAVED_ID, quote: '这段话已经被改掉了', comment: '孤儿' },
      { id: 'bbbbbbbbbbbbbbbb', quote: '重名节', before: 'zz', after: 'yy', comment: '多处' },
    ]), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        const items = savedItems(page);
        assert.equal(await items.count(), 2);
        assert.match(await items.nth(0).locator('.note-badge').textContent(), /^原文已变$/);
        assert.match(await items.nth(1).locator('.note-badge').textContent(), /^未在正文高亮$/);
        assert.equal(await page.locator('mark.sdflow-saved-hl').count(), 0);
        // 原文已变没有可定位的位置；未在正文高亮的意见有「定位」（点了只滚到所在文档并提示，见 RVP-13）
        assert.equal(await items.nth(0).locator('.note-actions').count(), 0);
        assert.equal(await items.nth(1).locator('.note-actions .sdflow-btn').textContent(), '定位');
      });
    });
  });

  test('数据块被改成非法 JSON：文档照常渲染，意见栏提示无法读取', async () => {
    await withRepo(() => makeRepoWithNotes([{ id: SAVED_ID, comment: 'x' }]), async (r) => {
      const file = new URL(r.url);
      const html = fs.readFileSync(file, 'utf-8');
      const broken = html.replace(/(<script type="application\/json" id="sdflow-saved-notes">)[\s\S]*?(<\/script>)/, '$1{broken$2');
      assert.notEqual(broken, html);
      fs.writeFileSync(file, broken, 'utf-8');
      await withPage({ url: r.url }, async ({ page, errors }) => {
        assert.equal(await page.locator('section.doc').count(), DOCS.length);
        assert.match(await page.locator('#sdflow-notes').textContent(), /已落盘意见无法读取/);
        assert.equal(await page.locator('#sdflow-notes .saved-group').isHidden(), true);
        assert.deepEqual(errors, []);
      });
    });
  });

  test('暂存与已落盘都是 1 号：删除暂存意见不影响已落盘高亮', async () => {
    await withRepo(() => makeRepoWithNotes([{ id: SAVED_ID, n: 1, comment: '已落盘 1 号' }]), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        await addNote(page, '设计', 'zeta eta', '暂存 1 号');
        assert.match(await stagedItems(page).locator('.note-head').textContent(), /^#1 /);
        assert.equal(await page.locator('mark.sdflow-saved-hl').count(), 1);
        await page.locator('#sdflow-notes .del-btn').click();
        assert.equal(await page.locator('mark.sdflow-hl').count(), 0);
        assert.equal(await page.locator(`mark.sdflow-saved-hl[data-saved="${SAVED_ID}"]`).textContent(), 'alpha beta');
        assert.equal(await savedItems(page).count(), 1);
      });
    });
  });

  test('合并：同 id 已复制只显示一次；未复制且正文改过则两条都显示并进入复制集合', async () => {
    await withRepo(() => makeRepoWithNotes([{ id: SAVED_ID, comment: '落盘版' }]), async (r) => {
      const key = 'sdflow-review:' + r.pathname;
      const base = { n: 1, id: SAVED_ID, doc: '设计', heading: '重名节', quote: 'alpha beta', before: '', after: '' };
      await withPage({ url: r.url, initScripts: [clipboardStub('ok')] }, async ({ page }) => {
        await seedNotes(page, [Object.assign({ comment: '落盘版', copied: true }, base)], { key });
        await page.reload();
        assert.equal(await stagedItems(page).count(), 0);
        assert.equal(await savedItems(page).count(), 1);

        await seedNotes(page, [Object.assign({ comment: '粘回后又改的', copied: false }, base)], { key });
        await page.reload();
        assert.equal(await stagedItems(page).count(), 1);
        assert.match(await stagedItems(page).locator('.note-badge').textContent(), /已修改，未落盘/);
        assert.equal(await savedItems(page).count(), 1);
        await page.locator('#sdflow-copy-new').click();
        await page.waitForFunction(() => document.getElementById('sdflow-copy-status').textContent.startsWith('已复制'));
        const clip = (await page.evaluate(() => window.__clip))[0];
        assert.ok(clip.includes('粘回后又改的'));
        assert.ok(!clip.includes('落盘版'));
        // 改过的暂存版复制后即隐藏（RVP-19）：它在正文的暂存高亮一并拿掉，已落盘高亮不动
        assert.equal(await stagedItems(page).count(), 0);
        assert.equal(await page.locator('mark.sdflow-hl').count(), 0);
        assert.equal(await page.locator(`mark.sdflow-saved-hl[data-saved="${SAVED_ID}"]`).textContent(), 'alpha beta');
      });
    });
  });

  test('「已修改，未落盘」的暂存意见编辑回与已落盘版相同：从列表消失，正文不留它的高亮', async () => {
    await withRepo(() => makeRepoWithNotes([{ id: SAVED_ID, comment: '落盘版' }]), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        await seedNotes(page, [
          { n: 1, id: SAVED_ID, doc: '设计', heading: '重名节', quote: 'alpha beta', before: '', after: '', comment: '改过', copied: false },
        ], { key: 'sdflow-review:' + r.pathname });
        await page.reload();
        assert.match(await stagedItems(page).locator('.note-badge').first().textContent(), /已修改，未落盘/);
        assert.deepEqual(await stagedMarks(page), { [SAVED_ID]: ['alpha beta'] });
        await stagedItems(page).locator('.edit-btn').click();
        await page.locator('#sdflow-note-text').fill('落盘版');
        await page.keyboard.press('Control+Enter');
        assert.equal(await stagedItems(page).count(), 0);
        assert.deepEqual(await stagedMarks(page), {});
        assert.equal(await page.locator(`mark.sdflow-saved-hl[data-saved="${SAVED_ID}"]`).textContent(), 'alpha beta');
        // 「编辑」按钮随这条一起消失：焦点落到正文区域
        assert.equal(await activeId(page), 'main');
      });
    });
  });

  test('图内划选的已落盘意见（inFigure）：新 context 打开，原文在正文唯一出现也不高亮，标「未在正文高亮」', async () => {
    await withRepo(() => makeRepoWithNotes([{ id: SAVED_ID, comment: '图内', inFigure: true }]), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        assert.equal(await savedItems(page).locator('.note-badge').textContent(), '未在正文高亮');
        assert.equal(await page.locator('mark.sdflow-saved-hl').count(), 0);
        assert.equal(await savedItems(page).locator('.jump-btn').count(), 1);
      });
    });
  });

  test('记着已高亮、mark 却丢了：点「定位」改标「未在正文高亮」，提示并把焦点放回这条的「定位」', async () => {
    await withRepo(() => makeRepoWithNotes([{ id: SAVED_ID, comment: '已落盘' }]), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        await addNote(page, '设计', 'zeta eta', '暂存');
        const unwrap = (sel) => page.evaluate((s) => {
          const m = document.querySelector(s);
          m.replaceWith(...m.childNodes);
        }, sel);
        for (const [items, sel] of [[stagedItems(page), 'mark.sdflow-hl'], [savedItems(page), 'mark.sdflow-saved-hl']]) {
          assert.equal(await items.locator('.note-badge').count(), 0);
          await unwrap(sel);
          await items.locator('.jump-btn').click();
          assert.equal(await items.locator('.note-badge').textContent(), '未在正文高亮');
          assert.equal(await page.locator('#sdflow-jump-hint').textContent(), '未在正文高亮');
          assert.equal(await items.locator('.jump-btn').evaluate((b) => b === document.activeElement), true);
        }
      });
    });
  });

  test('合并：已落盘无 id 时，doc+原文+正文相同的暂存意见视为同一条', async () => {
    await withRepo(() => makeRepoWithNotes([{ id: '', comment: '旧格式意见' }]), async (r) => {
      const key = 'sdflow-review:' + r.pathname;
      await withPage({ url: r.url }, async ({ page }) => {
        await seedNotes(page, [
          { n: 1, doc: '设计', heading: '重名节', quote: 'alpha beta', before: '', after: '', comment: '旧格式意见', copied: false },
          { n: 2, doc: '设计', heading: '重名节', quote: 'zeta eta', before: '', after: '', comment: '另一条', copied: false },
        ], { key });
        await page.reload();
        assert.equal(await stagedItems(page).count(), 1);
        assert.equal(await stagedItems(page).locator('.note-comment').textContent(), '另一条');
        assert.equal(await savedItems(page).count(), 1);
      });
    });
  });
});

// ── 4.3 回显端到端 ──────────────────────────────────────────────────────────
describe('回显端到端', () => {
  test('context A 写意见并复制 → 追加 review-notes.md → 重新生成 → 新 context B 看到并定位；A 重开只显示一次', async () => {
    await withRepo(() => makeRepo(), async (r) => {
      const a = await openPage({ url: r.url, initScripts: [clipboardStub('ok')] });
      try {
        await addNote(a.page, '设计', 'alpha beta', '端到端意见');
        appendPasted(r, await copyOnce(a.page));
        renderPage(r.root);

        // 同 context 重开：暂存里那条已复制，只显示已落盘版
        await a.page.reload();
        assert.equal(await stagedItems(a.page).count(), 0);
        assert.equal(await savedItems(a.page).count(), 1);
        assert.equal(await a.page.locator('#sdflow-notes .note-item').count(), 1);

        // 新 context：没有任何 localStorage，仍能看到并定位
        await withPage({ url: r.url }, async ({ page }) => {
          const item = savedItems(page);
          assert.equal(await item.count(), 1);
          assert.equal(await item.locator('.note-comment').textContent(), '端到端意见');
          assert.match(await item.locator('.note-head').textContent(), /design\.md:\d+ › 重名节/);
          await item.locator('.sdflow-btn', { hasText: '定位' }).click();
          const mark = page.locator('mark.sdflow-saved-hl.flash');
          assert.equal(await mark.count(), 1);
          assert.equal(await mark.textContent(), 'alpha beta');
          assert.equal(await mark.evaluate((el) => {
            const b = el.getBoundingClientRect();
            return b.top >= 0 && b.bottom <= window.innerHeight;
          }), true);
        });
      } finally { await a.close(); }
    });
  });

  test('图内划选的意见复制落盘后 inFigure 随块带出：新 context 里标「未在正文高亮」', async () => {
    await withRepo(() => makeRepo(), async (r) => {
      const a = await openPage({ url: r.url, initScripts: [clipboardStub('ok')] });
      try {
        await a.page.locator('section.doc[data-label="图"] .mermaid-fig svg').waitFor();
        await addNote(a.page, '图', '开始', '图上的意见');
        const text = await copyOnce(a.page);
        assert.equal(JSON.parse(text.match(/```json\n(.*)\n```\n$/)[1]).notes[0].inFigure, true);
        appendPasted(r, text);
        renderPage(r.root);
      } finally { await a.close(); }
      await withPage({ url: r.url }, async ({ page }) => {
        const embedded = await page.evaluate(() => JSON.parse(document.getElementById('sdflow-saved-notes').textContent));
        assert.equal(embedded[0].inFigure, true);
        assert.equal(await savedItems(page).locator('.note-badge').textContent(), '未在正文高亮');
        assert.equal(await page.locator('mark.sdflow-saved-hl').count(), 0);
      });
    });
  });

  test('粘回后改掉原文再重新生成：新 context 里标「原文已变」', async () => {
    await withRepo(() => makeRepo(), async (r) => {
      const a = await openPage({ url: r.url, initScripts: [clipboardStub('ok')] });
      try {
        await addNote(a.page, '设计', 'alpha beta', '会失效的意见');
        appendPasted(r, await copyOnce(a.page));
      } finally { await a.close(); }
      const design = path.join(r.changeDir, 'design.md');
      fs.writeFileSync(design, fs.readFileSync(design, 'utf-8').replace('alpha beta', '已改写的句子'), 'utf-8');
      renderPage(r.root);
      await withPage({ url: r.url }, async ({ page }) => {
        const item = savedItems(page);
        assert.equal(await item.count(), 1);
        assert.match(await item.locator('.note-badge').textContent(), /^原文已变$/);
        assert.equal(await page.locator('mark.sdflow-saved-hl').count(), 0);
      });
    });
  });
});

// ── 2.5 / 4.5 对话框焦点与「写意见」按钮可达 ────────────────────────────────
const activeId = (page) => page.evaluate(() => document.activeElement.id || document.activeElement.tagName);

describe('对话框焦点生命周期', () => {
  async function openNoteDialog(page) {
    await selectText(page, '设计', 'alpha beta');
    await page.locator('#sdflow-annotate').click();
    await page.locator('#sdflow-note-dialog').waitFor({ state: 'visible' });
  }

  test('写意见对话框：打开时焦点进输入框，Tab / Shift+Tab 在面板内循环', async () => {
    await withPage({}, async ({ page }) => {
      await openNoteDialog(page);
      assert.equal(await activeId(page), 'sdflow-note-text');
      const order = [];
      for (let i = 0; i < 4; i++) {
        await page.keyboard.press('Tab');
        order.push(await page.evaluate(() => document.activeElement.textContent || document.activeElement.id));
      }
      // 输入框 → 取消 → 保存 → 回到输入框 → 取消（输入框没有文字，记它的 id）
      assert.deepEqual(order, ['取消', '保存', 'sdflow-note-text', '取消']);
      await page.keyboard.press('Shift+Tab');
      assert.equal(await activeId(page), 'sdflow-note-text');
      await page.keyboard.press('Shift+Tab');
      assert.equal(await page.evaluate(() => document.activeElement.textContent), '保存');
    });
  });

  test('写意见对话框：Esc 只关闭一次，焦点回到「写意见」按钮', async () => {
    await withPage({}, async ({ page }) => {
      await openNoteDialog(page);
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#sdflow-note-dialog').isHidden(), true);
      assert.equal(await activeId(page), 'sdflow-annotate');
    });
  });

  test('编辑对话框：Esc 后焦点回到该条意见的「编辑」按钮，不被第二次关闭抢到 #main', async () => {
    await withPage({}, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲');
      await page.locator('#sdflow-notes .edit-btn').click();
      await page.locator('#sdflow-note-dialog').waitFor({ state: 'visible' });
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#sdflow-note-dialog').isHidden(), true);
      assert.equal(await page.evaluate(() => document.activeElement.classList.contains('edit-btn')), true);
    });
  });

  test('编辑对话框保存后（「编辑」按钮被重建）焦点回到新的「编辑」按钮', async () => {
    await withPage({}, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲');
      await page.locator('#sdflow-notes .edit-btn').click();
      await page.locator('#sdflow-note-text').fill('甲改');
      await page.keyboard.press('Control+Enter');
      assert.equal(await page.evaluate(() => document.activeElement.classList.contains('edit-btn')), true);
    });
  });

  test('复制对话框：打开时焦点进全文框，Tab 在面板内循环，Esc 关闭后焦点回到「复制全部」', async () => {
    await withPage({ initScripts: [clipboardStub('ok')] }, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲');
      await page.locator('#sdflow-copy-all').click();
      await page.waitForFunction(() => document.getElementById('sdflow-copy-status').textContent.startsWith('已复制'));
      assert.equal(await activeId(page), 'sdflow-copy-text');
      await page.keyboard.press('Tab');
      assert.equal(await activeId(page), 'sdflow-copy-close');
      await page.keyboard.press('Tab');
      assert.equal(await activeId(page), 'sdflow-copy-text');
      await page.keyboard.press('Shift+Tab');
      assert.equal(await activeId(page), 'sdflow-copy-close');
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#sdflow-copy-dialog').isHidden(), true);
      assert.equal(await activeId(page), 'sdflow-copy-all');
    });
  });

  test('复制对话框关闭时打开它的按钮已禁用：焦点移到 #main', async () => {
    await withPage({ initScripts: [clipboardStub('ok')] }, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲');
      await page.locator('#sdflow-copy-new').click();
      await page.waitForFunction(() => document.getElementById('sdflow-copy-status').textContent.startsWith('已复制'));
      assert.equal(await page.locator('#sdflow-copy-new').isDisabled(), true);
      await page.locator('#sdflow-copy-close').click();
      assert.equal(await activeId(page), 'main');
    });
  });

  test('写意见对话框打开后点了对话框外的空白处：Esc 仍能关闭（RVP-14）', async () => {
    await withPage({}, async ({ page }) => {
      await openNoteDialog(page);
      await page.mouse.click(4, 4);
      assert.equal(await activeId(page), 'BODY');
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#sdflow-note-dialog').isHidden(), true);
    });
  });

  test('写意见对话框打开后焦点落到页面主体：Tab 把焦点移回对话框内（RVP-14）', async () => {
    await withPage({}, async ({ page }) => {
      await openNoteDialog(page);
      await page.mouse.click(4, 4);
      assert.equal(await activeId(page), 'BODY');
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => !!document.activeElement.closest('#sdflow-note-dialog')), true);
      assert.equal(await page.locator('#sdflow-note-dialog').isVisible(), true);
    });
  });

  test('复制对话框打开后焦点落到页面主体：Esc 关闭、Tab 回到对话框内', async () => {
    await withPage({ initScripts: [clipboardStub('ok')] }, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲');
      await page.locator('#sdflow-copy-all').click();
      await page.waitForFunction(() => document.getElementById('sdflow-copy-status').textContent.startsWith('已复制'));
      await page.mouse.click(4, 4);
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => !!document.activeElement.closest('#sdflow-copy-dialog')), true);
      await page.mouse.click(4, 4);
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#sdflow-copy-dialog').isHidden(), true);
    });
  });

  test('对话框已关闭后按 Esc 不再触发任何关闭逻辑（焦点保持不动）', async () => {
    await withPage({}, async ({ page }) => {
      await openNoteDialog(page);
      await page.keyboard.press('Escape');
      assert.equal(await activeId(page), 'sdflow-annotate');
      await page.keyboard.press('Escape');
      assert.equal(await activeId(page), 'sdflow-annotate');
    });
  });
});

// 用真实鼠标拖选 needle（单行内）。程序化的 addRange 不会设置 Chromium 的顺序焦点导航起点，
// 只有真实鼠标选择会，所以键盘可达性的用例必须这样选。
async function dragSelect(page, docLabel, needle) {
  const box = await page.evaluate(({ docLabel, needle }) => {
    const body = document.querySelector(`section.doc[data-label="${docLabel}"] .doc-body`);
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const i = node.data.indexOf(needle);
      if (i < 0) continue;
      // 页面设了 smooth 滚动，不指定 instant 会在滚动途中取到旧坐标
      node.parentElement.scrollIntoView({ block: 'center', behavior: 'instant' });
      const range = document.createRange();
      range.setStart(node, i);
      range.setEnd(node, i + needle.length);
      const r = range.getClientRects()[0];
      return { x1: r.left + 1, x2: r.right - 1, y: r.top + r.height / 2 };
    }
    throw new Error('找不到要划选的文字：' + needle);
  }, { docLabel, needle });
  await page.mouse.move(box.x1, box.y);
  await page.mouse.down();
  await page.mouse.move(box.x2, box.y, { steps: 5 });
  await page.mouse.up();
  await page.locator('#sdflow-annotate').waitFor({ state: 'visible' });
}

// 划选后连按 Tab 直到焦点到「写意见」按钮（最多 30 次），返回每一步焦点所在：{id, inSection}。
async function tabTrail(page, docLabel) {
  const trail = [];
  for (let i = 0; i < 30; i++) {
    await page.keyboard.press('Tab');
    const info = await page.evaluate((lab) => ({
      id: document.activeElement.id,
      inSection: !!document.activeElement.closest(`section.doc[data-label="${lab}"]`),
    }), docLabel);
    trail.push(info);
    if (info.id === 'sdflow-annotate') break;
  }
  return trail;
}

function assertTrailStaysInSection(trail) {
  assert.equal(trail[trail.length - 1].id, 'sdflow-annotate', '按 Tab 轨迹：' + JSON.stringify(trail));
  assert.ok(trail.slice(0, -1).every((t) => t.inSection), '途中离开了所选文档节：' + JSON.stringify(trail));
}

describe('「写意见」按钮键盘可达（D14）', () => {
  test('划选后按 Tab 能到达按钮，途中不经过所选文档节之外的元素', async () => {
    await withPage({}, async ({ page }) => {
      await dragSelect(page, '设计', 'alpha beta');
      assert.equal(await page.evaluate(() => window.getSelection().toString()), 'alpha beta');
      assertTrailStaysInSection(await tabTrail(page, '设计'));
    });
  });

  test('换到末尾的另一份文档划选：按钮挪到该文档节之后，按 Tab 一步到达', async () => {
    await withPage({}, async ({ page }) => {
      await dragSelect(page, '设计', 'alpha beta');
      await page.keyboard.press('Escape');
      await dragSelect(page, '尾部', 'omega');
      assert.equal(await page.evaluate(() => window.getSelection().toString()), 'omega');
      assert.equal(await page.evaluate(() => document.getElementById('sdflow-annotate').previousElementSibling.id), 'doc-4');
      const trail = await tabTrail(page, '尾部');
      assertTrailStaysInSection(trail);
      assert.equal(trail.length, 1, '尾部文档节里没有可聚焦元素，第一下 Tab 就该到按钮：' + JSON.stringify(trail));
    });
  });

  test('正文区域平时不可聚焦；「跳到正文」把焦点移进正文，失焦后撤掉', async () => {
    await withPage({}, async ({ page }) => {
      assert.equal(await page.locator('#main').getAttribute('tabindex'), null);
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.activeElement.className), 'skip-link');
      await page.keyboard.press('Enter');
      assert.equal(await activeId(page), 'main');
      await page.keyboard.press('Tab');
      assert.notEqual(await activeId(page), 'main');
      assert.equal(await page.locator('#main').getAttribute('tabindex'), null);
    });
  });
});

// ── 4.4 页内锚点 ────────────────────────────────────────────────────────────
describe('页内锚点（GitHub slug）', () => {
  const anchorsDoc = (page) => page.locator('section.doc[data-label="锚点"] .doc-body');
  const hrefOf = (page, text) => anchorsDoc(page).locator('a', { hasText: text }).getAttribute('href');

  test('同文档中文标题链接（含百分号编码）改写为真实标题 id', async () => {
    await withPage({}, async ({ page, errors }) => {
      const id = await anchorsDoc(page).locator('h2', { hasText: '数据模型与生命周期' }).getAttribute('id');
      assert.match(id, /^d\d+-\d+$/);
      assert.equal(await hrefOf(page, '同文档中文'), '#' + id);
      assert.equal(await hrefOf(page, '同文档编码'), '#' + id);
      assert.deepEqual(errors, []);
    });
  });

  test('点击同文档链接滚到对应标题，页面 hash 为该标题 id', async () => {
    await withPage({}, async ({ page }) => {
      const id = await anchorsDoc(page).locator('h2', { hasText: '数据模型与生命周期' }).getAttribute('id');
      await anchorsDoc(page).locator('a', { hasText: '同文档中文' }).click();
      await page.waitForFunction((hid) => {
        const r = document.getElementById(hid).getBoundingClientRect();
        return r.top >= 0 && r.top < window.innerHeight / 2;
      }, id);
      assert.equal(await page.evaluate(() => location.hash), '#' + id);
    });
  });

  test('重名标题 #risks-1 指向第二个 Risks；标点标题 #a--b 命中', async () => {
    await withPage({}, async ({ page }) => {
      const ids = await anchorsDoc(page).locator('h2', { hasText: /^Risks$/ }).evaluateAll((els) => els.map((e) => e.id));
      assert.equal(ids.length, 2);
      assert.equal(await hrefOf(page, '重名第二个'), '#' + ids[1]);
      const ab = await anchorsDoc(page).locator('h2', { hasText: 'A & B' }).getAttribute('id');
      assert.equal(await hrefOf(page, '标点标题'), '#' + ab);
    });
  });

  test('同文档找不到的标题显示为纯文字（无 <a>）', async () => {
    await withPage({}, async ({ page }) => {
      assert.equal(await anchorsDoc(page).locator('a', { hasText: '缺失标题' }).count(), 0);
      assert.match(await anchorsDoc(page).locator('p').first().textContent(), /缺失标题/);
    });
  });

  test('跨文档 x.md#片段：命中指向该标题，未命中或无片段跳到该文档开头', async () => {
    await withPage({}, async ({ page }) => {
      const second = await page.locator('section.doc[data-label="设计"] h2', { hasText: '重名节' }).nth(1).getAttribute('id');
      assert.equal(await hrefOf(page, '跨文档命中'), '#' + second);
      assert.equal(await hrefOf(page, '跨文档未命中'), '#doc-1');
      assert.equal(await hrefOf(page, '跨文档无片段'), '#doc-1');
      await anchorsDoc(page).locator('a', { hasText: '跨文档命中' }).click();
      assert.equal(await page.evaluate(() => location.hash), '#' + second);
    });
  });

  test('标题 id 体系不变（仍是 d{文档序号}-{序号}），不留下待定占位', async () => {
    await withPage({}, async ({ page }) => {
      const ids = await page.locator('section.doc[data-label="设计"] :is(h1,h2,h3,h4)').evaluateAll((els) => els.map((e) => e.id));
      assert.deepEqual(ids, ['d0-1', 'd0-2', 'd0-3', 'd0-4', 'd0-5']);
      assert.equal(await page.locator('[data-pending-href]').count(), 0);
    });
  });
});

// ── 4.5 定时器与探测键 ──────────────────────────────────────────────────────
describe('定时器与探测键', () => {
  test('「清空」确认态不被旧定时器提前还原', async () => {
    await withPage({ clock: true }, async ({ page }) => {
      await addNote(page, '设计', 'alpha beta', '甲意见');
      await addNote(page, '设计', 'zeta eta', '乙意见');
      const clear = page.locator('#sdflow-clear');
      await clear.click();                       // t=0：进入确认态，旧定时器 t=4000 到点
      await page.clock.fastForward(3000);
      await page.locator('#sdflow-notes .del-btn').first().click();   // renderNotes 重置确认态
      assert.equal(await clear.textContent(), '清空');
      await clear.click();                       // t=3000：再次进入确认态，新定时器 t=7000 到点
      assert.equal(await clear.textContent(), '再点一次确认清空');
      await page.clock.fastForward(2000);        // t=5000：旧定时器若还在，已在 4000 把它还原
      assert.equal(await clear.textContent(), '再点一次确认清空');
      await page.clock.fastForward(3000);        // t=8000：新定时器到点
      assert.equal(await clear.textContent(), '清空');
    });
  });

  test('探测键写入后抛错（写入部分成功）：`:probe` 键不残留', async () => {
    const stub = `(() => {
      const orig = Storage.prototype.setItem;
      Storage.prototype.setItem = function (k, v) {
        orig.call(this, k, v);
        if (String(k).endsWith(':probe')) throw new Error('quota');
      };
    })();`;
    await withPage({ initScripts: [stub] }, async ({ page }) => {
      assert.equal(await page.locator('.notice').count(), 1);
      const keys = await page.evaluate(() => Object.keys(localStorage));
      assert.deepEqual(keys.filter((k) => k.endsWith(':probe')), []);
    });
  });
});

// ── 4.6 mermaid 图内划选 ────────────────────────────────────────────────────
describe('mermaid 图内划选', () => {
  async function figureSnapshot(page, label) {
    return page.evaluate((lab) => {
      const fig = document.querySelector(`section.doc[data-label="${lab}"] .mermaid-fig`);
      const walker = document.createTreeWalker(fig, NodeFilter.SHOW_TEXT);
      let count = 0;
      while (walker.nextNode()) count += 1;
      return { textNodes: count, text: fig.textContent, innerText: fig.innerText, marks: fig.querySelectorAll('mark').length };
    }, label);
  }

  // sequenceDiagram 另建一个多一份时序图文档的仓，不影响其余用例对「页面只有一张图」的假设。
  const SEQUENCE_DOC = ['时序', 'sequence.md', '# 时序图\n\n```mermaid\nsequenceDiagram\n  participant Alice\n  participant Bob\n  Alice->>Bob: 你好吗\n  Bob-->>Alice: 很好\n```\n'];
  for (const [kind, label, needle, withSequence] of [['flowchart（foreignObject 内 HTML 标签）', '图', '开始', false], ['sequenceDiagram（原生 <text>）', '时序', 'Alice', true]]) {
    test(`${kind}：划选保存后图不变，意见标「未在正文高亮」，刷新后不变，「定位」显示提示`, async () => {
      const r = withSequence ? makeRepo(DOCS.filter((d) => d[0] !== '图').concat([SEQUENCE_DOC])) : null;
      try {
      await withPage(r ? { url: r.url } : {}, async ({ page, errors }) => {
        await page.locator(`section.doc[data-label="${label}"] .mermaid-fig svg`).waitFor();
        const before = await figureSnapshot(page, label);
        await addNote(page, label, needle, '图上的意见');
        const after = await figureSnapshot(page, label);
        assert.deepEqual(after, before);
        assert.equal(await page.locator('mark.sdflow-hl').count(), 0);
        const item = page.locator('#sdflow-notes .note-item');
        assert.equal(await item.count(), 1);
        assert.match(await item.locator('.note-badge').textContent(), /^未在正文高亮$/);

        // 刷新：mermaid 重新渲染，意见仍是「未在正文高亮」，不是「原文已对不上」
        await page.reload();
        await page.locator(`section.doc[data-label="${label}"] .mermaid-fig svg`).waitFor();
        assert.deepEqual(await figureSnapshot(page, label), before);
        const item2 = page.locator('#sdflow-notes .note-item');
        assert.match(await item2.locator('.note-badge').textContent(), /^未在正文高亮$/);
        assert.equal(await page.locator('mark.sdflow-hl').count(), 0);

        // 定位：滚到所在文档并提示
        await page.evaluate(() => window.scrollTo(0, 0));
        await item2.locator('.sdflow-btn', { hasText: '定位' }).click();
        assert.equal(await page.locator('#sdflow-jump-hint').textContent(), '未在正文高亮');
        assert.equal(await page.locator('#sdflow-jump-hint').getAttribute('role'), 'status');
        await page.waitForFunction((lab) => {
          const r = document.querySelector(`section.doc[data-label="${lab}"]`).getBoundingClientRect();
          return r.top < window.innerHeight && r.bottom > 0;
        }, label);
        assert.deepEqual(errors, []);
      });
      } finally { if (r) rm(r); }
    });
  }

  test('图内划选的意见（inFigure）刷新后原文找不到时仍标「未在正文高亮」', async () => {
    await withPage({}, async ({ page }) => {
      await seedNotes(page, [
        { id: '0123456789abcdef', n: 1, doc: '图', heading: '', quote: '渲染后才有的文字', before: '', after: '', comment: '图上', copied: false, inFigure: true },
      ]);
      await page.reload();
      assert.match(await page.locator('#sdflow-notes .note-item .note-badge').textContent(), /^未在正文高亮$/);
    });
  });

  test('图内划选的暂存意见（inFigure）原文与正文某处相同：刷新后不高亮到正文（RVP-13）', async () => {
    await withPage({}, async ({ page }) => {
      // 「alpha beta」在设计文档正文里只出现一次：不短路的话第三级「原文全篇唯一」会把它高亮到正文
      await seedNotes(page, [
        { id: '0123456789abcdef', n: 1, doc: '设计', heading: '', quote: 'alpha beta', before: '', after: '', comment: '图上', copied: false, inFigure: true },
      ]);
      await page.reload();
      assert.equal(await page.locator('mark.sdflow-hl').count(), 0);
      assert.equal(await page.locator('#sdflow-notes .note-item .note-badge').textContent(), '未在正文高亮');
    });
  });

  test('原文只能在 mermaid 源码块内找到：不在源码里包 <mark>，标「未在正文高亮」', async () => {
    await withPage({ mermaid: 'abort' }, async ({ page }) => {
      await seedNotes(page, [
        { id: '0123456789abcdef', n: 1, doc: '图', heading: '', quote: 'A[开始]', before: '', after: '', comment: '源码里', copied: false },
      ]);
      await page.reload();
      assert.equal(await page.locator('pre > code.language-mermaid mark').count(), 0);
      assert.match(await page.locator('#sdflow-notes .note-item .note-badge').textContent(), /^未在正文高亮$/);
    });
  });
});

// ── 暂存意见的状态机：出现多处无法区分 → unmarked，不是 orphan ────────────────
describe('暂存意见状态机', () => {
  test('原文在正文出现多次且前后文无法区分：标「未在正文高亮」，不标「原文已对不上」', async () => {
    await withPage({}, async ({ page }) => {
      await seedNotes(page, [
        { id: '0123456789abcdef', n: 1, doc: '设计', heading: '', quote: '重名节', before: 'zz', after: 'yy', comment: '多处', copied: false },
      ]);
      await page.reload();
      const item = page.locator('#sdflow-notes .note-item');
      assert.match(await item.locator('.note-badge').textContent(), /^未在正文高亮$/);
      assert.equal(await page.locator('mark.sdflow-hl').count(), 0);
      assert.equal(await item.locator('.sdflow-btn', { hasText: '定位' }).count(), 1);
    });
  });

  test('原文完全找不到仍标「原文已对不上，仅列出」且没有「定位」', async () => {
    await withPage({}, async ({ page }) => {
      await seedNotes(page, [
        { id: '0123456789abcdef', n: 1, doc: '设计', heading: '', quote: '这段话原文里没有', before: '', after: '', comment: '孤儿', copied: false },
      ]);
      await page.reload();
      const item = page.locator('#sdflow-notes .note-item');
      assert.match(await item.locator('.note-badge').textContent(), /原文已对不上，仅列出/);
      assert.equal(await item.locator('.sdflow-btn', { hasText: '定位' }).count(), 0);
    });
  });
});

// ── 4.7 空意见错误的读屏语义 ────────────────────────────────────────────────
describe('空意见错误的 aria 语义', () => {
  test('错误写入 role=status 节点，输入框 aria-describedby 指向它并标 aria-invalid；输入后清除', async () => {
    await withPage({}, async ({ page }) => {
      await selectText(page, '设计', 'alpha beta');
      await page.locator('#sdflow-annotate').click();
      const err = page.locator('#sdflow-note-error');
      const text = page.locator('#sdflow-note-text');
      assert.equal(await err.getAttribute('role'), 'status');
      assert.equal(await err.textContent(), '');
      assert.equal(await text.getAttribute('aria-invalid'), null);

      await page.locator('#sdflow-note-dialog .sdflow-btn.primary').click();
      assert.equal(await err.textContent(), '意见不能为空');
      assert.equal(await text.getAttribute('aria-invalid'), 'true');
      assert.equal(await text.getAttribute('aria-describedby'), 'sdflow-note-error');
      // 按钮提示行保持原样
      assert.equal(await page.locator('#sdflow-note-dialog .dlg-hint').textContent(), 'Ctrl/⌘ + Enter 保存，Esc 取消');

      await text.pressSequentially('写');
      assert.equal(await err.textContent(), '');
      assert.equal(await text.getAttribute('aria-invalid'), null);
    });
  });

  test('取消后重新打开对话框：错误与无效标记已清除', async () => {
    await withPage({}, async ({ page }) => {
      await selectText(page, '设计', 'alpha beta');
      await page.locator('#sdflow-annotate').click();
      await page.locator('#sdflow-note-dialog .sdflow-btn.primary').click();
      await page.keyboard.press('Escape');
      await page.locator('#sdflow-annotate').click();
      assert.equal(await page.locator('#sdflow-note-error').textContent(), '');
      assert.equal(await page.locator('#sdflow-note-text').getAttribute('aria-invalid'), null);
    });
  });
});

// ── 3.1 跨节点划选：按文本节点分段高亮（RVP-20）────────────────────────────────
const RICH_DOCS = [
  ['富文本', 'rich.md', [
    '# 富文本',
    '',
    '普通甲 **粗体乙** 普通丙。',
    '',
    '- 列表项一文字',
    '- 列表项二文字',
    '',
    '末段结尾。',
    '',
  ].join('\n')],
];

describe('跨节点划选高亮（RVP-20）', () => {
  const docBodyText = (page, label) =>
    page.evaluate((lab) => document.querySelector(`section.doc[data-label="${lab}"] .doc-body`).textContent, label);

  test('跨粗体：三段文字都高亮，意见不标「未在正文高亮」', async () => {
    await withRepo(() => makeRepo(RICH_DOCS), async (r) => {
      await withPage({ url: r.url }, async ({ page, errors }) => {
        await addNoteAcross(page, '富文本', '普通甲', '普通丙', '跨粗体');
        const id = await page.locator('#sdflow-notes .note-item').getAttribute('data-note');
        assert.deepEqual(await stagedMarks(page), { [id]: ['普通甲 ', '粗体乙', ' 普通丙'] });
        assert.equal(await page.locator('#sdflow-notes .note-item .note-badge').count(), 0);
        // 刷新后同样恢复三段
        await page.reload();
        assert.deepEqual(await stagedMarks(page), { [id]: ['普通甲 ', '粗体乙', ' 普通丙'] });
        assert.deepEqual(errors, []);
      });
    });
  });

  test('跨列表项落盘后重新生成：两个列表项都以已落盘样式高亮，「定位」跳到第一段，闪烁全部分段，段间无竖线', async () => {
    await withRepo(() => makeRepo(RICH_DOCS), async (r) => {
      const a = await openPage({ url: r.url, initScripts: [clipboardStub('ok')] });
      try {
        await addNoteAcross(a.page, '富文本', '列表项一', '列表项二文字', '跨列表项');
        appendPasted(r, await copyOnce(a.page));
      } finally { await a.close(); }
      renderPage(r.root, RICH_DOCS);
      await withPage({ url: r.url }, async ({ page, errors }) => {
        const item = savedItems(page);
        assert.equal(await item.count(), 1);
        const sid = await item.getAttribute('data-saved');
        assert.deepEqual(await savedMarksOf(page), { [sid]: ['列表项一文字', '列表项二文字'] });
        assert.equal(await item.locator('.note-badge').count(), 0);
        // 按段绘制：首段无右边框、末段无左边框，上下边框仍是虚线
        const edges = await page.locator('mark.sdflow-saved-hl').evaluateAll((els) => els.map((m) => {
          const cs = getComputedStyle(m);
          return { l: cs.borderLeftWidth, r: cs.borderRightWidth, t: cs.borderTopStyle };
        }));
        assert.deepEqual(edges, [{ l: '2px', r: '0px', t: 'dashed' }, { l: '0px', r: '2px', t: 'dashed' }]);
        // 定位：滚到第一段，闪烁全部分段
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        await item.locator('.sdflow-btn', { hasText: '定位' }).click();
        assert.equal(await page.locator('mark.sdflow-saved-hl.flash').count(), 2);
        // 页面是平滑滚动：等第一段进入视口（页尾两节让页面够长，滚动确实发生）
        await page.waitForFunction(() => {
          const b = document.querySelector('mark.sdflow-saved-hl').getBoundingClientRect();
          return b.top >= 0 && b.bottom <= window.innerHeight;
        });
        assert.deepEqual(errors, []);
      });
    });
  });

  test('删除跨三段高亮的暂存意见：三段全部移除，正文文字不变', async () => {
    await withRepo(() => makeRepo(RICH_DOCS), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        const before = await docBodyText(page, '富文本');
        await addNoteAcross(page, '富文本', '普通甲', '普通丙', '要删的');
        assert.equal(await page.locator('mark.sdflow-hl').count(), 3);
        assert.equal(await docBodyText(page, '富文本'), before);
        await page.locator('#sdflow-notes .del-btn').click();
        assert.equal(await page.locator('mark').count(), 0);
        assert.equal(await docBodyText(page, '富文本'), before);
      });
    });
  });

  test('端点落在元素上（三击选段，终点在下一个块元素偏移 0）：该段高亮，不标「未在正文高亮」', async () => {
    await withPage({}, async ({ page }) => {
      await page.locator('section.doc[data-label="设计"] .doc-body p', { hasText: '第一处正文' }).click({ clickCount: 3 });
      await page.locator('#sdflow-annotate').waitFor({ state: 'visible' });
      // 前置：终点确实落在元素上（不是文本节点），否则这条用例没测到目标场景
      assert.equal(await page.evaluate(() => window.getSelection().getRangeAt(0).endContainer.nodeType), 1);
      await saveNote(page, '三击选段');
      const id = await page.locator('#sdflow-notes .note-item').getAttribute('data-note');
      assert.deepEqual(await stagedMarks(page), { [id]: ['第一处正文 alpha beta gamma delta epsilon。'] });
      assert.equal(await page.locator('#sdflow-notes .note-item .note-badge').count(), 0);
    });
  });

  test('文档最后一段三击：选区终点落在正文之外，仍出现「写意见」，该段高亮，不标「未在正文高亮」', async () => {
    await withRepo(() => makeRepo(RICH_DOCS), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        await page.locator('section.doc[data-label="富文本"] .doc-body p', { hasText: '末段结尾' }).click({ clickCount: 3 });
        // 前置：终点确实落在该文档正文之外，否则没测到目标场景
        assert.equal(await page.evaluate(() => {
          const r = window.getSelection().getRangeAt(0);
          const el = r.endContainer.nodeType === 1 ? r.endContainer : r.endContainer.parentElement;
          return !!el.closest('.doc-body');
        }), false);
        await page.locator('#sdflow-annotate').waitFor({ state: 'visible' });
        await saveNote(page, '末段三击');
        const id = await page.locator('#sdflow-notes .note-item').getAttribute('data-note');
        assert.deepEqual(await stagedMarks(page), { [id]: ['末段结尾。'] });
        assert.equal(await page.locator('#sdflow-notes .note-item .note-badge').count(), 0);
      });
    });
  });

  // 终点落在正文之外、且不是三击末段形态时，划选必须被拒绝（不出现「写意见」）。
  // 起点取 fromLabel 正文里 needle 的开头，终点取 endSelector 元素首个文本节点的偏移 2（标题文字中间）。
  for (const c of [
    { name: '从文档 A 正文拖到文档 B 标题', from: '设计', needle: '第一处正文', end: 'section.doc[data-label="另一份"] > :first-child' },
    { name: '从最后一份文档正文拖到页尾「修改日志」节', from: '锚点', needle: '数据模型正文', end: '#review-revisions h2' },
  ]) {
    test(`拖选越界：${c.name}，不产生划选`, async () => {
      await withPage({}, async ({ page }) => {
        await page.evaluate(({ from, needle, end }) => {
          const body = document.querySelector(`section.doc[data-label="${from}"] .doc-body`);
          const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
          let node;
          while ((node = walker.nextNode()) && node.data.indexOf(needle) < 0);
          if (!node) throw new Error('找不到起点文字：' + needle);
          const tw = document.createTreeWalker(document.querySelector(end), NodeFilter.SHOW_TEXT);
          const endNode = tw.nextNode();
          window.getSelection().setBaseAndExtent(node, node.data.indexOf(needle), endNode, 2);
        }, { from: c.from, needle: c.needle, end: c.end });
        // selectionchange 异步触发；等一拍再断言按钮没出现
        await page.evaluate(() => new Promise((resolve) => setTimeout(resolve, 150)));
        assert.equal(await page.locator('#sdflow-annotate').isHidden(), true);
        assert.equal(await page.locator('#sdflow-notes .note-item').count(), 0);
      });
    });
  }

  test('超过 500 码点的跨段选区：保存时与落盘重新生成后高亮的文字相同', async () => {
    await withRepo(() => makeRepo(), async (r) => {
      let staged;
      const a = await openPage({ url: r.url, initScripts: [clipboardStub('ok')] });
      try {
        await addNoteAcross(a.page, '设计', '填充段落第 1 行', '填充段落第 40 行', '超长');
        const id = await a.page.locator('#sdflow-notes .note-item').getAttribute('data-note');
        staged = (await stagedMarks(a.page))[id];
        assert.ok(staged.length > 3, '应跨多段');
        // 引用被截断到 500 码点：高亮文字总长 = 引用去掉段间换行后的长度，且没有铺到第 40 行
        const quote = await a.page.locator('#sdflow-notes .note-quote').textContent();
        assert.equal(Array.from(quote).length, 500);
        assert.equal(staged.join(''), quote.replace(/\n/g, ''));
        assert.ok(!staged.join('').includes('第 40 行'));
        // 刷新后暂存意见仍只高亮截断后的范围
        await a.page.reload();
        assert.deepEqual((await stagedMarks(a.page))[id], staged);
        appendPasted(r, await copyOnce(a.page));
      } finally { await a.close(); }
      renderPage(r.root);
      await withPage({ url: r.url }, async ({ page }) => {
        const saved = Object.values(await savedMarksOf(page));
        assert.equal(saved.length, 1);
        assert.deepEqual(saved[0], staged);
        assert.equal(await savedItems(page).locator('.note-badge').count(), 0);
      });
    });
  });
});

// ── 3.2 frontmatter 显示为元数据框（RVP-21）──────────────────────────────────
describe('frontmatter 元数据框（RVP-21）', () => {
  const SHA = 'b'.repeat(64);
  const GATE = ['ship-gate:', 'design_approved: true', `reviewed_sha: ${SHA}`];
  const tocText = (page) => page.locator('#toc').textContent();
  const metaBox = (page) => page.locator('section.doc[data-label="报告"] > details.doc-meta');

  function repoWith(text) {
    return makeRepo([['报告', 'report.md', text]]);
  }

  test('批准锚不进目录：「元数据」框含三行原文，在 .doc-body 之外，默认折叠，正文照常渲染', async () => {
    await withRepo(() => repoWith(['---', ...GATE, '---', '# 评审报告', '', '## 结论', '', '正文一句。', ''].join('\n')), async (r) => {
      await withPage({ url: r.url }, async ({ page, errors }) => {
        const toc = await tocText(page);
        assert.ok(!toc.includes('ship-gate'));
        assert.ok(!toc.includes(SHA));
        assert.match(toc, /评审报告/);
        const box = metaBox(page);
        assert.equal(await box.count(), 1);
        assert.equal(await box.locator('summary').textContent(), '元数据');
        assert.equal(await box.evaluate((el) => el.open), false);
        assert.equal(await box.locator('pre').textContent(), GATE.join('\n'));
        // 元数据框在文档标题区之后、.doc-body 之外；正文里没有 ship-gate
        assert.equal(await page.locator('section.doc[data-label="报告"] .doc-body details').count(), 0);
        assert.ok(!(await page.locator('section.doc[data-label="报告"] .doc-body').textContent()).includes('ship-gate'));
        assert.equal(await page.locator('section.doc[data-label="报告"] .doc-body h1').textContent(), '评审报告');
        assert.deepEqual(errors, []);
      });
    });
  });

  test('元数据框内的文字不能划选写意见', async () => {
    await withRepo(() => repoWith(['---', ...GATE, '---', '# 评审报告', '', '正文。', ''].join('\n')), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        await metaBox(page).locator('summary').click();
        await page.evaluate(() => {
          const pre = document.querySelector('details.doc-meta pre');
          const range = document.createRange();
          range.selectNodeContents(pre);
          const sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(range);
        });
        await page.waitForTimeout(150);
        assert.equal(await page.locator('#sdflow-annotate').isHidden(), true);
      });
    });
  });

  test('没有闭合行：整篇按原文渲染，不显示「元数据」框', async () => {
    await withRepo(() => repoWith(['---', 'ship-gate:', 'design_approved: true', '', '# 评审报告', '', '正文。', ''].join('\n')), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        assert.equal(await metaBox(page).count(), 0);
        assert.match(await page.locator('section.doc[data-label="报告"] .doc-body').textContent(), /design_approved: true/);
      });
    });
  });

  test('带 BOM、CRLF 换行的批准锚：目录不含 ship-gate，「元数据」框显示该块', async () => {
    await withRepo(() => repoWith('\uFEFF' + ['---', ...GATE, '---', '# 评审报告', '', '正文。', ''].join('\r\n')), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        assert.ok(!(await tocText(page)).includes('ship-gate'));
        assert.equal(await metaBox(page).locator('pre').textContent(), GATE.join('\n'));
        assert.equal(await page.locator('section.doc[data-label="报告"] .doc-body h1').textContent(), '评审报告');
      });
    });
  });

  test('以分隔线开头的正文（第二行是普通段落）：整篇按原文渲染，不显示「元数据」框', async () => {
    await withRepo(() => repoWith(['---', '这是普通段落文字', '', '---', '后文。', ''].join('\n')), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        assert.equal(await metaBox(page).count(), 0);
        const body = page.locator('section.doc[data-label="报告"] .doc-body');
        assert.match(await body.textContent(), /这是普通段落文字/);
        assert.ok((await body.locator('hr').count()) >= 1);
      });
    });
  });

  test('元数据按纯文本显示：含 <img onerror> 时不执行', async () => {
    await withRepo(() => repoWith(['---', 'title: <img src=x onerror="window.__pwn=7">', '---', '# 报告', ''].join('\n')), async (r) => {
      await withPage({ url: r.url }, async ({ page, dialogs }) => {
        assert.equal(await metaBox(page).locator('img').count(), 0);
        assert.match(await metaBox(page).locator('pre').textContent(), /<img src=x onerror=/);
        await expectNoScriptRan(page, dialogs);
      });
    });
  });
});

// ── 3.3 页头版本、意见栏处理标记、数据块损坏（RVP-22 / RVP-25）────────────────────
const RECORD_SCRIPT = path.resolve(__dirname, '..', '..', 'assets', 'hack', 'record-review-disposition.py');
const ID_B = 'bbbbbbbbbbbbbbbb';
const ID_C = 'cccccccccccccccc';

// 用处置记录脚本把处置追加进 review-notes.md（与真实流程同一入口），再重新生成页面。
function recordDispositions(r, items) {
  const rel = path.relative(r.root, r.notesFile).split(path.sep).join('/');
  const payload = rel + '\n' + JSON.stringify({ page: 'page.html', dispositions: items });
  execFileSync(PYTHON, [RECORD_SCRIPT, '--stdin'], { cwd: r.root, input: payload, encoding: 'utf-8' });
  renderPage(r.root);
}

// 三条已落盘意见：A（alpha beta）、B（zeta eta）、C（iota kappa）。
function makeRepoWithThreeNotes() {
  return makeRepoWithNotes([
    { id: SAVED_ID, quote: 'alpha beta', comment: '意见甲' },
    { id: ID_B, quote: 'zeta eta', comment: '意见乙' },
    { id: ID_C, quote: 'iota kappa', comment: '意见丙' },
  ]);
}

const records = (page) => page.locator('#review-records');
const revisions = (page) => page.locator('#review-revisions');

// 三条意见 + 两条处置：修改日志共三版（首次生成、写入意见后重新生成、记处置后重新生成）。
function makeRecordedRepo() {
  const r = makeRepoWithThreeNotes();
  recordDispositions(r, [
    { id: SAVED_ID, action: '采纳', detail: '已改 design' },
    { id: ID_B, action: '转 issue', detail: '另起一张', issue: 'T410' },
  ]);
  return r;
}

// 把页面里某个 JSON 数据块换成给定文本。
function replaceDataBlock(url, id, text) {
  const file = new URL(url);
  const html = fs.readFileSync(file, 'utf-8');
  const re = new RegExp('(<script type="application/json" id="' + id + '">)[\\s\\S]*?(</script>)');
  const out = html.replace(re, (m, a, b) => a + text + b);
  assert.notEqual(out, html);
  fs.writeFileSync(file, out, 'utf-8');
}

describe('页头版本与意见栏处理标记（RVP-22 / RVP-25）', () => {
  const headerOf = (page) => page.locator('#sdflow-gen-meta');

  test('页头显示「生成于 X · 第 N 版」：指定 epoch 的首版', async () => {
    await withPage({}, async ({ page }) => {
      assert.equal(await headerOf(page).textContent(), '生成于 2023-11-14T22:13:20+00:00 · 第 1 版');
      // 页头在标题之后、第一份文档之前
      assert.equal(await page.evaluate(() => {
        const h = document.getElementById('sdflow-gen-meta');
        return h.previousElementSibling.className + '|' + h.nextElementSibling.id;
      }), 'page-title|docs');
    });
  });

  test('文档改动后重新生成：第 2 版', async () => {
    await withRepo(() => makeRepo(), async (r) => {
      fs.appendFileSync(path.join(r.changeDir, 'other.md'), '\n新增一段。\n', 'utf-8');
      renderPage(r.root);
      await withPage({ url: r.url }, async ({ page }) => {
        assert.match(await headerOf(page).textContent(), / · 第 2 版$/);
      });
    });
  });

  test('已落盘意见显示处理类别、编号与说明；无处置显示「未记录处理」', async () => {
    await withRepo(() => makeRepoWithThreeNotes(), async (r) => {
      recordDispositions(r, [
        { id: SAVED_ID, action: '采纳', detail: '已改 design' },
        { id: ID_B, action: '转 issue', detail: '另起一张', issue: 'T410' },
      ]);
      await withPage({ url: r.url }, async ({ page, errors }) => {
        const lines = await savedItems(page).locator('.note-disposition').allTextContents();
        assert.deepEqual(lines, ['处理：采纳：已改 design', '处理：转 issue T410：另起一张', '处理：未记录处理']);
        assert.deepEqual(errors, []);
      });
    });
  });

  test('处置说明含 <img onerror>：意见栏与处理记录里都只作文字显示，不执行', async () => {
    const payload = '<img src=x onerror="window.__pwn=8">';
    await withRepo(() => makeRepoWithThreeNotes(), async (r) => {
      recordDispositions(r, [{ id: SAVED_ID, action: '不采纳', detail: payload }]);
      await withPage({ url: r.url }, async ({ page, dialogs }) => {
        const where = [
          { name: '意见栏', line: savedItems(page).first().locator('.note-disposition'), root: page.locator('#sdflow-notes') },
          { name: '处理记录', line: records(page).locator('.note-disposition').first(), root: records(page) },
        ];
        for (const w of where) {
          assert.equal(await w.line.textContent(), '处理：不采纳：' + payload, w.name);
          assert.equal(await w.root.locator('img').count(), 0, w.name);
        }
        await expectNoScriptRan(page, dialogs);
      });
    });
  });

  test('后记的处置覆盖先记的：意见栏只显示「采纳」', async () => {
    await withRepo(() => makeRepoWithThreeNotes(), async (r) => {
      recordDispositions(r, [{ id: SAVED_ID, action: '不采纳', detail: '先不改' }]);
      recordDispositions(r, [{ id: SAVED_ID, action: '采纳', detail: '想通了' }]);
      await withPage({ url: r.url }, async ({ page }) => {
        assert.equal(await savedItems(page).first().locator('.note-disposition').textContent(), '处理：采纳：想通了');
      });
    });
  });
});

// ── 3.4 页尾两节：意见与处理记录、修改日志（RVP-23 / RVP-25）───────────────────────
describe('页尾「意见与处理记录」「修改日志」（RVP-23 / RVP-25）', () => {
  test('两节在全部文档之后、先记录后日志；目录最后两项指向它们；两节不是 section.doc', async () => {
    await withRepo(() => makeRecordedRepo(), async (r) => {
      await withPage({ url: r.url }, async ({ page, errors }) => {
        const order = await page.evaluate(() => Array.from(document.getElementById('main').children).map((el) => el.id || el.tagName));
        assert.deepEqual(order.slice(-3), ['docs', 'review-records', 'review-revisions']);
        assert.equal(await page.locator('section.doc').count(), DOCS.length);
        assert.equal(await page.locator('#review-records.doc, #review-revisions.doc, #review-records .doc-body, #review-revisions .doc-body').count(), 0);
        const links = await page.locator('#toc > ul > li > a.doc-link').evaluateAll((els) => els.map((a) => [a.textContent, a.getAttribute('href')]));
        assert.deepEqual(links.slice(-2), [['意见与处理记录', '#review-records'], ['修改日志', '#review-revisions']]);
        assert.equal(links.length, DOCS.length + 2);
        // 点目录项滚到对应节
        await page.locator('#toc a[href="#review-revisions"]').click();
        await page.waitForFunction(() => {
          const b = document.getElementById('review-revisions').getBoundingClientRect();
          return b.top < window.innerHeight && b.bottom > 0;
        });
        assert.deepEqual(errors, []);
      });
    });
  });

  test('意见与处理记录：按文档分组列出全部已落盘意见，各显示文档、引用、意见、处理类别与说明；无处置显示「未记录处理」', async () => {
    await withRepo(() => makeRecordedRepo(), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        assert.equal(await records(page).locator('h2').textContent(), '意见与处理记录');
        assert.deepEqual(await records(page).locator('h3').allTextContents(), ['设计']);
        const items = records(page).locator('.note-item');
        assert.equal(await items.count(), 3);
        assert.deepEqual(await items.locator('.note-quote').allTextContents(), ['alpha beta', 'zeta eta', 'iota kappa']);
        assert.deepEqual(await items.locator('.note-comment').allTextContents(), ['意见甲', '意见乙', '意见丙']);
        assert.deepEqual(await items.locator('.note-disposition').allTextContents(),
          ['处理：采纳：已改 design', '处理：转 issue T410：另起一张', '处理：未记录处理']);
        assert.match(await items.first().locator('.note-head').textContent(), /^设计.*design\.md:\d+.* › 重名节$/);
      });
    });
  });

  test('没有已落盘意见时显示「暂无已落盘意见」', async () => {
    await withPage({}, async ({ page }) => {
      assert.equal(await records(page).locator('.note-item').count(), 0);
      assert.match(await records(page).textContent(), /暂无已落盘意见/);
    });
  });

  test('修改日志：倒序列出每版的版本号、时间、事件、变化的文档、意见数与处置数', async () => {
    await withRepo(() => makeRecordedRepo(), async (r) => {
      // 第 4 版：改一份文档（「另一份」）
      fs.appendFileSync(path.join(r.changeDir, 'other.md'), '\n新增一段。\n', 'utf-8');
      renderPage(r.root);
      await withPage({ url: r.url }, async ({ page }) => {
        assert.equal(await revisions(page).locator('h2').textContent(), '修改日志');
        const items = revisions(page).locator('li.rev-item');
        assert.equal(await items.count(), 4);
        const at = '2023-11-14T22:13:20+00:00';
        assert.deepEqual(await items.nth(0).locator('div').allTextContents(),
          [`第 4 版 · ${at} · 重新生成`, '变化的文档：另一份', '意见 3 条 · 处置 2 条']);
        assert.deepEqual(await items.nth(1).locator('div').allTextContents(),
          [`第 3 版 · ${at} · 重新生成`, '变化的文档：无', '意见 3 条 · 处置 2 条']);
        assert.deepEqual(await items.nth(2).locator('div').allTextContents(),
          [`第 2 版 · ${at} · 重新生成`, '变化的文档：无', '意见 3 条 · 处置 0 条']);
        assert.deepEqual(await items.nth(3).locator('div').allTextContents(),
          [`第 1 版 · ${at} · 首次生成`, '变化的文档：无', '意见 0 条 · 处置 0 条']);
      });
    });
  });

  test('两节内的文字不能划选写意见', async () => {
    await withRepo(() => makeRecordedRepo(), async (r) => {
      await withPage({ url: r.url }, async ({ page }) => {
        for (const sel of ['#review-records .note-comment', '#review-revisions .rev-item']) {
          await page.evaluate((s) => {
            const range = document.createRange();
            range.selectNodeContents(document.querySelector(s));
            const win = window.getSelection();
            win.removeAllRanges();
            win.addRange(range);
          }, sel);
          await page.waitForTimeout(150);
          assert.equal(await page.locator('#sdflow-annotate').isHidden(), true, sel);
        }
      });
    });
  });

  test('已采纳意见的原文在重新生成前被改掉：意见栏标「原文已变」，处理记录仍显示「采纳」', async () => {
    await withRepo(() => makeRepoWithThreeNotes(), async (r) => {
      recordDispositions(r, [{ id: SAVED_ID, action: '采纳', detail: '已改 design' }]);
      const designFile = path.join(r.changeDir, 'design.md');
      fs.writeFileSync(designFile, fs.readFileSync(designFile, 'utf-8').replace('alpha beta', 'ALPHA-REWRITTEN'), 'utf-8');
      renderPage(r.root);
      await withPage({ url: r.url }, async ({ page }) => {
        assert.match(await savedItems(page).first().locator('.note-badge').textContent(), /^原文已变$/);
        const first = records(page).locator('.note-item').first();
        assert.equal(await first.locator('.note-quote').textContent(), 'alpha beta');
        assert.equal(await first.locator('.note-disposition').textContent(), '处理：采纳：已改 design');
      });
    });
  });

  // 数据块损坏只影响用到它的位置，文档照常渲染。每条用例在同一个页面里同时检查意见栏、页头与页尾两节。
  const BROKEN_BLOCK_CASES = [
    {
      name: '修改日志块损坏：页头与「修改日志」一节显示「无法读取」，意见栏与记录一节照常',
      block: 'sdflow-revisions',
      async check(page) {
        assert.match(await page.locator('#sdflow-gen-meta').textContent(), /无法读取/);
        assert.match(await revisions(page).textContent(), /无法读取/);
        assert.equal(await revisions(page).locator('li').count(), 0);
        assert.equal(await savedItems(page).count(), 3);
        assert.equal(await records(page).locator('.note-item').count(), 3);
      },
    },
    {
      name: '处置块损坏：意见栏与记录一节仍列出全部意见，处理一栏显示「无法读取」，页头与修改日志不受影响',
      block: 'sdflow-dispositions',
      async check(page) {
        const broken = ['处理：无法读取', '处理：无法读取', '处理：无法读取'];
        assert.deepEqual(await savedItems(page).locator('.note-disposition').allTextContents(), broken);
        assert.deepEqual(await records(page).locator('.note-disposition').allTextContents(), broken);
        assert.equal(await records(page).locator('.note-item').count(), 3);
        // 修改日志块没坏：页头与日志仍按三版显示
        assert.equal(await page.locator('#sdflow-gen-meta').textContent(), '生成于 2023-11-14T22:13:20+00:00 · 第 3 版');
        assert.equal(await revisions(page).locator('li.rev-item').count(), 3);
      },
    },
  ];
  for (const c of BROKEN_BLOCK_CASES) {
    test(c.name, async () => {
      await withRepo(() => makeRecordedRepo(), async (r) => {
        replaceDataBlock(r.url, c.block, '{broken');
        await withPage({ url: r.url }, async ({ page, errors }) => {
          assert.equal(await page.locator('section.doc').count(), DOCS.length);
          await c.check(page);
          assert.deepEqual(errors, []);
        });
      });
    });
  }
});
