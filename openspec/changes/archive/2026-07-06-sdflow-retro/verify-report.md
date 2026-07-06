# Verify Report — sdflow-retro

- 日期：2026-07-06
- change：sdflow-retro

## 结论：PASS

<!-- ship-gate: verify=PASS -->

所有 ADDED（4 条 workflow-retro）+ MODIFIED（2 条 workflow-metrics）需求均有可机验证据锚点，核心功能全部落实。43 个 retro 测试 + 41 个 init 测试全绿；dogfood 报告已生成且真锚 join / in-progress / seed 守卫 / surfacing 契约实测正确；back-to-back 再生零漂移（view-only 幂等）。

## 逐需求核对表

| 需求 | 代码出处(文件:行/测试) | 状态 |
|---|---|---|
| **[ADDED] 只读再生全项目成本×价值复盘**（含 in-progress、供数不供裁决、tracked 活文档） | `retro_report.py:347 build_report` + `:463 main`（原子写 `openspec/retro/report.md`）；报告实测 `覆盖18 有真锚3 边界不可解析2`；`report.md:23` sdflow-retro 自身标 `in-progress`；`report.md` 已 `git ls-files` tracked；无自动决策代码路径 | ✅ |
| ↳ Scenario 再生全项目复盘 + 幂等无漂移 | dogfood `report.md` 有 per-change 阶段墙钟+价值行+阶段占比+双峰；back-to-back 两次运行 `diff` 完全一致（实测 TRUE IDEMPOTENT） | ✅ |
| ↳ Scenario 含进行中 change 标 in-progress | `:389 status = "in-progress" if info["active"] and not info["archive_dir"]`；`report.md:23` 实测命中 | ✅ |
| ↳ Scenario 价值维 active+archive 两源 + spec+code 两份〔D11〕 | `:228 lens_value_for_change` 遍历 `active_dir`+`archive_dir` × `_REPORT_NAMES`(spec+code)；测试 `test_lens_value_active_change_has_anchor`（:152）；dogfood sdflow-retro active change 挂上 Σfindings=32/采纳率0.88 | ✅ |
| ↳ Scenario N≥10 待复评镜机械显著呈现〔D12〕 | `:315 surfacing_block` 固定前缀 `⚠️ 待复评:`（无命中亦输出固定行）；测试 `test_surfacing_block_fixed_prefix`（:326）；报告顶部独立区块 `report.md:6` | ✅ |
| ↳ Scenario 只呈现不决策 | 全脚本无写 config / 无「应砍」标记；SKILL.md description 明示"只呈现不决策" | ✅ |
| **[ADDED] change 边界靠提交路径不靠 tag** | `:47 git_commits_for_path` 用 `git log -- <path>`；`:84 boundary_for_change` 查裸 `changes/<name>` ∪ archive 路径；未改 `checkpoint-commit.sh` tag 格式（`ship_gate` 测试仍绿见下） | ✅ |
| ↳ Scenario 归档 change 经裸路径捞回 pre-archive 历史〔F1修复〕 | `:84-110` 始终查 `openspec/changes/{name}` 裸路径 ∪ archive；测试 `test_archived_change_full_boundary_via_bare_path`（:77）；dogfood 归档 change 有真实非零 spec-rev/impl/code-rev Δ | ✅ |
| ↳ Scenario done 靠 path-rename 非 subject〔D8〕 | `:156 is_archive_rename` 检 `R`/`D+A` 进 archive 目录（边界锚定 regex 防子串误配）；`:207` stage=done；dogfood adaptive-workflow-routing done Δ=0.5 | ✅ |
| ↳ Scenario seed change 边界守卫〔D9〕 | `:75 seed_mass_shas`(碰≥3 dir 剔除) + `:107 len(merged)<=1 → unresolved`；dogfood issues-pool-batch-mgmt 标"边界不可解析"计入 K=2 | ✅ |
| **[ADDED] 时间维只到阶段级 + 诚实标注含人时间** | `:181 stage_walltimes` 相邻 ts 差；报告头 `report.md:4` 标注"阶段级 elapsed（含人读/拍板/生成时间）口径（adr/0009）"；`:202 Δ<0 钳0+reorder_suspected`〔E〕 | ✅ |
| **[ADDED] 复盘缺口显性 fail-safe** | 顶部覆盖计数 `:375 f"覆盖 {N} / 有真锚 {M} / 边界不可解析 {K}"`；坏文件 try/except 跳过（`:242`、`:294`、`:329 aggregate` 兜底）；无锚标"无度量锚"`:391` | ✅ |
| **[MODIFIED] 数据驱动反馈供数不供裁决 + surfacing 正主迁 retro** | maintain 步骤5 塌薄指针 `sdflow-maintain/SKILL.md:69-83`（"不内联跑聚合器…只提示跑 /sdflow-retro"）；surfacing 逻辑正主 = `retro_report.py:315 surfacing_block` | ✅ |
| ↳ Scenario maintain 保留薄指针不丢 cadence | `sdflow-maintain/SKILL.md:76` 显著提示"跑 /sdflow-retro 看完整复盘（含待复评镜）"，`:82` 明示聚合逻辑已迁出不重复实现 | ✅ |
| ↳ prose 指针改指 retro（5.5 四处+doc） | `sdflow-code-review/SKILL.md:132`、`sdflow-spec-review/SKILL.md:105`+`:120`、`docs/workflow-skills/sdflow-code-review.md:57` 均指 `/sdflow-retro`（grep 实证） | ✅ |
| **[MODIFIED] 聚合器移进 sdflow-retro/scripts/ + 不再派生消费仓** | `git mv` 确认（`git log --follow` 溯到 `a424fbb task1-mv-aggregator`）；旧址 `sdflow-init/assets/workflow/tools/lens_metric_aggregate.py` 已不存在；`init.py:129 ignore_patterns("tests")` 保留、注释 `:116-118` 改指 trivial_shape | ✅ |
| ↳ Scenario 聚合器随 skill 全局安装 | `sdflow-retro/scripts/lens_metric_aggregate.py` 存在；`retro_report.py:10` 同目录 import；`test_lens_metric_aggregate.py` 随迁（parents 校准）绿 | ✅ |
| ↳ init tests-exclusion 改断言非删〔F5/G2〕 | `test_init.py:119 assert trivial_shape.py is_file` + `:126 assert tools/tests/test_trivial_shape.py`（tests 排除覆盖保留）；`test_init.py` 41 passed | ✅ |
| **[数据类 skill] SKILL.md 存在 + 脚本 owns 机械活** | `sdflow-retro/SKILL.md` frontmatter `name: sdflow-retro`（setup.sh 识别）；边界/映射/join/原子写/不变量全在 `retro_report.py`；README:26 + INDEX.md:32 已加条目 | ✅ |
| hr-tg 双列〔D10〕 | `:304 hr_tg_flags` 返回 spec_hr_tg/code_hr_tg 两列；dogfood cross-model-outside-voice code_hr_tg=`TG-08,TG-17` | ✅ |

## 缺口清单

### 核心 FAIL
无。

### Minor / 已知接受取舍（不阻塞）
- **committed report.md 相对最新 git 历史 stale**：对已提交报告二次再生会有差异（新增 commit 后内容更新）。这是 spec 明示的"归档新 change 后未跑前 report 为 stale 属已知接受取舍"（锚/git 历史才是真相源），非缺陷；back-to-back 真幂等已验证。
- **pre-existing（非本 change）**：全仓 `pytest` 有 1 个 `sdflow-ship/tests/test_gate_anchor_scope.py::test_contract_archived_corpus_anchor_hits` 失败（B5，main 亦红），与本 change 无关，不计 gap。

---

PASS — 6 条需求（4 ADDED + 2 MODIFIED）全部有可机验锚点落实；retro 43 + init 41 测试绿、dogfood 与幂等实测通过；唯一预存 ship_gate 失败为非本 change 已知项。
