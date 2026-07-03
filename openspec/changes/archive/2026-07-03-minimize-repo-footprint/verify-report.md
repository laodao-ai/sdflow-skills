# Verify Report — minimize-repo-footprint

日期：2026-07-03
Change：`minimize-repo-footprint`

## 结论：**PASS**（含 6 条已记债的 Minor 缺口，均非核心功能缺失）

核心功能（分层部署、resolver 三步链脚本化、迁移不自动删+陈旧遮蔽告警、sdflow-upgrade skill、激活验证）均有可机验证据锚点支撑；未发现"复选框已勾但代码未落地"的静默放过项。

---

## 逐需求核对表

### R-MRF-1：分层部署（workflow bundle 改在权威源、经部署下发）

| 需求/任务 | 证据锚点 | 状态 |
|---|---|---|
| 0.1 运行 checkout 迁移至 `~/.skills/sdflow-skills` | activation-log.md「Task1 运行 checkout 迁移」：`git clone` 真实输出 + `bash setup.sh` 真实输出（22 软链）+ `readlink` 验证软链指向新仓 + 旧仓 `~/.skills/laodao-skills` 未触碰的 `git status --short` 空输出 | ✅ 实现 |
| 1.1 `setup.sh` 建 canonical（Unix，软链 + 所有权检查） | `setup.sh:114-129`（`install_sdflow` 函数：`[ -e ... ] && [ ! -L ... ]` 真实目录判非自属→`skipped`）；测试锚点 `opsx-project-init/tests/test_setup_sdflow.py::test_foreign_real_dir_not_clobbered`、`::test_takeover_of_stale_symlink_is_visible`（`pytest -q` 61 passed 含此文件） | ✅ 实现 |
| 1.2 `setup.sh` 建 canonical（Windows，指针文件） | `setup.sh:111-113`（`printf '%s\n' "$bundle" > "$sdflow/workflow-path"`，单行无 `\r`、POSIX 路径来自 `$REPO_DIR`）；resolver 侧 CRLF/空格容错测试 `test_resolve_workflow.py::test_pointer_with_trailing_crlf_and_spaces` | ⚠️ Minor 缺口 — Windows 分支**无所有权检查**（tasks.md 1.2 自述"未做"）→ **T14**（`openspec/issues/todolist/2026-07-todolist.md:22`） |
| 1.3 bundle 仍在 `assets/workflow`，唯一权威源实核 4 处 | `opsx-project-init/SKILL.md:9,16,102`（3 处）+ `opsx-project-init/scripts/init.py:24`（`权威源 = 本 skill 的 assets/workflow/`，1 处）= 4 处；`ls opsx-project-init/assets/workflow` 存在、仓根无提根副本（`ls` 仓根无 workflow 目录） | ✅ 实现 |
| 2.1 `copy_bundle` 只部署 `tools/` | `opsx-project-init/scripts/init.py:87-101`（`copy_bundle`：non-full 分支只 `copytree(BUNDLE_SRC/tools, tools_dst)`）；测试 `test_init.py::TestBundleToolsOnly::test_deploys_only_tools_subtree`、`::test_plain_update_does_not_deploy_rules` | ✅ 实现 |
| 2.2 `checkpoint-commit.sh` 全局装到 `~/.sdflow/hack/` | `setup.sh:131-137`（`install_sdflow` 拷贝 + `chmod +x`）；测试 `test_setup_sdflow.py::test_creates_canonical_symlink_and_hack_scripts`（断言 `is_file() and not is_symlink()` + exec 位）；`init.py` 无 `copy_hack` 函数，测试 `test_init.py::TestNoConsumerHack::test_init_module_has_no_copy_hack` | ✅ 实现 |
| 2.3 `[checkpoint]` 单点约定指向全局路径 | `opsx-project-init/assets/workflow/workflow.md` 内 `[checkpoint]` 锚文本已改指 `~/.sdflow/hack/checkpoint-commit.sh`（commit `43ff457 checkpoint(task8-fix): ... workflow.md 步骤7 resolver 注解`） | ✅ 实现 |
| 2.4 `serve.sh` / 根 `review.html` 复制逻辑保持 | `init.py:copy_review_tool`（未改动，`test_init.py::TestReviewToolDeployment` 全部通过） | ✅ 实现 |
| 2.5 `handle_config` 读 BUNDLE_SRC + 回归测试 | `init.py:187-196`（`handle_config` 用 `tmpl = os.path.join(BUNDLE_SRC, "config.template.yaml")`，非消费仓副本）；测试 `test_init.py::test_init_creates_config_without_consumer_template` | ✅ 实现 |
| MODIFIED Scenario「修改 workflow 规则」 | 同 1.3 锚点（权威源改动路径） | ✅ 实现 |
| MODIFIED Scenario「新 init 的消费仓不含规则副本」 | activation-log.md Step3b：新 init 临时仓 `find ... -name "*.md" -not -path "*/tools/*" \| wc -l` = **0**（真实命令输出）；`checkpoint-commit.sh` 未进消费仓 hack/（`hack 脚本：不再铺进仓` 输出行） | ✅ 实现 |

