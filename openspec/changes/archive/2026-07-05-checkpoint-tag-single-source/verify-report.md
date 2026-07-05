# Verify Report — checkpoint-tag-single-source

- 日期：2026-07-05
- Change：`checkpoint-tag-single-source`

## 结论：PASS

<!-- ship-gate: verify=PASS -->

证据锚点摘要：`python3 -m pytest sdflow-ship/tests/test_producer_parser_contract.py -v` → 8 passed（真实脚本产出 subject → 真实 `ship_gate.TAG_RE` 解析）；仓级 `python3 -m pytest -q` → 350 passed 无回归。

## 逐需求核对表

| 需求/任务 | 代码出处(文件:行/测试名) | 状态 |
|---|---|---|
| 契约测试 import 真实 `TAG_RE`（D4，无副作用） | `test_producer_parser_contract.py:17-21`（`importlib.util.spec_from_file_location` 按文件路径加载 `sdflow-ship/scripts/ship_gate.py`，非 sys.path 注入）；TAG_RE 源 `ship_gate.py:231` | ✅ 实现（已裁决机制精化：D4 文本写"sys.path 注入"，实现改用 importlib 保"import 无副作用/消全局污染"意图，见 code-review-report） |
| 集成正例（命名空间）：真调 `checkpoint-commit.sh demo:task1-slug` → git log subject → 断言 match + `group(1),group(2)==("demo","1")` | `test_namespaced_subject_matches_and_captures`（:36-41），真调 `subprocess.run(["bash", SCRIPT, ...])` + 真 `git log -1 --format=%s`（`run_producer` :24-33） | ✅ 实现 |
| 集成正例（裸格式）：真调 `checkpoint-commit.sh task1-slug` → 断言 match + `group(1) is None`、`group(2)=="1"` | `test_bare_subject_matches_with_null_namespace`（:44-50） | ✅ 实现 |
| kebab 多位号正例（真实标签形态 `checkpoint-tag-single-source:task12-slug`） | `test_kebab_namespace_multidigit_captures`（:53-62），断言 `("checkpoint-tag-single-source","12")` | ✅ 实现（DF7 code-voice 盲区补强） |
| 负例矩阵 ≥ D2 三类 MUST（无尾dash / 大写ns / 空号或前导符号）逐条 `match is None` | `test_tag_re_rejects_relaxations` 参数化（:69-82）：`task1slug`(无尾dash)、`DEMO:task1-`(大写ns)、`task-1-`(号位空/前导符号) | ✅ 实现（D2 三类全覆盖） |
| 负例扩展（字母加宽 `taskab-` + 空ns `:task1-`） | 同上 `NEGATIVE_CASES` :73-74 | ✅ 实现 |
| 集成用例定位脚本用仓根相对路径（勿硬编码绝对） | `test:9-10` `REPO = Path(__file__).resolve().parents[2]` + `parents[1]` 定位 gate（:17） | ✅ 实现 |
| 跑 `pytest sdflow-ship/tests/` 全绿（含既有 `test_workflow_authority.py` 不变） | 仓级 350 passed；SKILL.md/workflow.md/ship_gate.py 未改（TAG_RE `ship_gate.py:231` 与 producer `checkpoint-commit.sh:46` 逐字不变） | ✅ 实现 |
| 仓级 `pytest` 无回归 | `python3 -m pytest -q` → 350 passed in 24.07s | ✅ 实现 |

## 缺口清单

- 核心缺口（FAIL 项）：无。producer→parser 集成绑定（真脚本→真 TAG_RE）与 D2 负例矩阵三类 MUST 均已机械实现并全绿。
- Minor 缺口：
  - design D4 文本"sys.path 注入" vs 实现 `importlib.util.spec_from_file_location` —— 已裁决的机制精化（保 D4 意图"import TAG_RE 无副作用"、消全局污染），非缺口，以代码实况为准。
  - 无其他 Minor/deferred 项。本 change 无 `assets/` 权威源改动，无需 `sdflow-init update` / 重跑 `setup.sh`（仅加测试文件）。

## 关键锚点

- 契约测试文件：`sdflow-ship/tests/test_producer_parser_contract.py`（8 用例全绿）
- parser 真相源：`sdflow-ship/scripts/ship_gate.py:231` — `TAG_RE = re.compile(r"checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-")`
- producer 真相源：`sdflow-init/assets/hack/checkpoint-commit.sh:46` — `subject="checkpoint($step): $desc"`
- 测试新增 commit：`8c868fa`
