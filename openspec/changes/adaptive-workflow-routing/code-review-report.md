<!-- sdflow:step1-broad-review v1 mode="simulated" -->

# code-review 报告 — adaptive-workflow-routing

> **诚实声明（反静默）**：本轮为**聚焦 code-review**——1 个 fresh 冷镜（adversarial，claude）审新增判器 `trivial_shape.py` + 接入。Step1 gstack/review 与 outside-voice 未单独跑（proportionality：~200 行判器 + 34 pytest 覆盖 spec 全 scenario；改的是判器脚本非产品逻辑）。`broad` 锚 mode="simulated"。dogfood：判器判本 change **NOT_EXEMPT**（改 SKILL.md/判器自身=行为面路径）→ 本 change 按自己规则该受审，自洽。

## 命中范围
- 对象：`sdflow-init/assets/workflow/tools/trivial_shape.py`（新判器）+ `test_trivial_shape.py` + `sdflow-code-review/SKILL.md` Step2 接入 + `spec-workflow` delta。
- 冷镜聚焦：**危险方向**（logic 误判 EXEMPT = 唯一会真放过 bug 的失效）。

## Findings（置信 ≥80，全部确认 + 已修 [impl-review-fix]）

| # | 严重 | 问题 | 危险方向? | 修复 |
|---|---|---|---|---|
| **F1** | 高 | 裸 `*.txt` 免 `requirements.txt`/`runtime.txt`（依赖 pin=行为） | ✔ logic→EXEMPT | doc 扩展名锚定 + 裸 *.txt 落 NOT；仅 docs/ 下 .txt 算文档 |
| **F2** | 中 | `docs/*` 免 `docs/conf.py` 等源码 | ✔ | docs/ 下按扩展名，.py 落代码判定 |
| **F3** | 中 | `README*` basename 前缀误捕 `README_gen.py` | ✔ | 精确 stem（README/CHANGELOG/LICENSE/NOTICE）+ 扩展锚定 |
| **F4** | 中低 | chmod mode-only → 空 lines vacuous EXEMPT | ✔ | parse 记 mode_changed + 空内容守卫，均落 NOT |
| **F5** | 中低 | 内容行 `-- `/`++ ` 撞 header guard 被丢 → 或致误 EXEMPT | ✔ | parse_diff 改 hunk-state 机（@@ 后 +/- 一律内容） |
| **F6** | 低 | tests/ 新增仅排 conftest，漏 `__init__.py` import 副作用 | 残余 | 补排 `__init__.py` |
| **F7** | 低 | copy-detection（`copy from/to`）落内容判定 | ✔ | copy 同 rename → NOT |

冷镜同时确认无误的正确面（未列爆点）：hunk-header 函数上下文/上下文行忽略/多 hunk 隔离/删除逻辑文件/二进制/block-comment/rename/empty-diff/`x=1 # note`/SKILL 接入退出码一致——均正确。

## 修复 / defer 台账
- **自动修 7 项 [impl-review-fix]**（F1-F7 全修，判器重写 doc 判定为扩展名锚定的 `is_doc_file` + parse_diff hunk-state 机 + mode/copy/空内容守卫 + `__init__.py` 排除）。
- **补洞测试 12 例**（F1-F7 各正反例）：pytest **34 passed**（原 22 + 新 12）。
- **spec 同步收窄**：`spec-workflow` delta ① 措辞随 F1/F2/F3 更新（doc 扩展名锚定、裸 *.txt 非文档、docs/ 源码非文档）。
- defer 0。

## 度量锚（lens-metric，config metrics.enabled=true）

<!-- sdflow:step1-broad-review v1 mode="simulated" 见顶部诚实声明 -->
<!-- sdflow:hr-tg v1 hit="none" evidence="判器脚本+SKILL接入,不命中现 HR-TG 成员(TG-04/06/07/08/09/16/17/26 皆产品码风险)" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="7" 采纳="7" 裁掉="0" defer="0" 独立="7" sev="致0/高1/中2/低4" -->

> 数值一致性 = 主 session 信任边界、非机械门。outside-voice/domain/history 本聚焦轮未跑（proportionality，已声明）。

## 结论
7 个危险方向 finding 全确认全修、34 pytest 全绿、dogfood 自洽。**建议进 /sdflow-done**。

<!-- ship-gate: code-review=pass -->
