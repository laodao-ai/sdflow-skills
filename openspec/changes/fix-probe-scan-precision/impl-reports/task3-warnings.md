# Task 3 实现报告：告警语义改写（stale_shadow_warnings + maintain_scan）

**Blocked-by:** 2（已完成，见 task2-resolver-init.md）
**R-ID:** R4（spec-workflow MODIFIED 残留副本须告警）、R5（maintain-scan MODIFIED）

## 改动范围

| 文件 | 改动 |
|---|---|
| `sdflow-init/scripts/init.py` | `stale_shadow_warnings()`：判据扩员 + 新文案 |
| `sdflow-maintain/scripts/maintain_scan.py` | `scan_stale_shadow()`：同款判据扩员 + 同款新文案 |
| `sdflow-init/tests/test_init.py` | `TestStaleShadowWarnings` 新增/改写用例 + `TestInitAlsoWarnsShadow` 断言更新 |
| `sdflow-maintain/tests/test_maintain_scan.py` | `test_stale_shadow_only_tools_*` 断言反转 + 新增判据扩员/文案双断言用例 |

## 4.1 判据扩员 + 新文案

`RULE_MARKERS = ("workflow.md", "spec-checklists", "code-checklists")` 保持不动（被
`test_marker_consistency.py::test_rule_markers_equal` 机验跨脚本相等，不可改）。新增
`DEAD_RESIDUAL_MARKERS = RULE_MARKERS + ("tools", "lens-metric-contract.md")`，
`stale_shadow_warnings()` / `scan_stale_shadow()` 均改用扩员后的元组做检测。

新文案（两处 warns.append 共用 `_STALE_SHADOW_PRECONDITION` 常量）：

```
⚠ openspec/workflow/ 残留死件（<命中项>）：若刚 git pull 还没跑 bash setup.sh，先跑 setup 再判断
（部署窗口内旧 resolver 的仓内优先步可能仍生效），此后这些副本对评审已无生效路径（resolver 不再读
仓内副本）。删 = 清理死件（推荐）：`rm -rf openspec/workflow/<项1> openspec/workflow/<项2> ...`；
留 = 无害但无用
```

- 带前置条件（部署窗口告警）而非无条件绝对断言——满足 `MUST NOT 输出无条件的"已无任何生效路径"`。
- 可复制删除命令按实际命中项动态拼接 `rm -rf openspec/workflow/<found1> ...`，而非静态写死示例路径。
- MUST NOT 新增一次性自动清删代码——本次改动只改文案与检测范围，未新增任何删除动作。

## 4.2 checkpoint 孤儿告警的 pin 措辞清理

旧文案「若保留本地 workflow.md 副本（pin）且其仍引用仓内路径 → 勿删」（pin 语义已取消、该条件
不再成立）替换为与死件告警同款的前置条件 + 死件表述：

```
⚠ hack/checkpoint-commit.sh 为旧版仓内副本（checkpoint 已全局化 → ~/.sdflow/hack/）：若刚 git
pull 还没跑 bash setup.sh，先跑 setup 再判断（部署窗口内旧 resolver 的仓内优先步可能仍生效），
此后本副本已无生效路径。删 = 清理死件（推荐）：`rm -f hack/checkpoint-commit.sh`；留 = 无害但无用
```

## 4.3 sdflow-maintain 扫描同步 + 断言反转

`sdflow-maintain/scripts/maintain_scan.py::scan_stale_shadow()` 与 init.py 侧同构改写
（同款判据、同款文案生成逻辑，语义等价——`openspec/specs/maintain-scan/spec.md` 已注明文案漂移
为已知残差 defer，不要求逐字相同）。

`test_maintain_scan.py::test_stale_shadow_only_tools_clean` **断言反转**为
`test_stale_shadow_only_tools_now_reports_dead_file`：原用例在 tools-only 残留（无
RULE_MARKERS 规则本体）场景断言"陈旧遮蔽节存在但无残留规则本体"（即判干净）；新判据下
tools/ 本身即死件，改为断言该场景 **SHALL** 报「死件」+「tools」。此用例在旧实现（未扩员的
`RULE_MARKERS`）上会失败，是判据扩员的反向锚。

同批新增 `test_stale_shadow_lens_metric_contract_now_reports_dead_file`（`lens-metric-contract.md`
残留同为死件的正向覆盖）。

## 4.4 文案测试正反双断言

`sdflow-init/tests/test_init.py::TestStaleShadowWarnings::test_message_wording_positive_and_negative`
与 `sdflow-maintain/tests/test_maintain_scan.py::test_stale_shadow_message_wording_positive_and_negative`
均校验：

