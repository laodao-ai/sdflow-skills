# verify-report — drop-per-dir-review-stub

日期：2026-07-05

## 结论：PASS

<!-- ship-gate: verify=PASS -->

证据锚点全部落实：仓级 `python3 -m pytest -q` → **364 passed**（符合预期基线，零回归）；
`TestRetiredHooks` 8 用例全绿（含 CR-F1 两负例）；两个每目录 stub 生产者均已物理删除；
`init.py` 反注册机制完整且在 `run()` init/update 两路径均被调用；文档同步到位；根锚能力未回退。

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行 / 测试 / 结果） | 状态 |
|---|---|---|
| T1.4 `RETIRED_HOOKS` 名单 | `sdflow-init/scripts/init.py:63` = `["change-review-stub.py"]` | ✅ |
| T1.4 `retire_hooks()`（摘注册+删脚本+fail-safe） | `init.py:319-344` | ✅ |
| T1.4 `_deregister_hook_in_settings`（外科式摘除+空 entry 丢弃+坏 JSON fail-safe） | `init.py:279-316` | ✅ |
| T1.4 `_hook_command`（CR-F1 非 dict/非 str 归 ''） | `init.py:269-276` | ✅ |
| T1.4 `retire_hooks()` 在 `run()` 主流程被调（init/update 都跑，未按 mode 分支） | `init.py:382`（try 块内无条件调用） | ✅ |
| T1.1/1.2 反注册主/边界测试 | `test_init.py` TestRetiredHooks: `test_retires_existing_registration_and_script_keeping_others`(401)、`test_fresh_install_is_noop`(419)、`test_no_settings_file_still_deletes_script`(437)、`test_bad_json_settings_is_failsafe`(448)、`test_multiple_registrations_all_removed`(460)、`test_mixed_entry_keeps_sibling_hook`(520) | ✅ |
| CR-F1 两负例（非 dict 元素 / 非 str command 不崩） | `test_init.py:478 test_malformed_non_dict_hook_element_does_not_crash`、`:499 test_non_string_command_does_not_crash`；断言退役项摘除且畸形条目原样保留 | ✅ |
| TestRetiredHooks 全绿 | `pytest ...::TestRetiredHooks -q` → **8 passed** | ✅ |
| T2.1 `HOOKS` 移除 change-review-stub（仅留 ff0） | `init.py:49-57` 只含 `ff0-branch-guard.py` | ✅ |
| T2.2 删 `assets/hooks/change-review-stub.py` | `ls assets/hooks/` 仅剩 `ff0-branch-guard.py` | ✅ |
| T2.3 删 `test_change_review_stub_hook.py` | 不在 `sdflow-init/tests/`（已删） | ✅ |
| T2.3 test_init.py 断言改为「反注册」而非「安装」 | TestRetiredHooks 断言 `change-review-stub.py not in blob`（摘除语义） | ✅ |
| T3.1 删 `sdflow-roadmap/scripts/gen_review_stub.py` | 整个 `sdflow-roadmap/scripts/` 目录不存在 | ✅ |
| T3.2 删 `test_gen_review_stub.py` | 整个 `sdflow-roadmap/tests/` 目录不存在 | ✅ |
| T3.3 roadmap SKILL 去掉 gen_review_stub 步 | `sdflow-roadmap/SKILL.md:217` 改为「不再每目录生成 review.html stub（放弃 scoped 深链，可接受降级）」 | ✅ |
| T4.1 init SKILL 只列 ff0 + 退役 hook 说明 | `sdflow-init/SKILL.md:106`(仅 ff0-branch-guard)、`:107-109`(退役 hook 反注册说明) | ✅ |
| T4.2 ROADMAP.md 去 change-review-stub 并列 | `openspec/ROADMAP.md` grep 无 change-review-stub 命中；:36 仅提 ff0-branch-guard | ✅ |
| 根锚未破坏（能力不回退） | `copy_review_tool`(`init.py:146-177`)+`copy_bundle` tools/ 子树(`:108-124`) 未改；serve.sh/根 review.html 照铺 | ✅ |
| spec delta Scenario「建 change 不落每目录 stub」 | 两生产者均删（hook 出 HOOKS 列表 + gen_review_stub 删）→ 行为一致 | ✅ |
| spec delta Scenario「退役 hook 自愈」 | `retire_hooks()` + TestRetiredHooks 主用例断言存量摘除、fresh no-op → 一致 | ✅ |
| 活跃文件无悬空引用 | grep 剩余命中全为：RETIRED_HOOKS 正当引用（init.py/SKILL.md/test）+ 历史留档（docs/superpowers/plans、adr/0003、todolist） | ✅ |
| T5.1 仓级 pytest 无回归 | `python3 -m pytest -q` → **364 passed in 23.65s** | ✅ |

## 缺口清单

**核心缺口（FAIL）**：无。

**Minor / deferred（可接受）**：
- `docs/superpowers/plans/2026-07-01-openspec-review-html-tool.md`、`openspec/adr/0003`、
  `openspec/issues/todolist/2026-07-todolist.md` 仍含 change-review-stub / gen_review_stub 字样
  —— 均为**历史留档**（原实现计划 memo / ADR 决策记录 / todo 动机），非活跃代码路径，
  按 Non-Goals「archive 历史不追溯清理」原则，**判 Minor 可接受**，不阻断。
- CR-V1 / CR-V2 为**有意 defer**（对应 T44/T45），按任务约定不计缺口。
- T5.2 手验（临时项目 `openspec new change demo` 无 review.html + 根锚可导航）为人工步；
  其机制已由「两生产者物理删除」+「根锚 copy_review_tool 未动」双向保证，判 ✅（机制锚点充分）。

---

PASS