### R-MRF-2：规则全局解析 resolver

| 需求/任务 | 证据锚点 | 状态 |
|---|---|---|
| 3.1 接口契约（`--root`/`--explain`/`SDFLOW_HOME`/三步链/退出码） | `opsx-project-init/assets/hack/resolve-workflow.sh` 全文（1-84 行）：`--root` 缺省 `git rev-parse --show-toplevel`（L25-26）、`--explain`（L33-35）、`SDFLOW_HOME`（L11）、any-of 判据+部分残留告警（L37-51）、canonical 回落 Unix/Windows（L53-67）、健全性检查 `sane()`（L69-73）、exit 2 固定告警（L81-83） | ✅ 实现 |
| 3.2 skill 读点改调脚本（spec-review 3处 + impl-review 3-5处 + opsx-done/recorders 0处） | `grep -c resolve-workflow` spec-review/SKILL.md=3、impl-review/SKILL.md=3 行/5 处提及（含 L16/56/154，L56 含 3 次调用文本）；`opsx-done/SKILL.md` `buglist-recorder/SKILL.md` `todolist-recorder/SKILL.md` 均无 workflow.md/checklists 引用（grep 空输出，确认 0 处不改） | ✅ 实现（occurrence 计数与 tasks.md 注记的"4处"有轻微出入，为文档计数口径差异，非功能缺口） |
| 3.3 调用方守卫（不静默吞非零退出码 + 不重实现三步链） | `spec-review/SKILL.md:30`、`impl-review/SKILL.md:56`："退出码 2 → 显式降级...原样转发脚本 stderr 告警"、"禁止自行重实现三步链" | ✅ 实现 |
| 3.4 部署产物读点修复（config.template.yaml + 2 个 snippets） | `opsx-project-init/assets/workflow/config.template.yaml:4-5,39,40,47`（`@openspec/workflow/...` 引用旁注全局解析兼容说明）；`opsx-project-init/assets/snippets/index-section.md:6`（"无本地规则副本的仓：...位于全局 canonical"） | ✅ 实现 |
| 5.3 resolver 脚本单测（8 类场景） | `opsx-project-init/tests/test_resolve_workflow.py` 18 个 test_，覆盖：本地命中(`test_local_pin_hit`)、部分残留(`test_partial_residue_pins_and_warns`)、全局软链(`test_tools_only_repo_falls_to_global_symlink`)、全局指针(`test_pointer_file_fallback`)、全局缺(`test_global_missing_exits_2_with_guard_message`)、健全性不过检(`test_insane_bundle_treated_as_missing`, `test_sane_rejects_empty_checklist_dir`)、指针含空格/中文/CRLF(`test_pointer_with_trailing_crlf_and_spaces`, `test_pointer_path_with_chinese_dir_resolves`)、非仓根cwd+`--root`(`test_root_flag_overrides_cwd`, `test_deleted_cwd_exits_64`)；`pytest -q` 全绿（61 passed） | ✅ 实现 |
| 5.7 激活验证（真实调用，非文本已改） | activation-log.md「Task10 激活验证」Step3：`~/.sdflow/hack/resolve-workflow.sh --root . --explain` 真实 stderr `source=local-pin`；临时消费仓 `git init` 后缺省 `--root` → `source=global-canonical path=/Users/cheneyzhao/.sdflow/workflow`；Step4 Codex CLI 实测 `codex exec 'bash ~/.sdflow/hack/resolve-workflow.sh...'` 输出含 `source=local-pin`；「impl-review 第零步」小节：`/impl-review` SKILL.md 第零步真实调用 resolver，`exit_code=0`、`stderr: resolve-workflow: source=local-pin path=...` | ✅ 实现（证据为真实调用输出，非文本描述） |
| ADDED Scenario「迁移期部分残留判 pin 且告警」 | `resolve-workflow.sh:44-51` + 测试 `test_partial_residue_pins_and_warns` | ✅ 实现 |
| ADDED Scenario「消费仓无本地规则副本走全局」 | `resolve-workflow.sh:37-43`（any-of 全 0 → 不 exit，续步2）+ 测试 `test_tools_only_repo_falls_to_global_symlink` + activation-log Step3b 真实输出 | ✅ 实现 |
| ADDED Scenario「toolkit 源仓与显式 pin 命中本地」 | activation-log Step3a：本仓 `source=local-pin path=./openspec/workflow`（本仓 dogfood 副本存在即命中，无 config flag） | ✅ 实现 |
| ADDED Scenario「全局缺失显式降级不静默」 | `resolve-workflow.sh:81-83`（exit 2 + 固定 stderr 文案）+ 测试 `test_global_missing_exits_2_with_guard_message` | ✅ 实现 |
| ADDED Scenario「canonical 解析平台回落」 | `resolve-workflow.sh:53-67`（`case "$SDFLOW_HOME" in /*) ... -d workflow ... elif -f workflow-path` 平台判断全在脚本内） | ✅ 实现 |
| ADDED Scenario「resolver 由脚本执行而非模型 prose」 | 同 3.2/3.3/5.7 锚点 | ✅ 实现 |

