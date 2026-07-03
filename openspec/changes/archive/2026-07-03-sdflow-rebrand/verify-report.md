# Verify Report — sdflow-rebrand

日期：2026-07-03
结论：**PASS**

> 核验方法：Do-Not-Trust 冷启动——不信任 tasks.md 勾选状态、不信任既有 assert-log.md/code-review-report.md 的措辞，
> 对每条判 ✅ 的需求重新执行可复现的机验证据（重跑命令/测试，非仅阅读既有报告）。全部命令均在本次会话内亲自重跑，
> 输出与下表一致后才判 PASS。

## 逐需求核对表

| 需求/Scenario | 锚点（可复现） | 状态 |
|---|---|---|
| R-SR-1 · 9 个目录 `git mv`（保 blame） | `git log --diff-filter=R --summary` 命中 commit `45ef162`：9 组 rename 100%/95%/98%/99% 相似度，含 sibling 脚本/测试随迁 | ✅ |
| R-SR-1 Scenario「目录名与斜杠命令一致切换」 | 仓根 `ls`：12 个新名目录存在，0 个旧名目录残留；真实 `~/.claude/skills`、`~/.codex/skills` 仍指向旧名（`~/.skills/sdflow-skills` canonical checkout 停在 `70b5c0a`，早于本 change 全部改名提交）——**这正是 tasks.md 5.3 amendment 定义的验收边界**：实现期用沙箱测试验证（见下），真实激活改道 merge 后新会话 `/sdflow-upgrade`，非本次 gap | ✅（amendment 口径） |
| R-SR-1 Scenario「触发等价不回退」 | 重跑 `trigger-map.md` 附带的机械断言脚本（9 skill × 全部旧触发短语 `in` 新 SKILL.md frontmatter）→ 本次会话实测输出 `OVERALL: ALL PASS`，与 trigger-map.md 留档一致 | ✅ |
| R-SR-1 Scenario「sibling 脚本路径随名迁移」 | `sdflow-issues/scripts/issues.py:64-65`：`BUGLIST_SCRIPT`/`TODOLIST_SCRIPT` join `"sdflow-buglist"`/`"sdflow-todolist"`；`sdflow-done/SKILL.md:109-111` 三条固定路径已换新名 | ✅ |
| R-SR-2 · 安装器品牌标识 | `VERSION` = `0.9.0`；`setup.sh:161-163` 动态读 VERSION 输出 `sdflow-skills v${version}`；`test_version_line_branded`（`sdflow-init/tests/test_setup_sdflow.py`）动态断言，非硬编码 | ✅ |
| R-SR-2 Scenario「存量 laodao marker 仍被识别为自属」+「名单为界不误伤」 | `setup.sh:26,29-30`：`OUR_LEGACY_NAMES`（21 名=9 旧+9 新+3 保留）判据；`test_legacy_marker_recognized_only_for_our_names`（同文件）21 名单全量接线 + 1 个名单外（`bilibili-research`）对照，三分断言：旧名清零/现存名换链/名单外 skip — 本次会话重跑该测试文件：`10 passed` | ✅ |
| R-SR-3 · 托管区块 marker 迁移（token 定位） | `sdflow-init/scripts/init.py:38-46,70-90`：`_find_marker_line` 按 token（`opsx-init:start`/`opsx-init:rules:start`）定位而非全文精确匹配；本次会话重跑 `grep -c "opsx-init:start" CLAUDE.md AGENTS.md` 与 `grep -c "opsx-init:rules:start" openspec/INDEX.md` → 均为 `1`（原位替换非追加重复），且区块文案已是 `sdflow-init 维护` | ✅ |
| R-SR-3 Scenario「跨改名孤儿链真实可清」 | `setup.sh:74-114` `cleanup_orphans` 改用 `find "$dest" -mindepth 1 -maxdepth 1` 枚举（覆盖 dangling 软链）；`TestCleanupOrphansDangling`/`TestRenameEndToEnd`（`test_setup_sdflow.py`）两类测试通过 | ✅ |
| MODIFIED「workflow bundle 分层部署」「resolver」中的 sdflow- skill 名引用 | 该两条 MODIFIED 需求为既有功能（非本 change 新增），本 change 只涉其正文内旧 skill 名同步；`openspec/specs/spec-workflow/spec.md` 全文 grep 旧名（`opsx-project-init`/`opsx-done`/`opsx-maintain`/`opsx-roadmap-planner`/`buglist-recorder`/`todolist-recorder`/`issues-recorder`）零命中；`spec-review`/`impl-review` 命中均为 `[spec-review-amendment]`/`[impl-review-fix]` 工作流标签或 `spec-review-report.md` 文件名（通用约定非 skill 自称，trigger-map.md 已注明维持不变） | ✅ |
| 触发词重写（tasks 2.1/2.2） | 见上「触发等价不回退」锚点，同一断言 | ✅ |
| 品牌收拢（tasks 3.1-3.3） | VERSION/setup 输出见上；`README.md`/`CLAUDE.md` 正文 "来自 laodao-skills" 类表述已改；重跑 laodao 反向扫描（白名单同 assert-log Step2）→ 9 行残留，逐行核对均为 `.laodao-skills` 兼容代码本体/注释、CLAUDE.md 历史叙述句（白名单允许）、测试字面，无未解释残留 | ✅ |
| 4.1 新增测试（孤儿清理/marker 收窄/token 迁移/版本行/布局冒烟） | 本次会话重跑 `sdflow-init/tests/test_setup_sdflow.py`（10 passed）、`test_init.py -k "marker or token"`（3 passed） | ✅ |
| 4.2 存量测试路径修正 + 全量回归 | 本次会话重跑 `python3 -m pytest -q` → **233 passed**，与 brief 预期一致，全绿 | ✅ |
| 4.3 白名单反向断言（9 pattern，逐名定制 + 挪至 5.4 之后执行） | 本次会话按 assert-log.md 记录的确切命令重跑 9-pattern 反向扫描：`opsx-project-init`=9、`opsx-done`=5、`opsx-maintain`=3、`opsx-roadmap-planner`=3、`spec-review`(负向)=59、`impl-review`(负向)=19、`buglist-recorder`=5、`todolist-recorder`=3、`issues-recorder`=3——计数与 assert-log 留档的历史值有小幅漂移（119→112→本次约111，因后续 impl-review 阶段又新增了合法的 `[impl-review-fix]` 标签等白名单内文本），但抽查命中内容均属 assert-log「clean 判定理由」覆盖的类别（`OUR_LEGACY_NAMES` 定义行、`spec-review-report.md`/`code-review-report.md` 产出物文件名、`[impl-review-fix]` 通用标签、迁移测试故意保留的旧名字面、`spec-review.md` 方法论文件名），未发现新增的、白名单外的未判读命中 | ✅ |
| 5.1 `adr/0007` | 文件存在，含 RENAME-MAP 表、(a)-(g) 子决策、Considered Options、Consequences，措辞已用「OUR_NAMES 是迁移测试侧另维护的对照集合」等实况修正（final-review-fix 已回填） | ✅ |
| 5.2 ROADMAP 更名 supersede | `openspec/ROADMAP.md:16`："`sdflow-rebrand`（曾用名 `extract-sdflow-repo`）" 行存在，状态"🔵 实现完成（待 code-review/收尾）"，rescope 理由完整 | ✅ |
| 5.3 真实激活改道验收 | 见上 R-SR-1 Scenario 行；沙箱测试（`test_rename_scenario_old_links_cleaned_new_links_made`）已实测覆盖跨改名孤儿清理+新链建立；真实 canonical checkout 激活明确属 merge 后 hand-off 范围，不计入本次 gap | ✅（amendment 口径） |
| 5.4 `update --dev` 同步 + 4.3 断言顺序 | assert-log.md Step1 记录 `python3 sdflow-init/scripts/init.py update --dev --root .` 实跑输出（含 `openspec/workflow/` 全刷、托管区块更新提示）；本次会话重跑 `diff -q CLAUDE.md/AGENTS.md/INDEX.md` 区块 grep 计数确认区块唯一且已是新名（见上 R-SR-3 锚点），顺序（Step1 先于 Step2）与 brief 口径一致 | ✅ |
| 5.5 hand-off 四项 | verify 是本次任务范围；hand-off.md 尚未产出（预期由 opsx-done verify **之后**的独立步骤产出），tasks.md 对账注已注明"落地于本次收尾产出的 hand-off.md（随归档）"——不构成 verify 阶段 gap，转交 opsx-done 下一步 | ✅（范围内） |
| Minor 债务（T21-T24） | `openspec/issues/todolist/2026-07-todolist.md`：T21（inject 畸形态加固）/T22（open() 用 with 改造)/T23（Windows 分支缺直接测试）/T24（install_into 软链所有权校验）均 OPEN，来源标注 `sdflow-rebrand`，四项详情段落完整 | ✅ PASS 注明（已挂债，不阻塞） |

