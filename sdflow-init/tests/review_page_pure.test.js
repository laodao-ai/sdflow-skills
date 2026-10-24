'use strict';
// 评审页模板里的纯函数单测（add-html-review-and-dispatch-watchdog · tasks 4.4 + Task 3 fold）。
// 纯函数写在 template.html 内联脚本的 PURE-BEGIN / PURE-END 标记之间，这里按标记切出来执行，
// 不另存一份拷贝：测的就是页面里真正运行的那段源码。
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const TEMPLATE = path.resolve(__dirname, '..', 'assets', 'hack', 'review-page', 'template.html');
const NAMES = [
  'squash', 'classifyLink', 'classifyImage',
  'pagePathFromPathname', 'notesPathFromPathname', 'buildCopyText', 'formatLocalTime',
  'truncateQuote', 'locateNote', 'headCodepoints', 'tailCodepoints', 'isNoteId', 'idFromBytes',
  'parseSavedNotes', 'mergeNotes', 'githubSlugs', 'selectionContext', 'splitFrontmatter',
  'parseRevisions', 'parseDispositions', 'headerText', 'dispositionText',
];

function loadPure() {
  const src = fs.readFileSync(TEMPLATE, 'utf8');
  const app = /<script id="sdflow-app">([\s\S]*?)<\/script>/.exec(src);
  assert.ok(app, '模板缺少 sdflow-app 脚本块');
  const m = /\/\/ @@PURE-BEGIN([\s\S]*?)\/\/ @@PURE-END/.exec(app[1]);
  assert.ok(m, '模板缺少 PURE-BEGIN / PURE-END 标记');
  return new Function(m[1] + '\nreturn {' + NAMES.join(',') + '};')();
}

const P = loadPure();

// ── 链接分类（Task 3 fold）──────────────────────────────────────────────────
const DOCS = [
  { label: '提案', path: 'openspec/changes/x/proposal.md' },
  { label: '设计', path: 'openspec/changes/x/design.md' },
  { label: '清单', path: 'openspec/changes/x/specs/a/spec.md' },
];
const HERE = DOCS[0].path;

test('classifyLink: javascript: 降为纯文本', () => {
  assert.equal(P.classifyLink('javascript:alert(1)', DOCS, HERE), null);
});
test('classifyLink: 夹制表符 / 换行 / 空格的 javascript: 同样降级', () => {
  assert.equal(P.classifyLink('java\tscript:alert(1)', DOCS, HERE), null);
  assert.equal(P.classifyLink('java\nscript:alert(1)', DOCS, HERE), null);
  assert.equal(P.classifyLink('  JaVaScRiPt:alert(1)', DOCS, HERE), null);
});
test('classifyLink: 协议相对 //host 与反斜杠形式降级', () => {
  assert.equal(P.classifyLink('//evil.example/x', DOCS, HERE), null);
  assert.equal(P.classifyLink('\\\\evil.example\\x', DOCS, HERE), null);
});
test('classifyLink: data: 链接降级', () => {
  assert.equal(P.classifyLink('data:text/html,<script>alert(1)</script>', DOCS, HERE), null);
});
test('classifyLink: http / https 放行并标外链，mailto 放行不标外链', () => {
  assert.deepEqual(P.classifyLink('https://example.com/a', DOCS, HERE), { href: 'https://example.com/a', external: true });
  assert.deepEqual(P.classifyLink('http://example.com/a', DOCS, HERE), { href: 'http://example.com/a', external: true });
  assert.deepEqual(P.classifyLink('mailto:a@b.c', DOCS, HERE), { href: 'mailto:a@b.c', external: false });
});
// anchors[i]：第 i 份文档的「slug → 标题 id」表（页面在标题 id 分配完后建）。
const ANCHORS = [
  { 'sec': 'd0-1', '数据模型': 'd0-2', 'risks': 'd0-3', 'risks-1': 'd0-4' },
  { 'risks': 'd1-1', 'risks-1': 'd1-2' },
  {},
];
test('classifyLink: 同文档 #片段 命中则改写为标题 id，未命中降为纯文字', () => {
  assert.deepEqual(P.classifyLink('#sec', DOCS, HERE, ANCHORS), { href: '#d0-1', external: false });
  assert.equal(P.classifyLink('#nope', DOCS, HERE, ANCHORS), null);
  assert.equal(P.classifyLink('#', DOCS, HERE, ANCHORS), null);
});
test('classifyLink: 片段先解码（含百分号编码的中文）并转小写再查表', () => {
  assert.deepEqual(P.classifyLink('#%E6%95%B0%E6%8D%AE%E6%A8%A1%E5%9E%8B', DOCS, HERE, ANCHORS), { href: '#d0-2', external: false });
  assert.deepEqual(P.classifyLink('#数据模型', DOCS, HERE, ANCHORS), { href: '#d0-2', external: false });
  assert.deepEqual(P.classifyLink('#SEC', DOCS, HERE, ANCHORS), { href: '#d0-1', external: false });
  // 非法转义：用原串查表，不抛错
  assert.equal(P.classifyLink('#%E0%A4%A', DOCS, HERE, ANCHORS), null);
});
test('classifyLink: 重名标题的后缀 slug 指向第二个同名标题', () => {
  assert.deepEqual(P.classifyLink('#risks', DOCS, HERE, ANCHORS), { href: '#d0-3', external: false });
  assert.deepEqual(P.classifyLink('#risks-1', DOCS, HERE, ANCHORS), { href: '#d0-4', external: false });
});
test('classifyLink: 跨文档 x.md#片段 命中指向该标题，未命中跳到该文档开头', () => {
  assert.deepEqual(P.classifyLink('design.md#risks-1', DOCS, HERE, ANCHORS), { href: '#d1-2', external: false });
  assert.deepEqual(P.classifyLink('design.md#nope', DOCS, HERE, ANCHORS), { href: '#doc-1', external: false });
  assert.deepEqual(P.classifyLink('design.md#', DOCS, HERE, ANCHORS), { href: '#doc-1', external: false });
  assert.equal(P.classifyLink('other.md#risks', DOCS, HERE, ANCHORS), null);
});
test('classifyLink: 没有 slug 表时，依赖该表的链接标为待定，不依赖的照常处理', () => {
  assert.deepEqual(P.classifyLink('#sec', DOCS, HERE), { href: '#sec', external: false, pending: true });
  assert.deepEqual(P.classifyLink('design.md#x', DOCS, HERE), { href: 'design.md#x', external: false, pending: true });
  assert.deepEqual(P.classifyLink('design.md', DOCS, HERE), { href: '#doc-1', external: false });
  assert.equal(P.classifyLink('other.md#x', DOCS, HERE), null);
});

