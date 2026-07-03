# OpenSpec Review HTML Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give any project that runs `opsx-project-init` a zero-build, offline, static HTML tool for browsing/reviewing its `openspec/` markdown tree — one root entry (whole tree) plus auto-generated per-directory entries (roadmaps, changes) that default to that directory's files but can still follow links anywhere.

**Architecture:** A single shared vanilla-JS engine (`tools/engine.js` + `tools/engine.css`, vendoring `marked.js` for offline markdown rendering) is served by `python3 -m http.server` rooted at `openspec/`. Every directory gets a thin HTML shell (`review.html`) generated from one template (`tools/review-stub.html`, `__SCOPE__` placeholder) — the root copy has `__SCOPE__=""`, per-directory copies get their own path. The engine discovers directory contents live by fetching Python's auto-generated directory-index HTML and parsing it — no manifest, no build step, always reflects the current filesystem. Shell-generated links use root-relative paths (`/review.html`, `/tools/engine.js`) so they survive `openspec archive` moving a change 1 level deeper without regeneration. Distribution rides `opsx-project-init`'s existing "single source in `assets/`, `init`/`update` copies it" mechanism; the root entry ships there, the per-directory copies are generated at the moment they're needed — a new script for `opsx-roadmap-planner` (model-invoked, at four-piece-set completion) and a new PostToolUse hook (mirroring `ff0-branch-guard.py`, since `openspec new change <name>` is the one CLI chokepoint all of `/opsx:new`/`/opsx:ff`/`/opsx:propose`/`/opsx:onboard` share and none of those skills live in this repo).

**Tech Stack:** Python 3.9+ (stdlib only — `http.server`, `shutil`, `json`, `re`), vanilla JS (ES2017, no framework, no bundler), vendored `marked.js` (MIT), `pytest` for Python tests, Node's built-in `node:test` for JS pure-function tests, Playwright MCP tools for end-to-end browser verification.

## Global Constraints

- Zero build step for the shipped artifact — every file the browser loads is checked-in source, no compilation/bundling.
- Zero network access required at browse time — `marked.js` is vendored, not loaded from a CDN.
- Any static file server works (tested against `python3 -m http.server`, stdlib, Python 3.9.6) — no custom backend/API.
- Shell-generated links (the "back to root" link, and script/stylesheet references inside every `review.html`) MUST use root-relative paths (`/review.html`, `/tools/engine.js`, `/tools/engine.css`) — NOT directory-depth-relative (`../../...`) — because `openspec archive` moves an active change from `openspec/changes/<name>/` (2 levels under `openspec/`) to `openspec/changes/archive/<name>/` (3 levels), which would break a hardcoded relative path. Verified against the real archived example in the mqtt-console repo (2026-07-01).
- Directory discovery relies on Python's stdlib `http.server` auto-generated directory-index HTML format, verified live (Python 3.9.6, 2026-07-01): `<li><a href="name">name</a></li>` for files, `<li><a href="name/">name/</a></li>` for subdirectories (trailing `/` on both href and text is the only signal distinguishing dirs from files).
- The hook (Task 8) and `init.py`'s copy/install logic (Tasks 6/7) must fail open / fail silent on any missing precondition (project not yet running `opsx-project-init`, command not matching, directory missing) — never raise an uncaught exception that could break the user's actual `openspec` CLI invocation or Bash tool call. `gen_review_stub.py` (Task 9) is the deliberate exception: it's a model-invoked step (not an automatic hook), so it MUST raise `FileNotFoundError` loudly on a missing precondition rather than silently no-op — see Task 9's own rationale for why silent failure there would be worse (a skipped review.html nobody notices).
- Full context and rationale for every decision below (including rejected alternatives) is recorded in `opsx-project-init/memo-review-html-tool.md` — read it before touching any task if something here seems under-justified.

---

## File Structure

```
opsx-project-init/
  assets/
    review-tool/                          [NEW] single source of truth for the review tool
      serve.sh                             → copied to <project>/openspec/serve.sh
      tools/
        engine.js                          → copied to <project>/openspec/tools/engine.js
        engine.css                         → copied to <project>/openspec/tools/engine.css
        review-stub.html                   → copied to <project>/openspec/tools/review-stub.html
                                              (also used as the template to generate the root
                                              openspec/review.html, with __SCOPE__="")
        vendor/
          marked.min.js                    → copied to <project>/openspec/tools/vendor/marked.min.js
          NOTICE.md                        → vendoring provenance (not copied to projects)
    hooks/
      ff0-branch-guard.py                  [EXISTING, untouched]
      change-review-stub.py                [NEW] PostToolUse hook — stubs changes/<name>/review.html
  scripts/
    init.py                                [MODIFY] copy_review_tool() + generalized hook installer
  tests/                                    [NEW dir]
    test_init.py                            [NEW] pytest — copy_review_tool, hook generalization
    engine.test.js                          [NEW] node --test — pure functions in engine.js
    test_change_review_stub_hook.py         [NEW] pytest — subprocess-drives the new hook
  SKILL.md                                  [MODIFY] document new capability

opsx-roadmap-planner/
  scripts/                                  [NEW dir]
    gen_review_stub.py                      [NEW] generates roadmaps/<name>/review.html
  tests/                                    [NEW dir]
    test_gen_review_stub.py                 [NEW] pytest
  SKILL.md                                  [MODIFY] wire the script into 阶段 3 / tasks.md template

CHANGELOG.md                                [MODIFY] new entry
VERSION                                     [MODIFY] 1.7.0 → 1.8.0
```

All paths below are relative to `/Users/cheneyzhao/.skills/laodao-skills/` unless stated otherwise.

---

### Task 1: Pure logic functions in `engine.js` (directory-listing parser, link resolution, backtick auto-link)

**Files:**
- Create: `opsx-project-init/assets/review-tool/tools/engine.js`
- Test: `opsx-project-init/tests/engine.test.js`

