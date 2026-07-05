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
    (_match, path) => {
      // The server root is `openspec/` itself, so the href must strip the
      // redundant "openspec/" prefix (else it 404s at .../openspec/openspec/...).
      // The visible text keeps the full prose-style path for readability.
      const hrefPath = path.replace(/^openspec\//, '');
      return `<a href="/${hrefPath}" class="auto-link">${path}</a>`;
    }
  );
}

function resolveLink(href, baseUrl) {
  return new URL(href, baseUrl).toString();
}

function isMarkdownPath(path) {
  return /\.md$/i.test(path);
}

function parentOf(dirPath) {
  // dirPath always ends with '/' (this codebase's convention for directory paths),
  // e.g. '/changes/archive/foo/' -> '/changes/archive/'; '/changes/' -> '/'; '/' -> null.
  if (dirPath === '/') return null;
  const trimmed = dirPath.slice(0, -1);
  const idx = trimmed.lastIndexOf('/');
  return trimmed.slice(0, idx + 1);
}

function normalizeProjectName(projectName) {
  // `projectName` comes from `window.__OPENSPEC_PROJECT_NAME__`, baked into review-stub.html
  // at generation time (see init.py's copy_review_tool). It can be
  // missing entirely (undefined, e.g. an old template copy predating this feature), empty, or
  // — in the rare case someone serves the raw unrendered template — the literal, unsubstituted
  // `__PROJECT_NAME__` token. All three cases must normalize to '' so every caller (path bar,
  // tab title, ...) shares one fallback rule and none of them ever display
  // "undefined"/"null"/the raw placeholder token.
  const name = (projectName || '').trim();
  if (!name || name === '__PROJECT_NAME__') return '';
  return name;
}

function formatPathBar(projectName, dirPath) {
  const name = normalizeProjectName(projectName);
  if (!name) {
    return `📂 ${dirPath}`;
  }
  return `📂 ${name} · ${dirPath}`;
}

function formatTabTitle(projectName, path) {
  // Browser tab titles get truncated (with an end-of-string ellipsis) long before the
  // in-page path bar does, so — unlike a document read top-to-bottom — the FRONT of this
  // string is what stays visible when several projects' review tools are open in narrow
  // tabs. Put the project name first (same order as formatPathBar's "name · path") so a
  // truncated tab still identifies which project it belongs to.
  const name = normalizeProjectName(projectName);
  if (!name) {
    return path;
  }
  return `${name} · ${path}`;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    parseDirectoryListing,
    linkifyBacktickPaths,
    resolveLink,
    isMarkdownPath,
    parentOf,
    formatPathBar,
    formatTabTitle,
  };
}

// ---- DOM glue (browser-only; the `typeof document` guard keeps this inert under Node) ----