// ── GitHub 标题 slug ────────────────────────────────────────────────────────
test('githubSlugs: 转小写，去标点，空格换连字符，保留中文、数字、连字符、下划线', () => {
  assert.deepEqual(P.githubSlugs(['Hello World', '数据模型与生命周期', 'A & B', 'C++ (v2.0)', 'snake_case-name', 'Ünï']),
    ['hello-world', '数据模型与生命周期', 'a--b', 'c-v20', 'snake_case-name', 'ünï']);
});
test('githubSlugs: 重名依次加 -1、-2', () => {
  assert.deepEqual(P.githubSlugs(['Risks', 'Risks', 'Risks']), ['risks', 'risks-1', 'risks-2']);
  assert.deepEqual(P.githubSlugs(['重名节', '重名节']), ['重名节', '重名节-1']);
});
test('githubSlugs: 字面标题 risks-1 与重名后缀相撞时跳过已占用的 slug', () => {
  assert.deepEqual(P.githubSlugs(['Risks', 'Risks', 'Risks-1']), ['risks', 'risks-1', 'risks-1-1']);
  // 字面 risks-1 先出现：第二个 Risks 不能再用 risks-1
  assert.deepEqual(P.githubSlugs(['Risks-1', 'Risks', 'Risks']), ['risks-1', 'risks', 'risks-2']);
});
test('githubSlugs: 保留组合标记（天城文元音符号、分解写法的分音符），删去 ² 这类其他数字', () => {
  // 期望值由 github-slugger 2.0.0 实算
  assert.deepEqual(P.githubSlugs(['हिन्दी शीर्षक', 'Cafe\u0301 Ne\u0308', 'x² + y²', '①②']),
    ['हिन्दी-शीर्षक', 'cafe\u0301-ne\u0308', 'x--y', '']);
});
test('githubSlugs: 保留字母数字（Ⅻ）、Alphabetic 符号（Ⓐ）与连接标点（‿）', () => {
  assert.deepEqual(P.githubSlugs(['Ⅻ 章', 'Ⓐ 圈字', 'a‿b']), ['ⅻ-章', 'ⓐ-圈字', 'a‿b']);
});
test('githubSlugs: 空标题得到空 slug，不抛错', () => {
  assert.deepEqual(P.githubSlugs(['', '!!!']), ['', '-1']);
});

