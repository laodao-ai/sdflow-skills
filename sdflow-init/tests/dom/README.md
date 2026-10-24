# 评审页 DOM 回归测试

用 `render-review-page.py` 产出真实页面，在 Playwright 的 Chromium 里以 `file://` 打开。
测试全程不访问网络：mermaid 的 CDN 地址由路由换成 `node_modules/mermaid/dist/mermaid.min.js`。
Playwright 只用于测试，不进任何运行时代码。

## 覆盖范围

| 主题 | 对应 R-ID |
|---|---|
| 渲染与安全、链接与图片白名单、CSP | RVP-02 |
| 划选暂存、复制 | RVP-04、RVP-05 |
| 已落盘意见显示（纯文本）、与暂存意见合并 | RVP-11、RVP-19 |
| 页内标题锚点；mermaid 图内划选；键盘与读屏 | RVP-12、RVP-13、RVP-14 |
| 回显端到端（粘回后重新生成） | RVP-18 |
| 跨粗体、跨列表项的分段高亮；定位与删除覆盖全部分段；端点落在元素上；超过 500 码点 | RVP-20 |
| frontmatter 元数据框：不进目录、不可划选、没有闭合行、BOM + CRLF、以分隔线开头的正文 | RVP-21 |
| 页头「生成于 X · 第 N 版」；数据块损坏时显示「无法读取」 | RVP-22 |
| 页尾「意见与处理记录」「修改日志」：顺序、目录项、不可划选、已采纳意见原文已改 | RVP-23、RVP-25 |
| 意见栏的处理类别、编号与说明；处置说明含 `<img onerror>` 不执行 | RVP-25 |

处置类用例用 `record-review-disposition.py` 写入 `review-notes.md` 再重新生成页面，与真实流程同一入口。
修改日志类用例固定 `SOURCE_DATE_EPOCH=1700000000`、`TZ=UTC`，时间文字因此可逐字比对。
纯函数（`splitFrontmatter`、`parseRevisions`、`parseDispositions`、`headerText`、`dispositionText` 等）
由 `sdflow-init/tests/review_page_pure.test.js` 覆盖：`node --test sdflow-init/tests/review_page_pure.test.js`。

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