**Interfaces:**
- Produces (used by Task 3's DOM glue, appended to the same file): `parseDirectoryListing(html) -> Array<{name: string, href: string, isDir: boolean}>`, `linkifyBacktickPaths(html) -> string`, `resolveLink(href, baseUrl) -> string`, `isMarkdownPath(path) -> boolean`. All exported via a `module.exports` guard so `node --test` can `require()` them; the guard is inert in browsers (`typeof module === 'undefined'`).

- [ ] **Step 1: Write the failing test**

Create `opsx-project-init/tests/engine.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const {
  parseDirectoryListing,
  linkifyBacktickPaths,
  resolveLink,
  isMarkdownPath,
} = require('../assets/review-tool/tools/engine.js');

test('parseDirectoryListing: files and subdirectories', () => {
  const html = `<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Directory listing for /</title>
</head>
<body>
<h1>Directory listing for /</h1>
<hr>
<ul>
<li><a href="adr/">adr/</a></li>
<li><a href="config.yaml">config.yaml</a></li>
<li><a href="CONTEXT.md">CONTEXT.md</a></li>
</ul>
<hr>
</body>
</html>
`;
  const entries = parseDirectoryListing(html);
  assert.deepEqual(entries, [
    { name: 'adr', href: 'adr/', isDir: true },
    { name: 'config.yaml', href: 'config.yaml', isDir: false },
    { name: 'CONTEXT.md', href: 'CONTEXT.md', isDir: false },
  ]);
});

test('parseDirectoryListing: empty directory', () => {
  assert.deepEqual(parseDirectoryListing('<ul>\n</ul>'), []);
});

test('linkifyBacktickPaths: converts rendered <code> spans referencing openspec .md paths', () => {
  const input = 'See <code>openspec/CONTEXT.md</code> for details.';
  const output = linkifyBacktickPaths(input);
  assert.equal(
    output,
    'See <a href="/openspec/CONTEXT.md" class="auto-link">openspec/CONTEXT.md</a> for details.'
  );
});

test('linkifyBacktickPaths: leaves unrelated code spans untouched', () => {
  const input = 'Run <code>go test ./...</code>.';
  assert.equal(linkifyBacktickPaths(input), input);
});

test('resolveLink: resolves relative path against current document URL', () => {
  const resolved = resolveLink(
    '../adr/0001-x.md',
    'http://localhost:8000/roadmaps/mqtt-console/design.md'
  );
  assert.equal(resolved, 'http://localhost:8000/roadmaps/adr/0001-x.md');
});

test('resolveLink: root-relative path ignores current document depth', () => {
  const resolved = resolveLink(
    '/review.html',
    'http://localhost:8000/changes/archive/2026-07-01-foo/review.html'
  );
  assert.equal(resolved, 'http://localhost:8000/review.html');
});

test('isMarkdownPath: recognizes .md case-insensitively, rejects directories/other extensions', () => {
  assert.equal(isMarkdownPath('/foo/bar.md'), true);
  assert.equal(isMarkdownPath('/foo/bar.MD'), true);
  assert.equal(isMarkdownPath('/foo/bar/'), false);
  assert.equal(isMarkdownPath('/foo/bar.yaml'), false);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && node --test opsx-project-init/tests/engine.test.js`
Expected: FAIL — `Cannot find module '../assets/review-tool/tools/engine.js'` (file doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

Create `opsx-project-init/assets/review-tool/tools/engine.js`:

```js
/*
 * OpenSpec Review Engine — shared logic for every review.html shell in a project.
 * Zero build: loaded via a plain <script> tag. The `module.exports` guard below only
 * activates under Node (used by tests); browsers never define `module`, so it's inert there.
 */

function parseDirectoryListing(html) {
  const entries = [];
  const re = /<li><a href="([^"]+)">/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const rawHref = m[1];
    const isDir = rawHref.endsWith('/');
    const name = decodeURIComponent(isDir ? rawHref.slice(0, -1) : rawHref);
    entries.push({ name, href: rawHref, isDir });
  }
  return entries;
}

function linkifyBacktickPaths(html) {
  return html.replace(
    /<code>(openspec\/[A-Za-z0-9_\-./]+\.md)<\/code>/g,
    (_match, path) => `<a href="/${path}" class="auto-link">${path}</a>`
  );
}

function resolveLink(href, baseUrl) {
  return new URL(href, baseUrl).toString();
}

function isMarkdownPath(path) {
  return /\.md$/i.test(path);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { parseDirectoryListing, linkifyBacktickPaths, resolveLink, isMarkdownPath };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && node --test opsx-project-init/tests/engine.test.js`
Expected: PASS — 7 tests, 0 failures.

- [ ] **Step 5: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-project-init/assets/review-tool/tools/engine.js opsx-project-init/tests/engine.test.js
git commit -m "feat(opsx-project-init): add review-tool engine pure functions (dir-listing parser, link resolution, backtick auto-link)"
```

---

### Task 2: Vendor `marked.js` for offline markdown rendering

**Files:**
- Create: `opsx-project-init/assets/review-tool/tools/vendor/marked.min.js`
- Create: `opsx-project-init/assets/review-tool/tools/vendor/NOTICE.md`

**Interfaces:**
- Produces: a global `window.marked` object (used by Task 3's `loadDoc()` via `window.marked.parse(md)`).

- [ ] **Step 1: Fetch the library**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
mkdir -p opsx-project-init/assets/review-tool/tools/vendor
( curl -fsSL -o /tmp/marked.min.js https://cdn.jsdelivr.net/npm/marked/marked.min.js \
  || curl -fsSL -o /tmp/marked.min.js https://cdn.jsdelivr.net/npm/marked/lib/marked.umd.js )
wc -c /tmp/marked.min.js
```

Expected: file size > 10000 bytes. If both URLs 404 (library restructured its release layout since this
plan was written), resolve the current UMD/browser build URL from https://www.jsdelivr.com/package/npm/marked
and substitute it — the requirement is: a single JS file that, loaded via `<script>`, defines a global
`marked` object with a `.parse(markdownString) -> htmlString` method.

- [ ] **Step 2: Verify it's a working UMD bundle exposing a global**

```bash
node -e "
global.window = {};
const src = require('fs').readFileSync('/tmp/marked.min.js', 'utf8');
new Function(src)();
console.log(typeof window.marked, typeof window.marked.parse);
console.log(window.marked.parse('# hi\n\n- a\n- b'));
"
```

Expected: prints `object function`, then rendered HTML containing `<h1>hi</h1>` and a `<ul>` with two `<li>` items. (Some marked versions attach the export to `globalThis` instead of `window` if `window` isn't defined during eval — if the above throws or prints `undefined`, retry with `global.self = global.window` set before evaluating, since marked's UMD wrapper checks `self`/`window`/`globalThis` in that order.)

- [ ] **Step 3: Copy into place and record provenance**

```bash
cp /tmp/marked.min.js opsx-project-init/assets/review-tool/tools/vendor/marked.min.js
head -c 120 opsx-project-init/assets/review-tool/tools/vendor/marked.min.js
```

Take the output of `head -c 120` (it contains a version banner comment in marked's minified builds) and paste it into the NOTICE file below in place of `<PASTE BANNER HERE>`.

Create `opsx-project-init/assets/review-tool/tools/vendor/NOTICE.md`:

```markdown
# Vendored: marked.js

- Source: https://cdn.jsdelivr.net/npm/marked/marked.min.js (or the `lib/marked.umd.js` fallback)
- Fetched: 2026-07-01
- Version banner (first bytes of the file): <PASTE BANNER HERE>
- License: MIT — https://github.com/markedjs/marked/blob/master/LICENSE.md

Vendored (not loaded from a CDN) so the review tool works fully offline — this project is
local-first by design, the review tool shouldn't be the one thing that needs network access.
To upgrade: repeat the fetch command in `docs/superpowers/plans/2026-07-01-openspec-review-html-tool.md`
Task 2 Step 1 and re-run `opsx-project-init update` on every project that uses this tool.
```

- [ ] **Step 4: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-project-init/assets/review-tool/tools/vendor/
git commit -m "feat(opsx-project-init): vendor marked.js for offline markdown rendering in review tool"
```

---

### Task 3: DOM glue in `engine.js` — render, navigate, sidebar, history

**Files:**
- Modify: `opsx-project-init/assets/review-tool/tools/engine.js` (append after the pure-functions section from Task 1)
- Manual/scripted verification: Playwright MCP tools (`mcp__plugin_playwright_playwright__*`), no new test file — this section is DOM/fetch/history glue that isn't meaningfully unit-testable without a full browser; Task 1's pure functions already cover the logic that *can* be isolated.

**Interfaces:**
- Consumes: `parseDirectoryListing`, `linkifyBacktickPaths`, `resolveLink`, `isMarkdownPath` from Task 1 (same file, same scope, no import needed). `window.marked.parse` from Task 2. `window.__OPENSPEC_REVIEW_SCOPE__` (a string, either `""` for the root shell or `"roadmaps/<name>/"` / `"changes/<name>/"` for per-directory shells) set inline by Task 5's `review-stub.html` template before this script loads.
- Produces: no new exported functions (this is the browser-only entry point); it mounts into `<div id="app">` which Task 5's template provides, and expects CSS classes `#sidebar`, `#content`, `.back-link`, `.hint`, `.error`, `.auto-link` to exist (defined in Task 4's `engine.css`).

- [ ] **Step 1: Append the DOM glue to `engine.js`**

Append to `opsx-project-init/assets/review-tool/tools/engine.js` (after the existing `module.exports` block):

```js

// ---- DOM glue (browser-only; the `typeof document` guard keeps this inert under Node) ----

if (typeof document !== 'undefined') {
  (function () {
    const SCOPE = window.__OPENSPEC_REVIEW_SCOPE__ || '';
    const initialDir = SCOPE ? `/${SCOPE}` : '/';

    const app = document.getElementById('app');
    const sidebar = document.createElement('div');
    sidebar.id = 'sidebar';
    const content = document.createElement('div');
    content.id = 'content';
    app.appendChild(sidebar);
    app.appendChild(content);

    function escapeHtml(s) {
      return s.replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
      }[c]));
    }

    async function fetchText(path) {
      const res = await fetch(path);
      if (!res.ok) throw new Error(`fetch failed: ${path} (${res.status})`);
      return res.text();
    }

    async function loadSidebar(dirPath) {
      const html = await fetchText(dirPath);
      const entries = parseDirectoryListing(html)
        .filter((e) => e.isDir || isMarkdownPath(e.name))
        .sort((a, b) => (a.isDir === b.isDir ? a.name.localeCompare(b.name) : a.isDir ? -1 : 1));
      sidebar.innerHTML = '';
      if (SCOPE !== '') {
        const back = document.createElement('a');
        back.href = '/review.html';
        back.className = 'back-link';
        back.textContent = '← 全部文档'; // ← 全部文档
        sidebar.appendChild(back);
      }
      const list = document.createElement('ul');
      entries.forEach((e) => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = resolveLink(e.href, new URL(dirPath, window.location.href).toString());
        a.textContent = e.isDir ? `${e.name}/` : e.name;
        li.appendChild(a);
        list.appendChild(li);
      });
      sidebar.appendChild(list);
    }

    async function loadDir(path) {
      await loadSidebar(path);
      content.innerHTML = `<p class="hint">目录：${escapeHtml(path)}<br>请选择左侧的文档。</p>`;
      document.title = path;
    }

    async function loadDoc(path) {
      const md = await fetchText(path);
      const rendered = window.marked ? window.marked.parse(md) : `<pre>${escapeHtml(md)}</pre>`;
      content.innerHTML = linkifyBacktickPaths(rendered);
      document.title = path;
      const dir = path.replace(/[^/]*$/, '');
      await loadSidebar(dir);
    }

    async function navigate(path, push) {
      try {
        if (path.endsWith('/')) {
          await loadDir(path);
        } else {
          await loadDoc(path);
        }
        if (push) history.pushState({ path }, '', `#${path}`);
      } catch (err) {
        content.innerHTML = `<p class="error">加载失败：${escapeHtml(path)}</p>`;
      }
    }

    function onLinkClick(ev) {
      const a = ev.target.closest('a');
      if (!a) return;
      const href = a.getAttribute('href');
      if (!href || href.startsWith('http://') || href.startsWith('https://')) return;
      ev.preventDefault();
      const resolved = resolveLink(href, window.location.href);
      const path = new URL(resolved).pathname;
      navigate(path, true);
    }

    document.body.addEventListener('click', onLinkClick);
    window.addEventListener('popstate', (ev) => {
      const path = (ev.state && ev.state.path) || initialDir;
      navigate(path, false);
    });

    navigate(initialDir, false);
  })();
}
```

- [ ] **Step 2: Verify `node --test` from Task 1 still passes (the new code must not break the Node-require path)**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && node --test opsx-project-init/tests/engine.test.js`
Expected: PASS — same 7 tests as Task 1 (the `typeof document !== 'undefined'` guard means none of the new code executes under plain `node --test`, since Node has no global `document`).