- **负断言**：`"显式 pin"` 不在文案中、`"遮蔽全局"` 不在文案中（防「旧文案叠加新词也通过」的假绿）。
- **正断言**：含 `"死件"` 关键词、含 `"bash setup.sh"` 前置条件提示、含 `"rm -rf"` 与 `"rm -f"`
  可复制删除命令。

此外补充两条判据扩员的正向锚（`sdflow-init` 侧）：`test_tools_only_residual_now_warns`、
`test_lens_metric_contract_residual_now_warns`，与 `sdflow-maintain` 侧的
`test_stale_shadow_lens_metric_contract_now_reports_dead_file` 对称。

`test_clean_consumer_no_warnings`（原用例用「只建空 tools/ 目录」代表"干净"消费仓，判据扩员后
该前提不再成立——tools/ 目录本身即死件）改写为 `test_truly_clean_consumer_no_warnings`
（真正干净：`openspec/workflow/` 下无任何标记文件/目录），并保留一条同名 `test_clean_consumer_no_warnings`
覆盖"仅建 `openspec/` 无 `workflow/` 子目录"的更早期场景（fresh 安装前置状态）。

`TestInitAlsoWarnsShadow::test_init_on_legacy_repo_warns_shadow` 原断言 `"遮蔽" in out`，
随文案改写同步更新为 `"死件" in out`（发现于第一轮全量回归，非任务清单原列项，按「同一被改动
产出物的消费者」处置，非范围外加宽）。

## TDD 记录（red→green）

1. 先静态读取 `RULE_MARKERS`/`stale_shadow_warnings`/`scan_stale_shadow` 现状与相关测试，确认
   `test_stale_shadow_only_tools_clean`、`test_clean_consumer_no_warnings` 在扩员后必红（判据
   扩员的反向锚前提）。
2. 落地 `init.py` + `maintain_scan.py` 实现改动。
3. 改写/新增测试后运行：
   - `sdflow-init/tests/test_init.py -k StaleShadow` → 7 passed
   - `sdflow-maintain/tests/test_maintain_scan.py -k stale_shadow` → 6 passed
   - `sdflow-maintain/tests/test_marker_consistency.py` → 3 passed（`RULE_MARKERS` 未改，跨脚本
     一致性守卫仍绿）
4. 全量回归 `sdflow-init/tests/ sdflow-maintain/tests/`：第一轮命中 1 处遗漏
   （`TestInitAlsoWarnsShadow::test_init_on_legacy_repo_warns_shadow` 断言旧字样"遮蔽"），
   修正后第二轮：**836 passed, 4 skipped**（skip 为既有环境相关跳过，非本次改动引入）。
5. 连带回归 `hack/tests/`（跨脚本一致性门所在目录）：**380 passed**，无涟漪。

## 测试覆盖图对照（tasks.md TG-18 相关行）

| code path | 用例 | 结果 |
|---|---|---|
| 告警新文案 + 判据扩员 | `sdflow-init/tests/test_init.py::TestStaleShadowWarnings::test_message_wording_positive_and_negative` | ✅ pass，反向锚生效（旧文案叠加新词会被"不含显式 pin/遮蔽全局"拦下） |
| maintain 判据扩员反转 | `sdflow-maintain/tests/test_maintain_scan.py::test_stale_shadow_only_tools_now_reports_dead_file` | ✅ pass |
| maintain 文案双断言 | `sdflow-maintain/tests/test_maintain_scan.py::test_stale_shadow_message_wording_positive_and_negative` | ✅ pass |

## 范围边界（诚实报告）

- 未触碰 `sdflow-init/scripts/init.py` 之外任何 `RULE_MARKERS` 定义（跨脚本一致性守卫要求
  `RULE_MARKERS` 逐字相等，本次新增独立的 `DEAD_RESIDUAL_MARKERS` 满足扩员需求且不破坏该守卫）。
- 未处理 `openspec/adr/*`、`CLAUDE.md`、`AGENTS.md`、`openspec/specs/*`、`docs/*` 中残留的
  "遮蔽全局"/"显式 pin" 历史措辞——这些属 tasks.md task 6.4/6.5/6.7/6.8/7.6（概念词表 sweep）
  范围，非本 task 3（`stale_shadow_warnings` + `maintain_scan` 判据与文案本体）范围。
- 未触碰 `openspec/changes/archive/**` 下的历史归档文本（旧文案的历史快照，按 tasks.md 7.6
  归零词表的豁免清单本就排除归档目录）。

## 完成状态

4.1 / 4.2 / 4.3 / 4.4 全部完成。`/usr/bin/python3 -m pytest sdflow-init/tests/ sdflow-maintain/tests/`
836 passed / 4 skipped，`hack/tests/` 380 passed，无回归。

未勾选 tasks.md 复选框、未打 checkpoint 标签——按信号权威表，该动作留给双轴审后的执行模式。
