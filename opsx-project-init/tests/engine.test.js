const test = require('node:test');
const assert = require('node:assert/strict');
const {
  parseDirectoryListing,
  linkifyBacktickPaths,
  resolveLink,
  isMarkdownPath,
  parentOf,
  formatPathBar,
  formatTabTitle,
} = require('../assets/workflow/tools/engine.js');

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
    'See <a href="/CONTEXT.md" class="auto-link">openspec/CONTEXT.md</a> for details.'
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

test('parentOf: nested change directory goes up one level', () => {
  assert.equal(parentOf('/changes/archive/2026-07-01-foo/'), '/changes/archive/');
});

test('parentOf: top-level directory goes up to root', () => {
  assert.equal(parentOf('/changes/'), '/');
});

test('parentOf: root has no parent', () => {
  assert.equal(parentOf('/'), null);
});

test('formatPathBar: includes project name alongside directory path when present', () => {
  assert.equal(formatPathBar('mqtt-console', '/'), '📂 mqtt-console · /');
  assert.equal(
    formatPathBar('mqtt-console', '/roadmaps/mqtt-console/'),
    '📂 mqtt-console · /roadmaps/mqtt-console/'
  );
});

test('formatPathBar: falls back to directory-only when project name is empty string', () => {
  assert.equal(formatPathBar('', '/'), '📂 /');
});

test('formatPathBar: falls back to directory-only when project name is undefined (old template copy)', () => {
  assert.equal(formatPathBar(undefined, '/'), '📂 /');
});

test('formatPathBar: falls back to directory-only when project name is the unsubstituted placeholder token', () => {
  assert.equal(formatPathBar('__PROJECT_NAME__', '/roadmaps/'), '📂 /roadmaps/');
});

test('formatTabTitle: includes project name alongside path when present', () => {
  assert.equal(formatTabTitle('mqtt-console', '/'), 'mqtt-console · /');
  assert.equal(
    formatTabTitle('mqtt-console', '/roadmaps/mqtt-console/'),
    'mqtt-console · /roadmaps/mqtt-console/'
  );
});

test('formatTabTitle: falls back to path-only when project name is empty string', () => {
  assert.equal(formatTabTitle('', '/'), '/');
});

test('formatTabTitle: falls back to path-only when project name is undefined (old template copy)', () => {
  assert.equal(formatTabTitle(undefined, '/'), '/');
});

test('formatTabTitle: falls back to path-only when project name is the unsubstituted placeholder token', () => {
  assert.equal(formatTabTitle('__PROJECT_NAME__', '/roadmaps/'), '/roadmaps/');
});