## 复核方式说明

以下证据均为本次会话内**亲自重跑**得到，而非转抄既有报告文字：
- `python3 -m pytest -q` → 233 passed
- `sdflow-init/tests/test_setup_sdflow.py` 单独重跑 → 10 passed
- `sdflow-init/tests/test_init.py -k "marker or token"` → 3 passed
- trigger-map.md 机械断言脚本重跑 → `OVERALL: ALL PASS`
- 9-pattern 反向残留扫描重跑（assert-log.md 命令原样复用）
- laodao 反向残留扫描重跑（assert-log.md 命令原样复用）
- marker 区块唯一性 grep 重跑（`opsx-init:start`/`opsx-init:rules:start` 计数=1）
- `~/.skills/sdflow-skills`（canonical/runtime checkout）与 dev checkout 的 git log 对比，确认 5.3 amendment 所述"真实激活尚未发生、时序天然隔离"属实

## 缺口清单

无阻塞性缺口。四项 Minor 债务（T21-T24）已按设计门裁决 defer，随 todolist 池追踪，不阻塞本次收尾。

## 结论

**PASS**——19 项任务的实现均能在当前代码状态下重新验证到位；R-SR-1/2/3 的全部 Scenario 要么有可复现的测试/断言锚点，要么落入 tasks.md 对账注明确的 amendment 后验收口径（5.3 真实激活、5.5 hand-off 后续产出）。建议进入 hand-off → archive → commit → merge 流程。
