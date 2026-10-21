# 评审页 DOM 回归测试

用 `render-review-page.py` 产出真实页面，在 Playwright 的 Chromium 里以 `file://` 打开。
测试全程不访问网络：mermaid 的 CDN 地址由路由换成 `node_modules/mermaid/dist/mermaid.min.js`。
Playwright 只用于测试，不进任何运行时代码。

## 安装

三种缺依赖情形，各有一条命令：

| 缺什么 | 命令 |
|---|---|
| node | 安装 Node 20 或更新版本 |
| `node_modules`（playwright、mermaid） | `cd sdflow-init/tests/dom && npm ci` |
| Chromium 浏览器 | `cd sdflow-init/tests/dom && npx playwright install chromium` |

依赖版本钉在 `package.json`（`playwright` 1.64.1、`mermaid` 12.2.0），`package-lock.json` 提交入库。
`node_modules/` 已被仓根 `.gitignore` 忽略。

## 运行

```bash
pytest -rs sdflow-init/tests/test_review_page_dom.py
# 或直接跑 node（node 24 下必须传文件路径，传目录会判失败）
node --test sdflow-init/tests/dom/review_page_dom.test.js
```

本地缺依赖时 pytest 显示为 skip。裸跑 `pytest` 只显示 `s`，要加 `-rs` 才打印缺什么和修复命令。

## `SDFLOW_REQUIRE_DOM`

- 未设置：缺依赖则 skip。
- `SDFLOW_REQUIRE_DOM=1`：缺依赖则 FAIL。CI 的「Gate — 评审页 DOM 回归测试」一步设置它，防止依赖没装好时以 skip 通过。