### R-MRF-3：存量消费仓迁移不自动删、陈旧遮蔽须告警

| 需求/任务 | 证据锚点 | 状态 |
|---|---|---|
| 4.1 `update` 停止复制规则 | `init.py:copy_bundle` non-full 分支（同 2.1）；测试 `test_init.py::test_plain_update_does_not_deploy_rules` | ✅ 实现 |
| 4.2 陈旧遮蔽告警（update 内联 + opsx-maintain 兜底，覆盖 checkpoint 孤儿） | `init.py:stale_shadow_warnings`（L108-121，RULE_MARKERS any-of + checkpoint 孤儿双告警，仅 append 不删）；`opsx-maintain/SKILL.md:46-50`（兜底扫描同款判据与文案）；测试 `test_init.py::test_warns_on_residual_rules_and_orphan_hack_without_deleting`、`::test_clean_consumer_no_warnings`、`::test_update_prints_warnings`、`::test_init_on_legacy_repo_warns_shadow` | ✅ 实现 |
| 5.4 迁移测试（残留触发告警不删、留旧副本仍 local-first、孤儿 checkpoint 告警） | 同上 `test_init.py` 4 个测试 + resolver 侧 `test_partial_residue_pins_and_warns`（"仍能跑"对应 resolver 命中本地） | ✅ 实现 |
| MODIFIED Scenario「update 不删残留规则、给出遮蔽告警」 | `stale_shadow_warnings` + `test_warns_on_residual_rules_and_orphan_hack_without_deleting`（断言 `workflow.md` 文件仍 `.exists()`） | ✅ 实现 |
| MODIFIED Scenario「留旧副本仍能跑（pin 逃生口）」 | resolver 步①命中本地（`test_local_pin_hit` 系列）+ `test_clean_consumer_no_warnings` 反证干净仓无告警 | ✅ 实现 |

### 其余任务组（0/5/6/7）

| 任务 | 证据锚点 | 状态 |
|---|---|---|
| 5.1 dev/runtime 纪律段（adr/0005）+ 回滚句 | `openspec/adr/0005-dev-runtime-checkout-split.md` 全文（开发/运行 checkout 分离、回滚句见 CLAUDE.md 托管区块） | ✅ 实现 |
| 5.2 `opsx-project-init/tests/` 跟部署模型改 + SDFLOW_HOME 隔离 | `test_setup_sdflow.py:run_setup` 用 `env=dict(os.environ, HOME=..., SDFLOW_HOME=...)` 重定向 tmp_path；`test_init.py` 用 `CLAUDE_CONFIG_DIR` 重定向；未见测试写真实 `$HOME`（grep 全测试文件确认使用 tmp_path/monkeypatch） | ✅ 实现 |
| 5.5 文档必改清单（CLAUDE.md 例外句/INDEX/CLAUDE 托管区块/ROADMAP） | `CLAUDE.md:22-23`（"改 `opsx-project-init/assets/hack/` 下脚本后也必须重跑 `setup.sh`"例外句） | ✅ 实现 |
| 5.6 dev dogfood 刷新（`update --dev`） | `init.py:run` 的 `dev` 分支（身份校验 `_die` + `copy_bundle(root, full=dev)`）；activation-log「Task10」Step1 真实输出 + `diff -q` 无输出（instance 与 assets 一致） | ✅ 实现 |
| 5.7 已在 R-MRF-2 表列出 | 同上 | ✅ 实现 |
| 6.1 issues.py 落点决策 | `design.md:121`「issues.py 落点〔6.1 决策〕：留 `issues-recorder/scripts/`」 | ✅ 实现（决策收窄，未做迁移符合任务范围） |
| 7.1 新建 `sdflow-upgrade` skill | `sdflow-upgrade/SKILL.md` 全文（pull→setup→展示版本→提示 update；含回滚句） | ✅ 实现 |
| 7.2 README 列表 + 重跑 setup.sh | `README.md:17`（`sdflow-upgrade` 行）；activation-log Task10 Step2 `bash setup.sh` 真实输出含 `✓ sdflow-upgrade @ .../.claude/skills`、`✓ sdflow-upgrade @ .../.codex/skills` | ✅ 实现 |