test('classifyLink: 指向页内文档的相对 .md 链接改为页内锚点', () => {
  assert.deepEqual(P.classifyLink('./design.md', DOCS, HERE), { href: '#doc-1', external: false });
  assert.deepEqual(P.classifyLink('design.md#x', DOCS, HERE, [{}, {}, {}]), { href: '#doc-1', external: false });
  assert.deepEqual(P.classifyLink('specs/a/spec.md', DOCS, HERE), { href: '#doc-2', external: false });
  assert.deepEqual(P.classifyLink('../x/design.md?q=1', DOCS, HERE), { href: '#doc-1', external: false });
});
test('classifyLink: 不在本页的 .md 与其他相对链接降级', () => {
  assert.equal(P.classifyLink('./other.md', DOCS, HERE), null);
  assert.equal(P.classifyLink('./image.png', DOCS, HERE), null);
  assert.equal(P.classifyLink('foo/bar', DOCS, HERE), null);
});
test('classifyLink: 没有当前文档路径时相对链接降级，空链接降级', () => {
  assert.equal(P.classifyLink('./design.md', DOCS, null), null);
  assert.equal(P.classifyLink('', DOCS, HERE), null);
  assert.equal(P.classifyLink(undefined, DOCS, HERE), null);
});

test('classifyImage: 只放行 data:', () => {
  assert.equal(P.classifyImage('data:image/png;base64,AAAA'), 'data:image/png;base64,AAAA');
  assert.equal(P.classifyImage('  DATA:image/png;base64,AAAA'), 'DATA:image/png;base64,AAAA');
  assert.equal(P.classifyImage('https://example.com/a.png'), null);
  assert.equal(P.classifyImage('./a.png'), null);
  assert.equal(P.classifyImage('javascript:alert(1)'), null);
  assert.equal(P.classifyImage(''), null);
});

// ── 落盘路径推导（五种输入 + 解码失败）─────────────────────────────────────────
test('pagePathFromPathname: %20', () => {
  assert.equal(
    P.pagePathFromPathname('/home/u/my%20repo/openspec/changes/x/review/design-gate.html'),
    'openspec/changes/x/review/design-gate.html');
});
test('pagePathFromPathname: 中文目录名（含外层同名 openspec 前的中文）', () => {
  assert.equal(
    P.pagePathFromPathname('/home/u/%E6%88%91%E7%9A%84%20%E4%BB%93/openspec/changes/x/review/design-gate.html'),
    'openspec/changes/x/review/design-gate.html');
  assert.equal(
    P.pagePathFromPathname('/home/u/openspec/%E6%88%91%E7%9A%84%20%E4%BB%93/openspec/changes/x/review/design-gate.html'),
    'openspec/changes/x/review/design-gate.html');
});
test('pagePathFromPathname: /C:/… Windows 路径', () => {
  assert.equal(
    P.pagePathFromPathname('/C:/Users/u/repo/openspec/changes/x/review/design-gate.html'),
    'openspec/changes/x/review/design-gate.html');
  assert.equal(P.pagePathFromPathname('/C:/tmp/page.html'), 'C:/tmp/page.html');
});
test('pagePathFromPathname: 外层目录也叫 openspec 时取最后一个 /openspec/ 段', () => {
  assert.equal(
    P.pagePathFromPathname('/work/openspec/repo/openspec/changes/archive/2026-10-20-x/review/shipped.html'),
    'openspec/changes/archive/2026-10-20-x/review/shipped.html');
});
test('pagePathFromPathname: 无 openspec 段时用解码后的绝对路径', () => {
  assert.equal(P.pagePathFromPathname('/tmp/my%20dir/page.html'), '/tmp/my dir/page.html');
});
test('pagePathFromPathname: 非法转义（URIError）时用原串', () => {
  assert.equal(P.pagePathFromPathname('/tmp/bad%E0%A4%A/openspec/c/review/p.html'), 'openspec/c/review/p.html');
  assert.equal(P.pagePathFromPathname('/tmp/bad%zz/p.html'), '/tmp/bad%zz/p.html');
});
test('notesPathFromPathname: 与页面同目录的 review-notes.md', () => {
  assert.equal(
    P.notesPathFromPathname('/home/u/r/openspec/changes/x/review/design-gate.html'),
    'openspec/changes/x/review/review-notes.md');
  assert.equal(P.notesPathFromPathname('/tmp/my%20dir/page.html'), '/tmp/my dir/review-notes.md');
});
test('notesPathFromPathname: 归档后指向归档目录', () => {
  assert.equal(
    P.notesPathFromPathname('/r/openspec/changes/archive/2026-10-20-x/review/design-gate.html'),
    'openspec/changes/archive/2026-10-20-x/review/review-notes.md');
});