- [ ] **Step 3: End-to-end verification with a real server + real browser (Playwright)**

This step needs Task 4 (CSS) and Task 5 (review-stub.html template) done first to actually render anything —
if executing tasks strictly in order, come back to this step after Task 5, before committing Task 3.
Use the mqtt-console repo's real `openspec/` tree as the fixture (already has the multi-level structure —
`roadmaps/`, `adr/`, `changes/archive/<name>/` — this plan needs):

```bash
cd /Users/cheneyzhao/Documents/05-sarvelo/mqtt-console/openspec
cp -r /Users/cheneyzhao/.skills/laodao-skills/opsx-project-init/assets/review-tool/tools .
cp /Users/cheneyzhao/.skills/laodao-skills/opsx-project-init/assets/review-tool/tools/review-stub.html /tmp/root-review.html
sed 's/__SCOPE__//' /tmp/root-review.html > review.html
python3 -m http.server 8917 &
echo "PID=$!"
```

Then, using the Playwright MCP tools:
- Navigate to `http://localhost:8917/review.html`.
- Take a snapshot; confirm the sidebar lists `adr/`, `changes/`, `roadmaps/`, `workflow/`, etc. (matching the
  real directory list captured earlier in this project's exploration, reproduced in the memo).
- Click `roadmaps/` in the sidebar; confirm the sidebar updates to show `mqtt-console/` and the content pane
  shows the "目录：/roadmaps/" hint.
- Drill into `mqtt-console/`, click `design.md`; confirm the content pane renders real markdown (headers,
  the "决策" sections) — not raw text.
- Find a `` `openspec/CONTEXT.md` `` backtick reference inside a rendered doc (e.g. `requirements.md` has one)
  and confirm it rendered as a clickable link, and clicking it loads `CONTEXT.md`.
- Click browser back; confirm it returns to the previous doc (history works).
- Kill the test server: `kill %1` (or the PID printed above).

Expected: every step above behaves as described, no console errors. If anything fails, fix `engine.js`/`engine.css`
before proceeding — do not mark this task committed on a failing manual verification.

- [ ] **Step 4: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-project-init/assets/review-tool/tools/engine.js
git commit -m "feat(opsx-project-init): add review-tool DOM glue (navigate/render/sidebar/history)"
```

---

### Task 4: `engine.css`

**Files:**
- Create: `opsx-project-init/assets/review-tool/tools/engine.css`

**Interfaces:**
- Consumes: DOM structure produced by Task 3 (`#app > #sidebar, #content`, `.back-link`, `.hint`, `.error` inside `#content`, `.auto-link` on backtick-converted anchors).
- Produces: nothing consumed by later tasks directly; verified visually as part of Task 3 Step 3's Playwright pass.

- [ ] **Step 1: Write the stylesheet**

Create `opsx-project-init/assets/review-tool/tools/engine.css`:

```css
* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1a1a1a;
  background: #fff;
}

#app {
  display: flex;
  height: 100vh;
}

#sidebar {
  width: 260px;
  flex-shrink: 0;
  overflow-y: auto;
  border-right: 1px solid #ddd;
  padding: 12px;
  background: #fafafa;
}

#sidebar ul {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
}

#sidebar li {
  margin: 2px 0;
}

#sidebar a {
  display: block;
  padding: 4px 6px;
  border-radius: 4px;
  color: #1a1a1a;
  text-decoration: none;
  font-size: 13px;
  word-break: break-all;
}

#sidebar a:hover {
  background: #e8e8e8;
}

.back-link {
  display: block;
  margin-bottom: 8px;
  padding: 6px;
  font-weight: 600;
  color: #0969da;
  text-decoration: none;
  border-bottom: 1px solid #ddd;
}

#content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 40px;
  max-width: 900px;
}

#content .hint,
#content .error {
  color: #666;
}

#content .error {
  color: #c00;
}

#content pre {
  background: #f6f8fa;
  padding: 12px;
  overflow-x: auto;
  border-radius: 6px;
}

#content code {
  background: #f6f8fa;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 0.9em;
}

#content table {
  border-collapse: collapse;
}

#content th,
#content td {
  border: 1px solid #ddd;
  padding: 6px 10px;
}

a.auto-link {
  color: #0969da;
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-project-init/assets/review-tool/tools/engine.css
git commit -m "feat(opsx-project-init): add review-tool stylesheet"
```

---

### Task 5: `review-stub.html` template + `serve.sh`

**Files:**
- Create: `opsx-project-init/assets/review-tool/tools/review-stub.html`
- Create: `opsx-project-init/assets/review-tool/serve.sh`
- Test: `opsx-project-init/tests/test_init.py` (covers the substitution behavior via `copy_review_tool`, added in Task 6 — this task just produces the two static files; Step 2 below is a standalone manual check since there's no Python logic yet to unit test)

**Interfaces:**
- Produces: `review-stub.html` with the literal token `__SCOPE__` inside an inline `<script>`, to be string-replaced by Task 6's `copy_review_tool()`, Task 8's hook, and Task 9's `gen_review_stub.py`. `serve.sh` takes the same args as `python3 -m http.server` (e.g. a port number or none).

- [ ] **Step 1: Write the shell template**

Create `opsx-project-init/assets/review-tool/tools/review-stub.html`:

```html
<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenSpec Review</title>
<link rel="stylesheet" href="/tools/engine.css">
</head>
<body>
<div id="app"></div>
<script>window.__OPENSPEC_REVIEW_SCOPE__ = "__SCOPE__";</script>
<script src="/tools/vendor/marked.min.js"></script>
<script src="/tools/engine.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write the server launcher**

Create `opsx-project-init/assets/review-tool/serve.sh`:

```sh
#!/bin/sh
# Starts a static file server rooted at openspec/, regardless of the caller's cwd —
# review.html's root-relative asset paths (/tools/engine.js etc.) depend on the server
# root being exactly openspec/, so this always cd's to its own directory first.
cd "$(dirname "$0")" || exit 1
exec python3 -m http.server "$@"
```

```bash
chmod +x opsx-project-init/assets/review-tool/serve.sh
```

- [ ] **Step 3: Manually verify `serve.sh` roots correctly regardless of invocation cwd**

```bash
cd /tmp
bash /Users/cheneyzhao/.skills/laodao-skills/opsx-project-init/assets/review-tool/serve.sh 8918 &
echo "PID=$!"
sleep 1
curl -s http://localhost:8918/ | grep -o 'review-stub.html\|tools/\|serve.sh'
kill %1
```

Expected: the curl output lists `serve.sh` and `tools/` (confirming the server's root is the
`review-tool/` directory containing this script, NOT `/tmp` where we `cd`'d before running it).

- [ ] **Step 4: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-project-init/assets/review-tool/tools/review-stub.html opsx-project-init/assets/review-tool/serve.sh
git commit -m "feat(opsx-project-init): add review.html shell template and serve.sh launcher"
```

---

### Task 6: `init.py` — `copy_review_tool()` (root shell + tools/ + serve.sh)

**Files:**
- Modify: `opsx-project-init/scripts/init.py`
- Test: `opsx-project-init/tests/test_init.py` (new file)

**Interfaces:**
- Consumes: `ASSETS` constant (already defined in `init.py`, line 28: `os.path.join(SKILL_DIR, "assets")`).
- Produces: `copy_review_tool(root: str) -> int` (returns count of files written), called from `run()`. Later tasks (8, 9) rely on the *output* of this function existing on disk (`<project>/openspec/tools/review-stub.html`, `<project>/openspec/review.html`) — not on any Python symbol.

- [ ] **Step 1: Write the failing test**

Create `opsx-project-init/tests/test_init.py`:

```python
"""
Tests for init.py's review-tool copying + generalized hook installer.
Run with: python3 -m pytest opsx-project-init/tests/test_init.py -v
"""
import json
import os
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import init as init_mod
from init import copy_review_tool


class TestCopyReviewTool:
    def test_copies_tools_dir_and_serve_sh_and_generates_root_review_html(self, tmp_path):
        n = copy_review_tool(str(tmp_path))
        osroot = tmp_path / "openspec"
        assert (osroot / "tools" / "engine.js").is_file()
        assert (osroot / "tools" / "engine.css").is_file()
        assert (osroot / "tools" / "review-stub.html").is_file()
        assert (osroot / "tools" / "vendor" / "marked.min.js").is_file()
        assert (osroot / "serve.sh").is_file()
        assert (osroot / "review.html").is_file()
        assert n > 0

    def test_root_review_html_has_empty_scope(self, tmp_path):
        copy_review_tool(str(tmp_path))
        content = (tmp_path / "openspec" / "review.html").read_text(encoding="utf-8")
        assert 'window.__OPENSPEC_REVIEW_SCOPE__ = "";' in content
        assert "__SCOPE__" not in content

    def test_serve_sh_is_executable(self, tmp_path):
        copy_review_tool(str(tmp_path))
        mode = (tmp_path / "openspec" / "serve.sh").stat().st_mode
        assert mode & stat.S_IXUSR

    def test_idempotent_rerun_overwrites_cleanly(self, tmp_path):
        copy_review_tool(str(tmp_path))
        copy_review_tool(str(tmp_path))  # update-mode re-run
        osroot = tmp_path / "openspec"
        assert (osroot / "review.html").is_file()
        content = (osroot / "review.html").read_text(encoding="utf-8")
        assert content.count("__OPENSPEC_REVIEW_SCOPE__") == 1  # not duplicated/appended
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && python3 -m pytest opsx-project-init/tests/test_init.py -v`
Expected: FAIL — `ImportError: cannot import name 'copy_review_tool' from 'init'` (doesn't exist yet).

- [ ] **Step 3: Implement `copy_review_tool()` in `init.py`**

Read the full current file first: `opsx-project-init/scripts/init.py`.

Modify `opsx-project-init/scripts/init.py` — add this constant near the top, right after the existing
`BUNDLE_SRC = os.path.join(ASSETS, "workflow")` line (around line 29):

```python
REVIEW_TOOL_SRC = os.path.join(ASSETS, "review-tool")
```

Add this function right after the existing `copy_bundle()` function (around line 81, before `ensure_dirs`):

```python
def copy_review_tool(root):
    """铺设 review.html / serve.sh / tools/（engine.js, engine.css, vendor/, review-stub.html）到
    openspec/。根 review.html 由 review-stub.html 模板生成（__SCOPE__ 替换为空串）。
    update 模式整体覆盖刷新（与 copy_bundle 同款语义）。
    """
    osroot = os.path.join(root, "openspec")
    dst_tools = os.path.join(osroot, "tools")
    shutil.copytree(os.path.join(REVIEW_TOOL_SRC, "tools"), dst_tools, dirs_exist_ok=True)

    serve_src = os.path.join(REVIEW_TOOL_SRC, "serve.sh")
    serve_dst = os.path.join(osroot, "serve.sh")
    shutil.copyfile(serve_src, serve_dst)
    shutil.copymode(serve_src, serve_dst)

    stub_path = os.path.join(dst_tools, "review-stub.html")
    template = open(stub_path, encoding="utf-8").read()
    review_html = template.replace("__SCOPE__", "")
    with open(os.path.join(osroot, "review.html"), "w", encoding="utf-8") as f:
        f.write(review_html)

    return sum(len(fs) for _, _, fs in os.walk(dst_tools)) + 2  # +serve.sh +review.html
```

Wire it into `run()` — modify the existing block (around line 181-182):

```python
    dst, n = copy_bundle(root)
    report.append(f"铺 bundle：openspec/workflow/（{n} 文件，{'覆盖' if mode=='update' else '写入'}）")
```

to:

```python
    dst, n = copy_bundle(root)
    report.append(f"铺 bundle：openspec/workflow/（{n} 文件，{'覆盖' if mode=='update' else '写入'}）")

    n_review = copy_review_tool(root)
    report.append(
        f"铺 review 工具：openspec/review.html + openspec/tools/ + openspec/serve.sh"
        f"（{n_review} 文件，{'覆盖' if mode=='update' else '写入'}）"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && python3 -m pytest opsx-project-init/tests/test_init.py -v`
Expected: PASS — 4 tests (the ones written in Step 1; the hook-installer tests come in Task 7).

- [ ] **Step 5: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-project-init/scripts/init.py opsx-project-init/tests/test_init.py
git commit -m "feat(opsx-project-init): copy review-tool assets into projects on init/update"
```

---

### Task 7: Generalize `ensure_global_hook()` into a data-driven multi-hook installer

**Files:**
- Modify: `opsx-project-init/scripts/init.py`
- Test: `opsx-project-init/tests/test_init.py` (append)

**Interfaces:**
- Consumes: nothing new.
- Produces: `HOOKS` (list of hook spec dicts), `ensure_global_hook(spec: dict) -> str`, `ensure_global_hooks() -> str`. Task 8's new hook file gets registered via a new entry in `HOOKS`.

**Why this task exists:** `ensure_global_hook()` currently (lines 106-164 of the existing `init.py`) hardcodes
exactly one hook (`ff0-branch-guard.py`, `PreToolUse`). Task 8 adds a second hook
(`change-review-stub.py`, `PostToolUse`) that needs the same idempotent install-and-register behavior. Rather
than copy-pasting the whole function with different constants, generalize it once so both hooks — and any
future one — share one code path.

- [ ] **Step 1: Write the failing test**

Append to `opsx-project-init/tests/test_init.py`:

```python
class TestEnsureGlobalHooks:
    def _settings_path(self, home):
        return home / "settings.json"

    def test_installs_and_registers_a_new_hook_spec(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        src = tmp_path / "myhook.py"
        src.write_text("print('hi')\n", encoding="utf-8")
        spec = {
            "name": "myhook.py",
            "src": str(src),
            "event": "PostToolUse",
            "matcher": "Bash",
            "cmd": 'python3 "$HOME/.claude/hooks/myhook.py"',
        }
        msg = init_mod.ensure_global_hook(spec)
        assert "安装" in msg
        assert (home / "hooks" / "myhook.py").is_file()
        data = json.loads(self._settings_path(home).read_text(encoding="utf-8"))
        assert data["hooks"]["PostToolUse"][0]["matcher"] == "Bash"
        assert "myhook.py" in data["hooks"]["PostToolUse"][0]["hooks"][0]["command"]

    def test_rerun_is_idempotent_no_duplicate_registration(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        src = tmp_path / "myhook.py"
        src.write_text("print('hi')\n", encoding="utf-8")
        spec = {
            "name": "myhook.py",
            "src": str(src),
            "event": "PostToolUse",
            "matcher": "Bash",
            "cmd": 'python3 "$HOME/.claude/hooks/myhook.py"',
        }
        init_mod.ensure_global_hook(spec)
        init_mod.ensure_global_hook(spec)
        data = json.loads(self._settings_path(home).read_text(encoding="utf-8"))
        assert len(data["hooks"]["PostToolUse"]) == 1

    def test_two_different_hooks_land_in_their_own_event_lists(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        pre_src = tmp_path / "pre.py"
        pre_src.write_text("print('pre')\n", encoding="utf-8")
        post_src = tmp_path / "post.py"
        post_src.write_text("print('post')\n", encoding="utf-8")
        init_mod.ensure_global_hook({
            "name": "pre.py", "src": str(pre_src), "event": "PreToolUse",
            "matcher": "Bash", "cmd": 'python3 "$HOME/.claude/hooks/pre.py"',
        })
        init_mod.ensure_global_hook({
            "name": "post.py", "src": str(post_src), "event": "PostToolUse",
            "matcher": "Bash", "cmd": 'python3 "$HOME/.claude/hooks/post.py"',
        })
        data = json.loads(self._settings_path(home).read_text(encoding="utf-8"))
        assert len(data["hooks"]["PreToolUse"]) == 1
        assert len(data["hooks"]["PostToolUse"]) == 1

    def test_preexisting_single_hook_registration_still_recognized(self, tmp_path, monkeypatch):
        """Backward compat: a settings.json written by the OLD single-hook ensure_global_hook()
        must still be recognized as 'already registered' by the new generalized version."""
        home = tmp_path / "home"
        home.mkdir()
        (home / "hooks").mkdir()
        src = tmp_path / "ff0.py"
        src.write_text("print('ff0')\n", encoding="utf-8")
        (home / "hooks" / "ff0.py").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        (self._settings_path(home)).write_text(json.dumps({
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/ff0.py"'}
            ]}]}
        }), encoding="utf-8")
        spec = {
            "name": "ff0.py", "src": str(src), "event": "PreToolUse",
            "matcher": "Bash", "cmd": 'python3 "$HOME/.claude/hooks/ff0.py"',
        }
        msg = init_mod.ensure_global_hook(spec)
        assert "已注册" in msg
        data = json.loads(self._settings_path(home).read_text(encoding="utf-8"))
        assert len(data["hooks"]["PreToolUse"]) == 1  # not duplicated
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && python3 -m pytest opsx-project-init/tests/test_init.py::TestEnsureGlobalHooks -v`
Expected: FAIL — `AttributeError: module 'init' has no attribute 'ensure_global_hook'` with the new signature
(the current one takes zero arguments, not a `spec` dict).

- [ ] **Step 3: Replace the hardcoded `ensure_global_hook()` with the generalized version**

Modify `opsx-project-init/scripts/init.py` — replace the entire existing block (lines 39-42 constants
`HOOK_SRC`/`HOOK_NAME`/`HOOK_CMD`, and the whole `ensure_global_hook()` function at lines 106-164) with:

```python
HOOKS = [
    {
        "name": "ff0-branch-guard.py",
        "src": os.path.join(ASSETS, "hooks", "ff0-branch-guard.py"),
        "event": "PreToolUse",
        "matcher": "Bash",
        "cmd": 'python3 "$HOME/.claude/hooks/ff0-branch-guard.py"',
    },
    {
        "name": "change-review-stub.py",
        "src": os.path.join(ASSETS, "hooks", "change-review-stub.py"),
        "event": "PostToolUse",
        "matcher": "Bash",
        "cmd": 'python3 "$HOME/.claude/hooks/change-review-stub.py"',
    },
]


def ensure_global_hook(spec):
    """幂等把单个全局 hook 装好：脚本拷进 ~/.claude/hooks/ + 注册进 ~/.claude/settings.json
    对应 event 的 hooks 列表。spec 形如 HOOKS 里的一项。返回动作描述。
    """
    home_claude = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    acts = []

    hooks_dir = os.path.join(home_claude, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    dst = os.path.join(hooks_dir, spec["name"])
    if not os.path.exists(spec["src"]):
        return f"跳过（hook 源缺失：{spec['src']}）"
    new_src = open(spec["src"], encoding="utf-8").read()
    old_src = open(dst, encoding="utf-8").read() if os.path.exists(dst) else None
    if old_src != new_src:
        shutil.copyfile(spec["src"], dst)
        acts.append("脚本已" + ("更新" if old_src is not None else "安装") + f" {dst}")
    else:
        acts.append("脚本已最新")

    settings = os.path.join(home_claude, "settings.json")
    if os.path.exists(settings):
        try:
            data = json.load(open(settings, encoding="utf-8"))
        except (ValueError, OSError):
            return "脚本已就位；跳过注册（~/.claude/settings.json 非合法 JSON，请手动注册）"
        if not isinstance(data, dict):
            return "脚本已就位；跳过注册（~/.claude/settings.json 顶层非对象）"
    else:
        data = {}

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        data["hooks"] = hooks
    event_list = hooks.get(spec["event"])
    if not isinstance(event_list, list):
        event_list = []
        hooks[spec["event"]] = event_list

    for entry in event_list:
        for h in (entry.get("hooks") or []):
            if spec["name"] in (h.get("command") or ""):
                acts.append("已注册（全局）")
                return "；".join(acts)

    event_list.append({
        "matcher": spec["matcher"],
        "hooks": [{"type": "command", "command": spec["cmd"]}],
    })
    with open(settings, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    acts.append(f"已注册 → ~/.claude/settings.json（{spec['event']}）")
    return "；".join(acts)


def ensure_global_hooks():
    """按 HOOKS 逐个幂等安装，返回多行汇总。"""
    return "\n".join(f"  · {spec['name']}：{ensure_global_hook(spec)}" for spec in HOOKS)
```

Then update the one call site in `run()` (originally `report.append("FF-0 hook（全局）：" + ensure_global_hook())`)
to:

```python
    report.append("全局 hooks：\n" + ensure_global_hooks())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && python3 -m pytest opsx-project-init/tests/test_init.py -v`
Expected: PASS — all tests from Task 6 and Task 7 (8 total).

- [ ] **Step 5: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-project-init/scripts/init.py opsx-project-init/tests/test_init.py
git commit -m "refactor(opsx-project-init): generalize ensure_global_hook to a data-driven multi-hook installer"
```

---

### Task 8: New PostToolUse hook — `change-review-stub.py`

**Files:**
- Create: `opsx-project-init/assets/hooks/change-review-stub.py`
- Test: `opsx-project-init/tests/test_change_review_stub_hook.py`

**Interfaces:**
- Consumes: the `review-stub.html` template produced at `<project>/openspec/tools/review-stub.html` by Task 6's `copy_review_tool()`.
- Produces: `<project>/openspec/changes/<name>/review.html` (a side effect on disk, invoked by Claude Code's PostToolUse hook mechanism — no Python function is imported by anything else; Task 7's `HOOKS` list references this file by path only).

- [ ] **Step 1: Write the failing test**

Create `opsx-project-init/tests/test_change_review_stub_hook.py`:

```python
"""
Tests for the change-review-stub.py PostToolUse hook.
Run with: python3 -m pytest opsx-project-init/tests/test_change_review_stub_hook.py -v
"""
import json
import subprocess
import sys
from pathlib import Path

HOOK = str(Path(__file__).parent.parent / "assets" / "hooks" / "change-review-stub.py")


def run_hook(payload, cwd):
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(payload),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=5,
    )


def make_project(tmp_path, with_review_tool=True):
    osroot = tmp_path / "openspec"
    (osroot / "changes" / "add-widget").mkdir(parents=True)
    if with_review_tool:
        (osroot / "tools").mkdir(parents=True, exist_ok=True)
        (osroot / "tools" / "review-stub.html").write_text(
            '<script>window.__OPENSPEC_REVIEW_SCOPE__ = "__SCOPE__";</script>', encoding="utf-8"
        )
        (osroot / "review.html").write_text("root", encoding="utf-8")
    return tmp_path


class TestChangeReviewStubHook:
    def test_writes_stub_when_change_dir_and_review_tool_exist(self, tmp_path):
        make_project(tmp_path)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change add-widget"},
            "cwd": str(tmp_path),
        }
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0
        stub = tmp_path / "openspec" / "changes" / "add-widget" / "review.html"
        assert stub.is_file()
        assert 'window.__OPENSPEC_REVIEW_SCOPE__ = "changes/add-widget/";' in stub.read_text(encoding="utf-8")

    def test_skips_silently_when_review_tool_not_installed(self, tmp_path):
        make_project(tmp_path, with_review_tool=False)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change add-widget"},
            "cwd": str(tmp_path),
        }
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0
        assert not (tmp_path / "openspec" / "changes" / "add-widget" / "review.html").exists()

    def test_skips_silently_when_change_dir_does_not_exist(self, tmp_path):
        make_project(tmp_path)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change never-created"},
            "cwd": str(tmp_path),
        }
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0
        assert not (tmp_path / "openspec" / "changes" / "never-created").exists()

    def test_ignores_non_bash_tools(self, tmp_path):
        make_project(tmp_path)
        payload = {"tool_name": "Write", "tool_input": {}, "cwd": str(tmp_path)}
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0

    def test_ignores_unrelated_bash_commands(self, tmp_path):
        make_project(tmp_path)
        payload = {"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(tmp_path)}
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0

    def test_idempotent_rerun_does_not_error(self, tmp_path):
        make_project(tmp_path)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change add-widget"},
            "cwd": str(tmp_path),
        }
        run_hook(payload, tmp_path)
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0

    def test_handles_garbage_stdin_by_exiting_zero(self, tmp_path):
        make_project(tmp_path)
        result = subprocess.run(
            [sys.executable, HOOK], input="not json", cwd=str(tmp_path),
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && python3 -m pytest opsx-project-init/tests/test_change_review_stub_hook.py -v`
Expected: FAIL — every test errors because `assets/hooks/change-review-stub.py` doesn't exist yet
(`FileNotFoundError` from `subprocess.run`).

- [ ] **Step 3: Write the hook**

Create `opsx-project-init/assets/hooks/change-review-stub.py`:

```python
#!/usr/bin/env python3
"""Change review-stub hook —— PostToolUse hook（change 目录建好后补一份 review.html）。

为什么挂在 CLI 这层：/opsx:new、/opsx:propose、/opsx:ff、/opsx:onboard 都殊途同归调用同一条命令
`openspec new change <name>` 来 scaffold 变更（这几个 skill 本身不在本仓库）。只需拦这一条 Bash
命令，即覆盖所有「创建变更」入口，参见 ff0-branch-guard.py 的同一思路（那个拦 PreToolUse 做 deny，
这个挂 PostToolUse 做补文件，互不冲突）。

行为：
  · 仅对 Bash 工具、且命令实际执行 `openspec new change <name>` 时介入（PostToolUse：命令已跑完）。
  · 解析出 <name>；若 openspec/changes/<name>/ 不存在（如被 FF-0 拦下、或命令本身失败）→ 静默放行。
  · 若项目根 openspec/review.html 或 openspec/tools/review-stub.html 不存在（还没跑过
    opsx-project-init）→ 静默放行，不强迫铺设顺序。
  · 否则读模板、替换 __SCOPE__ 为 "changes/<name>/"，写入
    openspec/changes/<name>/review.html（幂等：内容已一致则跳过写入）。
  · 任何异常 → 静默放行（fail-open，绝不因本 hook 故障阻断正常工作）。

铺设/注册：全局装于 ~/.claude/hooks/ + 注册进 ~/.claude/settings.json 的 PostToolUse.Bash
          （opsx-project-init 的 ensure_global_hooks() 负责，见 scripts/init.py 的 HOOKS 列表）。
"""
import json
import os
import re
import sys

NEW_CHANGE_RE = re.compile(r"openspec\s+(?:new\s+change|change\s+new)\s+(\S+)")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command", "") or ""
    m = NEW_CHANGE_RE.search(command)
    if not m:
        sys.exit(0)

    name = m.group(1).strip().strip("'\"")
    cwd = payload.get("cwd") or "."

    change_dir = os.path.join(cwd, "openspec", "changes", name)
    if not os.path.isdir(change_dir):
        sys.exit(0)  # 命令没真正建出目录（被拦 / 失败）→ 放行

    stub_template_path = os.path.join(cwd, "openspec", "tools", "review-stub.html")
    root_review_path = os.path.join(cwd, "openspec", "review.html")
    if not (os.path.isfile(stub_template_path) and os.path.isfile(root_review_path)):
        sys.exit(0)  # 项目还没跑过 opsx-project-init → 静默跳过

    try:
        template = open(stub_template_path, encoding="utf-8").read()
    except OSError:
        sys.exit(0)

    stub_content = template.replace("__SCOPE__", f"changes/{name}/")
    dst = os.path.join(change_dir, "review.html")
    existing = open(dst, encoding="utf-8").read() if os.path.exists(dst) else None
    if existing != stub_content:
        try:
            with open(dst, "w", encoding="utf-8") as f:
                f.write(stub_content)
        except OSError:
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && python3 -m pytest opsx-project-init/tests/test_change_review_stub_hook.py -v`
Expected: PASS — 7 tests.

- [ ] **Step 5: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-project-init/assets/hooks/change-review-stub.py opsx-project-init/tests/test_change_review_stub_hook.py
git commit -m "feat(opsx-project-init): add PostToolUse hook that stubs review.html into new change dirs"
```

---

### Task 9: `opsx-roadmap-planner/scripts/gen_review_stub.py`

**Files:**
- Create: `opsx-roadmap-planner/scripts/gen_review_stub.py`
- Test: `opsx-roadmap-planner/tests/test_gen_review_stub.py`

**Interfaces:**
- Consumes: `<project>/openspec/tools/review-stub.html` and `<project>/openspec/review.html` (existence-checked, same precondition as Task 8's hook).
- Produces: `<project>/openspec/roadmaps/<name>/review.html`. CLI entry point `python3 gen_review_stub.py <name> [--root PATH]`, invoked by a human/model per Task 10's SKILL.md instructions — not imported by other code.

- [ ] **Step 1: Write the failing test**

Create `opsx-roadmap-planner/tests/test_gen_review_stub.py`:

```python
"""
Tests for gen_review_stub.py — generates openspec/roadmaps/<name>/review.html.
Run with: python3 -m pytest opsx-roadmap-planner/tests/test_gen_review_stub.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from gen_review_stub import gen_review_stub


def make_project(tmp_path, with_review_tool=True, with_roadmap_dir=True):
    osroot = tmp_path / "openspec"
    if with_roadmap_dir:
        (osroot / "roadmaps" / "my-feature").mkdir(parents=True)
    if with_review_tool:
        (osroot / "tools").mkdir(parents=True, exist_ok=True)
        (osroot / "tools" / "review-stub.html").write_text(
            '<script>window.__OPENSPEC_REVIEW_SCOPE__ = "__SCOPE__";</script>', encoding="utf-8"
        )
        (osroot / "review.html").write_text("root", encoding="utf-8")
    return tmp_path


class TestGenReviewStub:
    def test_writes_stub_with_correct_scope(self, tmp_path):
        make_project(tmp_path)
        dst = gen_review_stub(str(tmp_path), "my-feature")
        content = Path(dst).read_text(encoding="utf-8")
        assert 'window.__OPENSPEC_REVIEW_SCOPE__ = "roadmaps/my-feature/";' in content

    def test_raises_when_review_tool_missing(self, tmp_path):
        make_project(tmp_path, with_review_tool=False)
        with pytest.raises(FileNotFoundError, match="review 工具"):
            gen_review_stub(str(tmp_path), "my-feature")

    def test_raises_when_roadmap_dir_missing(self, tmp_path):
        make_project(tmp_path, with_roadmap_dir=False)
        with pytest.raises(FileNotFoundError, match="目录不存在"):
            gen_review_stub(str(tmp_path), "my-feature")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && python3 -m pytest opsx-roadmap-planner/tests/test_gen_review_stub.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gen_review_stub'`.

- [ ] **Step 3: Write the script**

Create `opsx-roadmap-planner/scripts/gen_review_stub.py`:

```python
#!/usr/bin/env python3
"""生成 openspec/roadmaps/{name}/review.html —— roadmap 四件套产出后顺手落一份查看器 stub。

读取项目根 openspec/tools/review-stub.html 模板（由 opsx-project-init 铺设），替换 __SCOPE__
为 "roadmaps/{name}/"，写入 openspec/roadmaps/{name}/review.html。

与 change-review-stub.py 那个 hook 的取舍不同：hook 是自动触发、缺前提静默跳过；这里是
opsx-roadmap-planner 流程里模型显式调用的一步，缺前提直接抛错更利于及时发现。
"""
import argparse
import os
import sys


def gen_review_stub(root, name):
    osroot = os.path.join(root, "openspec")
    stub_template_path = os.path.join(osroot, "tools", "review-stub.html")
    root_review_path = os.path.join(osroot, "review.html")
    if not (os.path.isfile(stub_template_path) and os.path.isfile(root_review_path)):
        raise FileNotFoundError(
            "项目未铺设 review 工具（缺 openspec/tools/review-stub.html 或 openspec/review.html）。"
            "先跑 opsx-project-init init/update。"
        )
    roadmap_dir = os.path.join(osroot, "roadmaps", name)
    if not os.path.isdir(roadmap_dir):
        raise FileNotFoundError(f"目录不存在：{roadmap_dir}（应在四件套生成之后再跑本脚本）")

    template = open(stub_template_path, encoding="utf-8").read()
    stub_content = template.replace("__SCOPE__", f"roadmaps/{name}/")
    dst = os.path.join(roadmap_dir, "review.html")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(stub_content)
    return dst


def main():
    p = argparse.ArgumentParser(description="生成 roadmap 目录的 review.html stub")
    p.add_argument("name", help="roadmap 目录名（kebab-case，即 openspec/roadmaps/<name>/）")
    p.add_argument("--root", default=".", help="项目根（默认当前目录）")
    args = p.parse_args()
    try:
        dst = gen_review_stub(args.root, args.name)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✓ 已生成 {dst}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/cheneyzhao/.skills/laodao-skills && python3 -m pytest opsx-roadmap-planner/tests/test_gen_review_stub.py -v`
Expected: PASS — 3 tests.

- [ ] **Step 5: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-roadmap-planner/scripts/gen_review_stub.py opsx-roadmap-planner/tests/test_gen_review_stub.py
git commit -m "feat(opsx-roadmap-planner): add gen_review_stub.py to stub roadmaps/<name>/review.html"
```

---

### Task 10: Wire `gen_review_stub.py` into `opsx-roadmap-planner/SKILL.md`

**Files:**
- Modify: `opsx-roadmap-planner/SKILL.md`

**Interfaces:**
- Consumes: Task 9's `scripts/gen_review_stub.py`.
- Produces: documentation only — no code interface.

- [ ] **Step 1: Add a row to the 阶段 3 file table**

Read the current file: `opsx-roadmap-planner/SKILL.md`.

In the "### 阶段 3 详细：产出四件套" section, the table currently ends with the `memo.md` row
(around line 215: `| \`memo.md\` (可选) | 讨论备忘，考古用 | \`references/memo-template.md\` |`).
Add one more row right after it:

```markdown
| `review.html` | 查看器 stub（浏览用，不是内容文件） | 跑 `scripts/gen_review_stub.py {name}`（不读模板，是脚本，四件套写完之后再跑） |
```

- [ ] **Step 2: Add the step to the tasks.md template snippet**

In the same file, the "## 2. 产出 roadmap 文档包" checklist block (around lines 181-186) currently ends at:

```markdown
- [ ] 2.5 (可选) 保留或生成 openspec/roadmaps/{name}/memo.md
```

Add:

```markdown
- [ ] 2.6 生成 openspec/roadmaps/{name}/review.html：跑
      `python3 ~/.skills/laodao-skills/opsx-roadmap-planner/scripts/gen_review_stub.py {name}`
      （若报错提示项目未铺设 review 工具，先跑 opsx-project-init init/update 再重试）
```

- [ ] **Step 3: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-roadmap-planner/SKILL.md
git commit -m "docs(opsx-roadmap-planner): wire gen_review_stub.py into the 阶段 3 file table and tasks.md template"
```

---

### Task 11: Update `opsx-project-init/SKILL.md`

**Files:**
- Modify: `opsx-project-init/SKILL.md`

**Interfaces:**
- Documentation only.

- [ ] **Step 1: Update the "铺设了什么" tree diagram**

Read the current file: `opsx-project-init/SKILL.md`.

The "## 铺设了什么" section (around lines 68-84) currently shows a tree ending at `CLAUDE.md / AGENTS.md`.
Add the review-tool files into the tree, right after the `changes/  specs/` line:

```markdown
├── changes/  specs/       ← 目录骨架
├── review.html            ← 文档查看器根入口（scope="" 全树导航）
├── serve.sh                ← 一行封装：cd 到 openspec/ 再起 python3 -m http.server
├── tools/                  ← engine.js + engine.css + vendor/marked.min.js + review-stub.html
│                             （review-stub.html 是模板，roadmap/change 目录的 review.html 由它生成）
```

- [ ] **Step 2: Document the second global hook**

The "## 注意" section's FF-0 bullet (around line 100) currently only describes `ff0-branch-guard.py`.
Add a new bullet right after it:

```markdown
- **change 目录自动补 review.html（全局第二个 hook）**：hook 脚本源在本 skill 的
  `assets/hooks/change-review-stub.py`，由 `init`/`update` 全局安装到 `~/.claude/hooks/` + 注册进
  `~/.claude/settings.json` 的 `PostToolUse.Bash`。`openspec new change <name>` 跑完后，若项目已铺设
  review 工具（`openspec/review.html` 存在），自动在新建的 `openspec/changes/<name>/` 下补一份
  `review.html`（scope 指向该目录），随 `openspec archive` 一起搬迁、无需重新生成。项目未铺设 review
  工具时静默跳过，不强迫铺设顺序。
```

- [ ] **Step 3: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add opsx-project-init/SKILL.md
git commit -m "docs(opsx-project-init): document review-tool distribution and the new PostToolUse hook"
```

---

### Task 12: End-to-end verification + version bump

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `VERSION`

**Interfaces:**
- None — this task verifies the whole feature works together against a real project, then records the release.

- [ ] **Step 1: Fresh `init` against a throwaway project directory**

```bash
mkdir -p /tmp/review-tool-e2e && cd /tmp/review-tool-e2e
git init -q
python3 /Users/cheneyzhao/.skills/laodao-skills/opsx-project-init/scripts/init.py init --root .
ls openspec/review.html openspec/serve.sh openspec/tools/engine.js openspec/tools/vendor/marked.min.js
```

Expected: all four paths print (exist), plus the script's own printed report shows both the bundle copy
and the review-tool copy lines, and `全局 hooks：` shows two entries (`ff0-branch-guard.py` and
`change-review-stub.py`), both ending in "已安装" or "脚本已最新"/"已注册".

- [ ] **Step 2: Confirm both global hooks are actually registered**

```bash
cat ~/.claude/settings.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(list(d.get('hooks',{}).keys()))"
```

Expected: includes both `PreToolUse` and `PostToolUse`.

- [ ] **Step 3: `update` mode is idempotent and doesn't duplicate**

```bash
cd /tmp/review-tool-e2e
python3 /Users/cheneyzhao/.skills/laodao-skills/opsx-project-init/scripts/init.py update --root .
python3 -c "
import json
d = json.load(open('/Users/cheneyzhao/.claude/settings.json'))
assert len(d['hooks']['PreToolUse']) == 1
assert len(d['hooks']['PostToolUse']) == 1
print('OK: no duplicate hook registrations after update')
"
```

Expected: prints `OK: no duplicate hook registrations after update`.

- [ ] **Step 4: Verify the archive-depth fix actually survives a simulated archive move**

```bash
cd /tmp/review-tool-e2e
mkdir -p openspec/changes/demo-change
python3 -c "
import sys
sys.path.insert(0, '/Users/cheneyzhao/.skills/laodao-skills/opsx-roadmap-planner/scripts')
" 
cp openspec/tools/review-stub.html /tmp/stub.html
python3 -c "
content = open('/tmp/stub.html').read().replace('__SCOPE__', 'changes/demo-change/')
open('openspec/changes/demo-change/review.html', 'w').write(content)
"
mkdir -p openspec/changes/archive
mv openspec/changes/demo-change openspec/changes/archive/2026-07-01-demo-change
grep -o 'href="/review.html"\|src="/tools/engine.js"' openspec/changes/archive/2026-07-01-demo-change/review.html
```

Expected: nothing printed by this particular grep against `review.html` itself, because those root-relative
references live in `review-stub.html`'s *rendered output when opened by a browser fetching `/tools/engine.js`
and `/tools/engine.css`*, not as literal strings inside the moved file needing correction — the real check is
that the file's `<link>`/`<script src>` attributes are `/tools/engine.css` and `/tools/engine.js` (root-relative,
unchanged by the `mv`):

```bash
grep -o 'href="/tools/engine.css"\|src="/tools/engine.js"' openspec/changes/archive/2026-07-01-demo-change/review.html
```

Expected: both lines print — confirming the moved file's asset references are still root-relative and
therefore still correct after the directory got one level deeper.

- [ ] **Step 5: Real browser walkthrough on the throwaway project (Playwright)**

```bash
cd /tmp/review-tool-e2e/openspec && bash serve.sh 8919 &
echo "PID=$!"
```

Using the Playwright MCP tools: navigate to `http://localhost:8919/review.html`, confirm the page loads
without console errors and the sidebar shows `changes/`, `tools/` (and whatever else exists in this
throwaway project). Then navigate to `http://localhost:8919/changes/archive/2026-07-01-demo-change/review.html`
directly, confirm it also loads without errors and its sidebar shows the "← 全部文档" back-link, and that
clicking it returns to `http://localhost:8919/review.html`.

Then: `kill %1` (or the printed PID), and clean up: `rm -rf /tmp/review-tool-e2e`.

- [ ] **Step 6: Update CHANGELOG.md and VERSION**

Read the current files: `CHANGELOG.md`, `VERSION`.

Modify `VERSION` — replace `1.7.0` with:

```
1.8.0
```

Modify `CHANGELOG.md` — add this entry at the very top, above the existing `## 1.7.0 — 2026-06-29` entry:

```markdown
## 1.8.0 — 2026-07-01

- `opsx-project-init` 新增 OpenSpec 文档 HTML Review 工具（零构建、离线可用）：
  - **根入口** `openspec/review.html` + `openspec/serve.sh`：一条 `bash openspec/serve.sh` 起本地
    静态服务器，浏览整个 `openspec/` 树；目录内容通过解析 Python `http.server` 自带的目录索引页
    动态发现（不打包清单，md 增删即时反映）；markdown 渲染内联 vendor 了 `marked.js`（离线可用，
    见 `opsx-project-init/assets/review-tool/tools/vendor/NOTICE.md`）；反引号包裹的
    `` `openspec/xxx.md` `` 路径自动转可点链接。
  - **`openspec/roadmaps/<name>/review.html`**：`opsx-roadmap-planner` 四件套生成完之后，跑
    `scripts/gen_review_stub.py {name}` 生成，scope 默认聚焦本目录。
  - **`openspec/changes/<name>/review.html`**：新增全局 PostToolUse hook
    `change-review-stub.py`（`ff0-branch-guard.py` 的姊妹篇，同样拦 `openspec new change <name>`
    这一条 CLI 命令，覆盖 `/opsx:new`/`/opsx:ff`/`/opsx:propose`/`/opsx:onboard` 全部入口），change
    目录建好后自动补一份，随 `openspec archive` 搬迁到 `changes/archive/` 无需重新生成。
  - 三处 stub 共用同一模板 + 同一份共享引擎（`tools/engine.js`/`engine.css`），全部使用
    **根相对路径**引用资源与"回根"链接——不管目录搬多深，链接都不断。
  - `ensure_global_hook()` 从单一硬编码 hook 重构为数据驱动的多 hook 安装器（`HOOKS` 列表），
    向后兼容既有的 ff0 hook 注册状态。
  - 设计过程详见 `opsx-project-init/memo-review-html-tool.md`。
```

- [ ] **Step 7: Commit**

```bash
cd /Users/cheneyzhao/.skills/laodao-skills
git add CHANGELOG.md VERSION
git commit -m "chore: bump version to 1.8.0 for the OpenSpec review-html tool"
```

---

## Self-Review Notes

**Spec coverage** — all five pieces from the memo are covered: shared engine (Tasks 1/3/4), vendored
markdown renderer (Task 2), root shell + serve.sh (Task 5, generated by Task 6), `opsx-project-init`
distribution (Task 6), `opsx-roadmap-planner` wiring (Tasks 9/10), the new PostToolUse hook + hook-installer
generalization (Tasks 7/8), both `SKILL.md` updates (Tasks 10/11), archive-depth root-relative-path fix
(Global Constraints + verified in Task 12 Step 4), directory-listing parsing verified against the real
Python 3.9.6 output captured during exploration (Task 1's test fixture uses that exact captured HTML).

**Rejected alternatives intentionally NOT re-litigated here** (docsify/mkdocs, File System Access API,
static manifest JSON, attaching to spec-review/impl-review instead of a hook) — see
`opsx-project-init/memo-review-html-tool.md` for why; this plan only implements the converged design.

**Known follow-ups not in this plan** (acceptable gaps, not blocking): exact `marked.js` version is
resolved at fetch time rather than pre-pinned in this document (Task 2); no automated test for the DOM
glue itself, only Playwright manual verification (Task 3) — acceptable since the underlying logic it calls
(Task 1) is unit tested and the glue is thin; no UI polish pass (responsive/mobile, dark mode) — out of
scope for a first working version.
