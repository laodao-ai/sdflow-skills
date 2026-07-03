# Vendored: marked.js

- Source: https://unpkg.com/marked@9/marked.min.js (CDN fell back due to SSL; v9.1.6 has traditional UMD)
- Fetched: 2026-07-01
- Version banner (first bytes of the file): 
  ```
  /**
   * marked v9.1.6 - a markdown parser
   * Copyright (c) 2011-2023, Christopher Jeffrey. (MIT Licensed)
   * https://gith
  ```
- License: MIT — https://github.com/markedjs/marked/blob/master/LICENSE.md

Vendored (not loaded from a CDN) so the review tool works fully offline — this project is
local-first by design, the review tool shouldn't be the one thing that needs network access.
To upgrade: fetch from https://unpkg.com/marked@VERSION/marked.min.js and re-run `opsx-project-init update`
on every project that uses this tool.