// ── 复制文本 ────────────────────────────────────────────────────────────────
function sample(over) {
  return Object.assign({
    title: '设计门 · x',
    pathname: '/home/u/%E6%88%91%E7%9A%84%20%E4%BB%93/openspec/changes/x/review/design-gate.html',
    copiedAt: '2026-10-20 10:30:05',
    notes: [
      { n: 1, id: '0123456789abcdef', doc: '设计', path: 'openspec/changes/x/design.md', heading: '失败模式',
        quote: '第一行\n第二行', before: '前文甲', after: '后文乙', comment: '这里不对\n# 以井号开头的行\n正常行' },
      { n: 3, id: 'fedcba9876543210', doc: '提案', path: 'openspec/changes/x/proposal.md', heading: '',
        quote: '单行', before: '', after: '', comment: '无上级标题' },
    ],
  }, over || {});
}

test('buildCopyText: 第一行是落盘指示，路径取页面所在目录', () => {
  const text = P.buildCopyText(sample());
  const first = text.split('\n')[0];
  assert.equal(first,
    '请先把下面全文原样追加到 `openspec/changes/x/review/review-notes.md`（不存在则新建），再逐条处理这些意见。');
});
test('buildCopyText: 归档后的页面位置决定落盘路径与 JSON 的 page', () => {
  const text = P.buildCopyText(sample({ pathname: '/r/openspec/changes/archive/2026-10-20-x/review/design-gate.html' }));
  assert.ok(text.split('\n')[0].includes('`openspec/changes/archive/2026-10-20-x/review/review-notes.md`'));
  assert.ok(text.includes('"page":"openspec/changes/archive/2026-10-20-x/review/design-gate.html"'));
});
test('buildCopyText: 标题、页面、复制时间、按序正文', () => {
  const text = P.buildCopyText(sample());
  const lines = text.split('\n');
  assert.ok(lines.includes('# 评审意见 · 设计门 · x'));
  assert.ok(lines.includes('页面：`openspec/changes/x/review/design-gate.html`'));
  assert.ok(lines.includes('复制于：2026-10-20 10:30:05'));
  assert.ok(lines.includes('## 1. 设计（openspec/changes/x/design.md） › 失败模式'));
  assert.ok(lines.includes('## 3. 提案（openspec/changes/x/proposal.md）'));
  assert.ok(text.indexOf('## 1.') < text.indexOf('## 3.'));
});
test('buildCopyText: 引用每行加 "> "，正文 # 行转义', () => {
  const lines = P.buildCopyText(sample()).split('\n');
  assert.ok(lines.includes('> 第一行'));
  assert.ok(lines.includes('> 第二行'));
  assert.ok(lines.includes('\\# 以井号开头的行'));
  assert.ok(!lines.includes('# 以井号开头的行'));
  assert.ok(lines.includes('这里不对'));
});
test('buildCopyText: 末尾 JSON 块可解析且字段齐全', () => {
  const text = P.buildCopyText(sample());
  const m = /\n(`{3,})json\n([\s\S]*)\n\1\n?$/.exec(text);
  assert.ok(m, '末尾应是 ```json 围栏块');
  const data = JSON.parse(m[2]);
  assert.equal(data.page, 'openspec/changes/x/review/design-gate.html');
  assert.equal(data.v, 2);
  assert.equal(data.copied_at, '2026-10-20 10:30:05');
  assert.deepEqual(Object.keys(data), ['v', 'page', 'copied_at', 'notes']);
  assert.deepEqual(data.notes[0], {
    n: 1, id: '0123456789abcdef', doc: '设计', path: 'openspec/changes/x/design.md', heading: '失败模式',
    quote: '第一行\n第二行', before: '前文甲', after: '后文乙', comment: '这里不对\n# 以井号开头的行\n正常行',
    inFigure: false,
  });
  assert.equal(data.notes[1].n, 3);
  assert.equal(data.notes[1].heading, '');
  assert.equal(data.notes[1].id, 'fedcba9876543210');
});
test('buildCopyText: 图内划选的意见在 JSON 块里带 inFigure: true，其余为 false', () => {
  const t = sample();
  t.notes[1] = Object.assign({}, t.notes[1], { inFigure: true });
  const m = /\n(`{3,})json\n([\s\S]*)\n\1\n?$/.exec(P.buildCopyText(t));
  assert.deepEqual(JSON.parse(m[2]).notes.map((n) => n.inFigure), [false, true]);
});
test('buildCopyText: JSON 块整体在一行', () => {
  const text = P.buildCopyText(sample());
  const m = /\n(`{3,})json\n([\s\S]*)\n\1\n?$/.exec(text);
  assert.ok(!m[2].includes('\n'));
  assert.ok(m[2].startsWith('{"v":2,'));
});
test('buildCopyText: JSON 围栏比全文最长反引号串多一个', () => {
  const t = sample({ notes: [{ n: 1, doc: 'd', heading: 'h', quote: '含 ```` 四个反引号', comment: '含 `` 两个' }] });
  const text = P.buildCopyText(t);
  const m = /\n(`{3,})json\n/.exec(text);
  assert.ok(m);
  assert.equal(m[1].length, 5);
  const longest = Math.max(...(text.slice(0, m.index).match(/`+/g) || ['']).map((s) => s.length));
  assert.equal(longest, 4);
});
test('buildCopyText: 没有长反引号串时围栏为三个反引号', () => {
  const text = P.buildCopyText(sample());
  assert.ok(/\n```json\n/.test(text));
});
test('buildCopyText: CRLF 引用按行拆分，不残留 \\r', () => {
  const text = P.buildCopyText(sample({ notes: [{ n: 1, doc: 'd', heading: '', quote: 'a\r\nb', comment: 'c' }] }));
  const body = text.slice(0, text.indexOf('```json'));
  assert.ok(!body.includes('\r'));
  assert.ok(body.split('\n').includes('> b'));
});
test('buildCopyText: 标题与标签里的换行折成空格，不破坏 ## 行', () => {
  const text = P.buildCopyText(sample({ title: 'a\nb', notes: [{ n: 1, id: 'a'.repeat(16), doc: 'x\ny', path: 'p/\nq.md', heading: 'h\n# z', quote: 'q', comment: 'c' }] }));
  const lines = text.split('\n');
  assert.ok(lines.includes('# 评审意见 · a b'));
  assert.ok(lines.includes('## 1. x y（p/ q.md） › h # z'));
});

test('formatLocalTime: 本地时间 YYYY-MM-DD HH:mm:ss', () => {
  assert.equal(P.formatLocalTime(new Date(2026, 9, 5, 3, 4, 5)), '2026-10-05 03:04:05');
});

// ── 选中原文截断与定位 ──────────────────────────────────────────────────────
test('truncateQuote: 500 字内原样，超出截断', () => {
  assert.equal(P.truncateQuote('abc'), 'abc');
  assert.equal(P.truncateQuote('x'.repeat(500)).length, 500);
  assert.equal(P.truncateQuote('x'.repeat(501)).length, 500);
});
test('locateNote: 前后文唯一定位同一句出现多次的原文', () => {
  const hay = '甲甲 重复句 乙乙。丙丙 重复句 丁丁。';
  const note = { quote: '重复句', before: '丙丙 ', after: ' 丁丁。' };
  assert.equal(P.locateNote(hay, note), hay.indexOf('丙丙 重复句') + 3);
});
test('locateNote: 前后文对不上但原文全篇唯一时仍可定位', () => {
  const hay = '改写后的段落里有一句独一无二的话。';
  assert.equal(P.locateNote(hay, { quote: '独一无二的话', before: '旧前文', after: '旧后文' }), hay.indexOf('独一无二的话'));
});
test('locateNote: 对不上且原文出现多次时不定位', () => {
  assert.equal(P.locateNote('重复 重复', { quote: '重复', before: 'zz', after: 'yy' }), -1);
});
test('locateNote: 原文消失时不定位', () => {
  assert.equal(P.locateNote('完全不同的内容', { quote: '旧原文', before: '', after: '' }), -1);
});
test('locateNote: 前后文都为空且原文出现多次时不定位（不取第一处）', () => {
  assert.equal(P.locateNote('重复 重复', { quote: '重复', before: '', after: '' }), -1);
  // 只有后文：后文对不上就不退回「前文 + 原文」那一级去取第一处
  assert.equal(P.locateNote('重复 重复', { quote: '重复', before: '', after: 'zz' }), -1);
  assert.equal(P.locateNote('重复甲 重复乙', { quote: '重复', before: '', after: '乙' }), 4);
});
test('locateNote: 原文被截断时用前文 + 截断段定位', () => {
  const full = 'A'.repeat(600);
  const hay = '前文X' + full + '后文Y';
  assert.equal(P.locateNote(hay, { quote: full.slice(0, 500), before: '前文X', after: '后文Y' }), 3);
});

test('selectionContext: 选区超过 500 码点时后文紧接截断后的原文，第一级就能定位', () => {
  // 两段前文相同、开头 500 码点相同，只有紧跟截断点之后的文字能区分它们。
  // 后文若取自整个选区之后（「尾」），第一级落空，第二级「前文 + 原文」会落到第一段。
  const lead = 's'.repeat(40);
  const head = '前文' + 'x'.repeat(500);
  const text = lead + head + '甲'.repeat(40) + lead + head + '乙'.repeat(40) + '尾';
  const second = text.lastIndexOf(head);
  const ctx = P.selectionContext(text, second, head.length + 40);
  assert.equal(ctx.quote, head.slice(0, 500));
  assert.equal(ctx.before, 's'.repeat(32));
  assert.equal(ctx.after, 'xx' + '乙'.repeat(30));
  assert.equal(P.locateNote(text, ctx), second);
});
test('selectionContext: 500 码点内原文原样，后文从选区末尾起算', () => {
  const text = '开头 中间这段 结尾的文字';
  const ctx = P.selectionContext(text, 3, 4);
  assert.deepEqual(ctx, { quote: '中间这段', before: '开头 ', after: ' 结尾的文字' });
});

// ── 码点截断 ────────────────────────────────────────────────────────────────
function hasLoneSurrogate(str) {
  return /[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/.test(str);
}
test('truncateQuote: 按码点计 500，emoji 落在边界时整个保留或整个去掉，不留孤立代理项', () => {
  const t = P.truncateQuote('a'.repeat(499) + '😀😀');
  assert.equal(Array.from(t).length, 500);
  assert.equal(t, 'a'.repeat(499) + '😀');
  assert.ok(!hasLoneSurrogate(t));
  assert.equal(Array.from(P.truncateQuote('😀'.repeat(600))).length, 500);
});
test('headCodepoints / tailCodepoints: 输入被切在代理对中间时去掉孤立半边', () => {
  const cutHead = '😀'.slice(1) + 'abc';       // 开头是孤立低位
  assert.equal(P.tailCodepoints(cutHead, 32), 'abc');
  const cutTail = 'abc' + '😀'.slice(0, 1);     // 结尾是孤立高位
  assert.equal(P.headCodepoints(cutTail, 32), 'abc');
  assert.equal(P.tailCodepoints('x😀y', 2), '😀y');
  assert.equal(P.headCodepoints('x😀y', 2), 'x😀');
});

// ── 意见 id ─────────────────────────────────────────────────────────────────
test('isNoteId: 只认 16 位小写十六进制', () => {
  assert.equal(P.isNoteId('0123456789abcdef'), true);
  for (const bad of ['', '0123456789ABCDEF', '0123456789abcde', '0123456789abcdef0', '0123456789abcdeg', null, 5, '0123456789abcdef\n']) {
    assert.equal(P.isNoteId(bad), false, String(bad));
  }
});
test('idFromBytes: 8 字节 → 16 位十六进制，补前导零', () => {
  assert.equal(P.idFromBytes([0, 1, 15, 16, 255, 171, 205, 239]), '00010f10ffabcdef');
});

// ── 已落盘意见解析与合并 ────────────────────────────────────────────────────
test('parseSavedNotes: 合法数组按字段规整，非法 id 当无 id，line 非正整数为 null', () => {
  const r = P.parseSavedNotes(JSON.stringify([
    { id: '0123456789abcdef', n: 2, doc: '设计', path: 'p.md', heading: 'h', quote: 'q', before: 'b', after: 'a', comment: 'c', copied_at: 't', line: 7 },
    { id: 'BAD', quote: 'q2', comment: 'c2', line: 0 },
  ]));
  assert.equal(r.ok, true);
  assert.equal(r.notes.length, 2);
  assert.deepEqual(r.notes[0], { id: '0123456789abcdef', key: '0123456789abcdef', status: null, n: 2, doc: '设计', path: 'p.md', heading: 'h', quote: 'q', before: 'b', after: 'a', comment: 'c', copied_at: 't', line: 7, inFigure: false });
  assert.equal(r.notes[1].id, '');
  assert.equal(r.notes[1].line, null);
});
test('parseSavedNotes: 无 id 的意见用序位作 key（按解析后的位置，跳过的项不占位）', () => {
  const r = P.parseSavedNotes(JSON.stringify([
    { quote: 'q0', comment: 'c0' }, null, { id: '0123456789abcdef', quote: 'q1', comment: 'c1' }, { quote: 'q2', comment: 'c2' },
  ]));
  assert.deepEqual(r.notes.map((n) => n.key), ['idx-0', '0123456789abcdef', 'idx-2']);
});
test('parseSavedNotes: inFigure 只认布尔 true，旧数据没有该字段为 false', () => {
  const r = P.parseSavedNotes(JSON.stringify([
    { quote: 'q', comment: 'c', inFigure: true }, { quote: 'q', comment: 'c', inFigure: 'true' }, { quote: 'q', comment: 'c' },
  ]));
  assert.deepEqual(r.notes.map((n) => n.inFigure), [true, false, false]);
});
test('parseSavedNotes: 非法 JSON、非数组 → ok=false 空列表；缺 quote/comment 的项被丢弃', () => {
  assert.deepEqual(P.parseSavedNotes('{not json'), { ok: false, notes: [] });
  assert.deepEqual(P.parseSavedNotes('{"a":1}'), { ok: false, notes: [] });
  assert.deepEqual(P.parseSavedNotes('[]'), { ok: true, notes: [] });
  assert.equal(P.parseSavedNotes('[{"quote":"q"},null,5]').notes.length, 0);
});

const ID1 = '1111111111111111';
const ID2 = '2222222222222222';
function st(over) { return Object.assign({ id: ID1, n: 1, doc: 'd', quote: 'q', comment: 'c', copied: false }, over); }
function sv(over) { return Object.assign({ id: ID1, doc: 'd', quote: 'q', comment: 'c' }, over); }
function ids(view) { return view.map((v) => v.note.id + (v.modified ? '*' : '')); }

test('mergeNotes: 同 id 且已复制 → 只显示已落盘版', () => {
  assert.deepEqual(P.mergeNotes([st({ copied: true, comment: '另一个' })], [sv()]), []);
});
test('mergeNotes: 同 id 且正文相同（未标已复制）→ 只显示已落盘版', () => {
  assert.deepEqual(P.mergeNotes([st()], [sv()]), []);
});
test('mergeNotes: 同 id、未复制、正文不同 → 两条都显示，暂存版标已修改', () => {
  assert.deepEqual(ids(P.mergeNotes([st({ comment: '改过' })], [sv()])), [ID1 + '*']);
});
test('mergeNotes: id 不同的暂存意见原样保留，顺序不变', () => {
  assert.deepEqual(ids(P.mergeNotes([st(), st({ id: ID2, n: 2 })], [sv({ id: 'f'.repeat(16) })])), [ID1, ID2]);
});
test('mergeNotes: 已落盘无 id → doc+quote+comment 相同的暂存意见视为同一条', () => {
  assert.deepEqual(P.mergeNotes([st()], [sv({ id: '' })]), []);
  assert.deepEqual(ids(P.mergeNotes([st({ comment: '不同' })], [sv({ id: '' })])), [ID1]);
  assert.deepEqual(ids(P.mergeNotes([st({ doc: '别的文档' })], [sv({ id: '' })])), [ID1]);
});
test('mergeNotes: 无已落盘意见时全部原样返回', () => {
  assert.deepEqual(ids(P.mergeNotes([st(), st({ id: ID2 })], [])), [ID1, ID2]);
});

// ── frontmatter 判定（RVP-21）────────────────────────────────────────────────
const SHA = 'a'.repeat(64);
test('splitFrontmatter: 批准锚（ship-gate / design_approved / reviewed_sha）整块进 meta，其余是正文', () => {
  const text = '---\nship-gate:\ndesign_approved: true\nreviewed_sha: ' + SHA + '\n---\n# 标题\n正文\n';
  assert.deepEqual(P.splitFrontmatter(text), {
    meta: 'ship-gate:\ndesign_approved: true\nreviewed_sha: ' + SHA,
    body: '# 标题\n正文\n',
  });
});
test('splitFrontmatter: 没有闭合的 --- 行：整篇按原文', () => {
  const text = '---\nkey: v\n正文\n';
  assert.deepEqual(P.splitFrontmatter(text), { meta: null, body: text });
});
test('splitFrontmatter: BOM + CRLF 的批准锚：去 BOM、忽略行尾 \\r', () => {
  const text = '\uFEFF---\r\nship-gate:\r\ndesign_approved: true\r\n---\r\n# 标题\r\n';
  assert.deepEqual(P.splitFrontmatter(text), { meta: 'ship-gate:\ndesign_approved: true', body: '# 标题\r\n' });
});
test('splitFrontmatter: 以分隔线开头的正文（第二行不是「键:」）：整篇按原文', () => {
  const text = '---\n这是普通段落\n\n---\n后文\n';
  assert.deepEqual(P.splitFrontmatter(text), { meta: null, body: text });
});
test('splitFrontmatter: 第二行以非字母开头、或紧跟闭合行：不算 frontmatter', () => {
  assert.equal(P.splitFrontmatter('---\n123: x\n---\n正文').meta, null);
  assert.equal(P.splitFrontmatter('---\n---\n正文').meta, null);
  assert.equal(P.splitFrontmatter('---\n').meta, null);
});
test('splitFrontmatter: 没有 frontmatter 时也去掉开头的 BOM', () => {
  assert.deepEqual(P.splitFrontmatter('\uFEFF# 标题\n'), { meta: null, body: '# 标题\n' });
});

// ── 修改日志 / 处置数据块解析与显示文字（RVP-22 / RVP-25）──────────────────────
const REV = (over) => Object.assign({ n: 1, at: '2023-11-14T22:13:20+00:00', event: '首次生成', docs: {}, notes: 0, dispositions: 0, changed: ['设计'], fp: 'x' }, over);
test('parseRevisions: 合法日志按原样取出，缺字段补默认值', () => {
  const r = P.parseRevisions(JSON.stringify({ v: 1, page: 'p.html', revisions: [REV({ n: 1 }), REV({ n: 2, event: '重新生成', changed: [], notes: 3, dispositions: 2 })] }));
  assert.equal(r.ok, true);
  assert.equal(r.revisions.length, 2);
  assert.deepEqual(r.revisions[1], { n: 2, at: '2023-11-14T22:13:20+00:00', event: '重新生成', changed: [], notes: 3, dispositions: 2 });
  assert.equal(P.parseRevisions(JSON.stringify({ revisions: [{}] })).revisions[0].event, '');
});
test('parseRevisions: 非法 JSON、顶层不是对象、revisions 不是数组、条目不是对象：ok=false', () => {
  assert.equal(P.parseRevisions('{broken').ok, false);
  assert.equal(P.parseRevisions('[]').ok, false);
  assert.equal(P.parseRevisions('null').ok, false);
  assert.equal(P.parseRevisions('{"revisions":{}}').ok, false);
  assert.equal(P.parseRevisions('{"revisions":[5]}').ok, false);
});
test('headerText: 取最后一条的时间和 n', () => {
  const revs = [REV({ n: 1, at: 'T1' }), REV({ n: 2, at: 'T2' })];
  assert.equal(P.headerText(revs), '生成于 T2 · 第 2 版');
  assert.equal(P.headerText([]), '');
});
test('headerText: 日志条目 n 不连续时，版本号取最后一条的 n，不是条数', () => {
  const revs = [REV({ n: 1, at: 'T1' }), REV({ n: 3, at: 'T3' })];
  assert.equal(P.headerText(revs), '生成于 T3 · 第 3 版');
});
test('parseDispositions: 取 action / detail / issue，坏条目跳过；顶层不是对象则 ok=false', () => {
  const r = P.parseDispositions(JSON.stringify({
    aaaaaaaaaaaaaaaa: { action: '采纳', detail: '已改', issue: '', at: 't' },
    bbbbbbbbbbbbbbbb: { action: '转 issue', detail: '另起', issue: 'T410', at: 't' },
    cccccccccccccccc: 5,
    dddddddddddddddd: { detail: '没有类别' },
  }));
  assert.equal(r.ok, true);
  assert.deepEqual(Object.keys(r.map).sort(), ['aaaaaaaaaaaaaaaa', 'bbbbbbbbbbbbbbbb']);
  assert.deepEqual(r.map.bbbbbbbbbbbbbbbb, { action: '转 issue', detail: '另起', issue: 'T410' });
  assert.deepEqual(P.parseDispositions('{}'), { ok: true, map: Object.create(null) });
  assert.equal(P.parseDispositions('[]').ok, false);
  assert.equal(P.parseDispositions('{x').ok, false);
});
test('parseDispositions: __proto__ 一类的键只是普通键，不污染原型', () => {
  const r = P.parseDispositions('{"__proto__": {"action": "采纳", "detail": "x", "issue": ""}}');
  assert.equal(r.ok, true);
  assert.equal(Object.getPrototypeOf(r.map), null);
  assert.equal(Object.keys(r.map).length, 1);
  assert.equal(({}).action, undefined);
});
test('dispositionText: 类别、编号、说明；无处置显示「未记录处理」', () => {
  assert.equal(P.dispositionText({ action: '采纳', detail: '已改 design', issue: '' }), '采纳：已改 design');
  assert.equal(P.dispositionText({ action: '转 issue', detail: '另起', issue: 'T410' }), '转 issue T410：另起');
  assert.equal(P.dispositionText({ action: '不采纳', detail: '', issue: '' }), '不采纳');
  assert.equal(P.dispositionText(null), '未记录处理');
  assert.equal(P.dispositionText(undefined), '未记录处理');
});