if (typeof document !== 'undefined') {
  (function () {
    const initialDir = window.location.pathname.replace(/[^/]*$/, '');
    // Baked into review-stub.html at generation time (see formatPathBar's comment above for
    // why this is safe to bake in, unlike the removed __SCOPE__ mechanism). `|| ''` covers the
    // undefined case (old template copy predating this feature); formatPathBar covers the rest.
    const projectName = window.__OPENSPEC_PROJECT_NAME__ || '';
    // The shell page itself never navigates (history is hash-based, see `navigate`
    // below), so `window.location.pathname` always stays at the shell's own path.
    // Relative markdown links must instead be resolved against whatever doc/dir is
    // CURRENTLY DISPLAYED — track that explicitly here, updated on every successful
    // navigation.
    let currentPath = initialDir;

    const app = document.getElementById('app');
    const sidebar = document.createElement('div');
    sidebar.id = 'sidebar';
    const content = document.createElement('div');
    content.id = 'content';
    // `pathBar` is a persistent, always-visible "you are here" indicator —
    // separate from `contentBody` (where loadDir/loadDoc write their rendered
    // output) so re-rendering a doc/dir never wipes it out. Appended before
    // `contentBody` so it sits at the top of #content (sticky, via CSS).
    const pathBar = document.createElement('div');
    pathBar.id = 'path-bar';
    const contentBody = document.createElement('div');
    contentBody.id = 'content-body';
    content.appendChild(pathBar);
    content.appendChild(contentBody);
    app.appendChild(sidebar);
    app.appendChild(content);

    function escapeHtml(s) {
      return s.replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
      }[c]));
    }

    // Rendered docs are our own openspec/ markdown, but escape any raw HTML tokens
    // (marked otherwise passes them through verbatim) so a stray `<script>` or
    // `<img onerror=...>` pasted into a doc can't execute in this local viewer.
    if (window.marked) {
      const renderer = new window.marked.Renderer();
      renderer.html = (html) => escapeHtml(html);
      window.marked.setOptions({ renderer });
    }

    async function fetchText(path) {
      const res = await fetch(path);
      if (!res.ok) throw new Error(`fetch failed: ${path} (${res.status})`);
      return res.text();
    }

    async function loadSidebar(dirPath) {
      // Same directory-path value the sidebar itself draws from — surface it
      // in the persistent path bar too, so "where am I" is visible without
      // relying on the sidebar's home/up toolbar (which is hidden at root).
      pathBar.textContent = formatPathBar(projectName, dirPath);
      const html = await fetchText(dirPath);
      const entries = parseDirectoryListing(html)
        .filter((e) => e.isDir || isMarkdownPath(e.name))
        .sort((a, b) => (a.isDir === b.isDir ? a.name.localeCompare(b.name) : a.isDir ? -1 : 1));
      sidebar.innerHTML = '';
      if (dirPath !== '/') {
        const toolbar = document.createElement('div');
        toolbar.className = 'sidebar-toolbar';

        const home = document.createElement('a');
        home.href = '/';
        home.className = 'nav-link home-link';
        home.textContent = '🏠 首页';
        toolbar.appendChild(home);

        const parent = parentOf(dirPath);
        if (parent) {
          const up = document.createElement('a');
          up.href = parent;
          up.className = 'nav-link up-link';
          up.textContent = '↑ 上级目录';
          toolbar.appendChild(up);
        }

        sidebar.appendChild(toolbar);
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
      contentBody.innerHTML = `<p class="hint">目录：${escapeHtml(path)}<br>请选择左侧的文档。</p>`;
      document.title = formatTabTitle(projectName, path);
    }

    async function loadDoc(path) {
      const md = await fetchText(path);
      const rendered = window.marked ? window.marked.parse(md) : `<pre>${escapeHtml(md)}</pre>`;
      contentBody.innerHTML = linkifyBacktickPaths(rendered);
      document.title = formatTabTitle(projectName, path);
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
        currentPath = path;
        if (push) history.pushState({ path }, '', `#${path}`);
      } catch (err) {
        contentBody.innerHTML = `<p class="error">加载失败：${escapeHtml(path)}</p>`;
      }
    }

    function onLinkClick(ev) {
      const a = ev.target.closest('a');
      if (!a) return;
      const href = a.getAttribute('href');
      if (!href) return;
      // Only intercept links to markdown docs or directory listings — everything
      // else (images, `/workflow/tools/engine.js`, same-page `#fragment` anchors, etc.)
      // should fall through to native browser handling. Checking the raw href
      // (not the resolved URL) means a bare `#foo` fragment is correctly excluded
      // here too, since it's neither a `.md` path nor directory-shaped.
      if (!isMarkdownPath(href) && !href.endsWith('/')) return;
      // Resolve against the CURRENTLY DISPLAYED doc/dir, not `window.location.href`
      // — the shell's own location never changes (hash-based history), so resolving
      // against it would break every relative link in a doc that isn't sitting next
      // to the shell file.
      const base = new URL(currentPath, window.location.origin).toString();
      const resolved = resolveLink(href, base);
      const url = new URL(resolved);
      // resolveLink always returns an absolute URL (even for same-origin sidebar
      // links), so a naive `startsWith('http://')` check can't distinguish "real"
      // external links from internal ones — compare origins instead.
      if (url.origin !== window.location.origin) return;
      ev.preventDefault();
      navigate(url.pathname, true);
    }

    document.body.addEventListener('click', onLinkClick);
    window.addEventListener('popstate', (ev) => {
      const path = (ev.state && ev.state.path) || initialDir;
      navigate(path, false);
    });

    // Root entry (this shell's own directory, not a roadmap/change sub-directory
    // entry): greet the visitor with openspec/INDEX.md's rendered content instead
    // of the generic "选择左侧文档" hint. `loadDoc` already populates the sidebar
    // with the containing directory's listing as a side effect (via its own
    // `loadSidebar(dir)` call), so the root directory listing still shows up
    // exactly as it does today — this is additive, not a replacement.
    // If INDEX.md is missing or fails to fetch (e.g. the project hasn't run
    // sdflow-init recently enough to have one, or it was deleted), that
    // must not surface as a scary "加载失败" error on first load — fall back to
    // the plain directory-listing view instead.
    async function bootstrap() {
      if (initialDir === '/') {
        try {
          await loadDoc('/INDEX.md');
          currentPath = '/INDEX.md';
          return;
        } catch (err) {
          // fall through to the plain root directory listing below
        }
      }
      await navigate(initialDir, false);
    }

    bootstrap();
  })();
}