---

## 缺口清单

### 核心缺口
（无）

### Minor 缺口（均已记债，非本次验收阻断项）

| ID | 内容 | 影响面 |
|---|---|---|
| T13 | resolver/setup 测试断言可补强（unreadable-pointer stdout 空断言等） | 测试细节，不影响功能正确性 |
| T14 | `setup.sh` Windows 分支缺所有权检查（同 Unix 分支的异物停手告警） | Windows 平台专属，本机 macOS 环境无法实测；tasks.md 1.2 已自述并记债 |
| T15 | `update --dev` 在 dogfood 源仓每次输出两条误报 ⚠（陈旧遮蔽告警对"既是权威源又是消费仓"场景不适用） | 噪声，非功能错误；activation-log 已注明为误报原因 |
| T16 | `install_sdflow` 告警未走独立打印分支，与 `skipped` 数组文案叠加 | 输出可读性 |
| T17 | 陈旧遮蔽判据存在两处（`RULE_MARKERS` 常量 vs `opsx-maintain/SKILL.md` prose 复述），无同步机制 | 未来维护风险，非当前功能缺陷 |
| T18 | `install_into` 对既有软链切换无指向变更提示 | 可观测性，非功能缺陷 |

以上 6 条均已在 `openspec/issues/todolist/2026-07-todolist.md`（T13-T18）登记，关联 change = `minimize-repo-footprint`，状态 OPEN。

---

## 附：测试运行证据

```
$ python3 -m pytest opsx-project-init/tests/ -q
.............................................................            [100%]
61 passed in 1.73s
```

## 附：checkpoint 提交链（fcbe3a3..HEAD，18 个 checkpoint commit，覆盖 Task1-11 + fix）

```
ce5a8e7 checkpoint(impl-review) ... 935eb42 checkpoint(impl-review-fix) ...
22cefad checkpoint(final-review) ... fe7ef97 checkpoint(task11-docs) ...
383c38a checkpoint(task10-activation) ... 797b557 checkpoint(task9-sdflow-upgrade) ...
43ff457 checkpoint(task8-fix) ... eea3533 checkpoint(task8-readpoints) ...
6669fe7 checkpoint(task7-update-dev) ... 6bfbda2 checkpoint(task6-stale-shadow) ...
b418477 checkpoint(task5-init-layered) ... 0fd2d3f checkpoint(task4-setup-sdflow) ...
2fa99ba checkpoint(task3-resolver-edges) ... ee23990 checkpoint(task2-resolver-core) ...
0744306 checkpoint(task1-migrate-runtime) ... 71149be checkpoint(writing-plans) ...
ed96009 checkpoint(gate) ... 5ecb4ac checkpoint(spec-review) ... 670b476 checkpoint(spec-review-autoplan) ...
35480d4 checkpoint(model-baseline) ...
```

---

## 最终判定

**PASS** — R-MRF-1/2/3 全部 MODIFIED/ADDED Requirement 及其 Scenario 均有可机验证据锚点（脚本代码行号、测试用例名、activation-log.md 真实调用输出、commit hash）支撑；5.7 类"激活验证"需求的锚点均为 `--explain` 真实调用输出而非"文本已改"。仅存 6 条 Minor 缺口，均已记入 todolist（T13-T18）并关联本 change，不构成核心功能缺失，不阻断 archive。
