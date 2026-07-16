---
ship-gate:
  verify: PASS
---

# verify 报告 — add-codex-host-support

**日期**：2026-07-16 · **change**：add-codex-host-support · **宿主**：Claude（`CLAUDECODE=1`）

## 结论：**PASS**

Claude-side 全部核心功能代码均已落地并有机验锚点；全量 `uv run --with pytest pytest -q` = **1426 passed**；`setup.sh` 两道门（`sync_principles --check` / `gen_workflow_guide --check`）均绿。唯一未勾的 4 项（0.1 / 0.2 / 0.3 / 10.1）是**Codex 真机验证 deferred**（本轮 Claude 宿主无法执行），用户已显式授权(C)未验即合并、风险自负——属「验证动作未在 Codex 跑」而非「代码未实现」，判 Minor/deferred，不构成 FAIL。

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行 / 测试） | 状态 |
|---|---|---|
| 1.1-1.3 契约枚举升维（host + runner=none/unknown，删 claude-fallback） | `lens-metric-contract.md:24-31`（enums 块）+ `:50-59`（fold 块 codex/claude→outside-voice） | ✅ |
| 2.1/2.2 anchor_lint REQUIRED_FIELDS 含 host + 枚举校验 | `anchor_lint.py:27,67-76` | ✅ |
| 2.2b outside-voice 锚 KV 解析（reason_code 必填） | `anchor_lint.py:422,454-484` | ✅ |
| 2.3 合法组合矩阵=自审红线单一源（always-on 独立函数） | `anchor_lint.py:428-493`（classify_combo/check_legal_combo）+ `:688` 无条件调用 | ✅ |
| 2.3b 普通镜 + OV lens-metric 行级组合校验（B1 fix 面治） | `anchor_lint.py:619-643`（ov-runner-none/ov-unknown-host/ov-runner-unknown） | ✅ |
| 2.4 anchor_lint 不判宿主（无 resolve-models import） | `anchor_lint.py` 无 resolve-models 引用（grep 确认）+ `:418` 边界注释 | ✅ |
| 2.5 fanout 一致性 lint 读 mirrors=（always-on，缺锚/坏值 fail-closed） | `anchor_lint.py:497-590`（check_fanout_consistency）+ `:689` 无条件调用 | ✅ |
| 3.1/3.2 emitter --host 必填受控 fail-closed + parse_known_args + extras 拒 + none 合法 | `lens_metric_emit.py:206-238`（allow_abbrev=False, extras, D4/D12） | ✅ |
| 3.2b/8.6 skew 探测 fail-loud（两 SKILL） | `sdflow-spec-review/SKILL.md:105` · `sdflow-code-review/SKILL.md:129` | ✅ |
| 3.3/3.4 golden fixture + 四条既有 Scenario 回归 | `tools/tests/fixtures/lens_metric_input.json` + `test_lens_metric_emit.py`（1426 绿） | ✅ |
| 4.1-4.4 guard same-family + v1 兼容读 + 引用矩阵 + runner=none 不复用 | `outside_voice_guard.py:16-63`（REASON_CODES 七码 + classify_combo 本地重实现） | ✅ |
| 4.5 矩阵跨工具全笛卡尔 golden（完整分类逐条一致） | `test_outside_voice_guard.py:388-415`（test_matrix_cross_tool_golden_full_cartesian） | ✅ |
| 4.6 codex#N prose 标签旁路核（C1 fix：删除 fallback，不构成复用资格） | `outside_voice_guard.py:123-134`（parse_codex_findings 已删 _CODEX_LABEL_RE） | ✅ |
| 5.2/5.3/5.4 聚合器双代兼容读 + host 分组 + 逐行一致 | `lens_metric_aggregate.py:116-140`（normalize_host_runner/group_key）+ `test_lens_metric_aggregate.py:124-132` | ✅ |
| 5.5 retro_report 同步 | `sdflow-retro/scripts/retro_report.py` + `test_retro_report.py`（1426 绿） | ✅ |
| 6.1/6.2 resolve-models.sh 四分支宿主判定 + eval 导出六变量 + 档位读 model-tiers.md | `resolve-models.sh`（全文）+ `test_resolve_models.py:100-181` | ✅ |
| 6.2b/6.2c 覆盖按机队分键 + 扁平兼容读 Claude + config.template | `resolve-models.sh:5.节`（fleet override）+ `config.template.yaml:57-68` + `test_resolve_models.py:193-234` | ✅ |
| 6.2d eval 注入加固（printf %q + 字符集校验 + 恶意值回归） | `resolve-models.sh:4.节`（_valid_model_id）+ `:7.节`（printf %q）+ `init.py:269`（config_lint 同口径）+ `test_resolve_models.py:234` | ✅ |
| 6.3 setup.sh 装 resolve-models.sh（验安装路径） | `setup.sh:145-150`（拷 hack/*.sh）+ `test_setup_sdflow.py` | ✅ |
| 6.4 G6 同源锁（outside-voice.sh 不自调 resolve-models） | `outside-voice.sh` 只读 `$SDFLOW_VOICE_RUNNER`（grep 确认无 resolve-models 调用） | ✅ |
| 7.1/7.2 preflight 探目标 runner CLI + exec 按 runner 分叉 + 三件套共用 | `outside-voice.sh:171,198-217`（secret_scan/render_prompt 单份共用） | ✅ |
| 7.3/7.4 安全承重墙：claude exec 只读工具集 + strict-mcp + add-dir（+ A1 fix 第四旗 --settings 读围栏） | `outside-voice.sh:215-217` + `test_outside_voice.py` | ✅ |
| 7.5 HOST=unknown → 不跑 voice + host-unknown | `outside-voice.sh:173,249` | ✅ |
| 7.7 secret_scan stderr 脱敏（只出规则类型+行号） | `outside-voice.sh:92-95` | ✅ |
| 7.8 missing-deps → preflight-error 映射 | `outside-voice.sh:19,255`（返回）+ SKILL 映射 `spec-review:271`/`code-review:271` | ✅ |
| 7.6 版本号升级 | `outside-voice.sh:56` OV_VERSION=1.3.0（A1 fix 从 1.2.0 再升，含读围栏+出境 secret_scan） | ✅（见 Minor #1） |
| 8.1 model-tiers.md 按机队分列 + defaults 机读块 | `model-tiers.md:11-15,28-34` | ✅ |
| 8.2/8.3/8.4/8.5 两 SKILL host= 锚 + 引用矩阵 + SDFLOW_TIER 变量 + task-specific reason | `spec-review/SKILL.md:104,178,243` · `code-review/SKILL.md:128,202,229`（B2 fix 模板 `:323` 补 host=） | ✅ |
| 9.1/9.3 消费仓 Codex 子代理授权声明 + init 守卫 | `snippets/claude-section.md:82-91` + `AGENTS.md` + `test_codex_subagent_authorization.py:44-156` | ✅ |
| 9.2/9.4 fan-out 前能力探针 + mirrors= 直接落 | `spec-review/SKILL.md:134-150` · `code-review/SKILL.md:162-167` | ✅ |
| 10.2 Claude 宿主回归行为不变 + 存量聚合逐行一致 | `test_lens_metric_aggregate.py`（回归基线）+ 1426 绿 | ✅ |
| 11.1 docs workflow-map.{md,html} 字段表同步 | `docs/workflow-map.md:141,150-151` + `docs/workflow-map.html:555-566` | ✅ |
| 11.2 全量 pytest + setup 两道门 | 1426 passed · sync_principles/gen_workflow_guide --check 均绿（本轮实跑确认） | ✅ |

## 缺口清单

### 核心缺口（FAIL 项）
**无。** Claude-side 全部核心功能代码均已实现并有机验锚点。

### Minor / deferred 缺口（不阻塞 PASS）

1. **[deferred·用户 C 授权] Codex 真机验证 4 项未勾**（0.1 A1 核验 / 0.2 A3 核验 / 0.3 前置门结论写回 / 10.1 Codex 宿主端到端）——本轮 Claude 宿主（`CLAUDECODE=1`）无法在真实 Codex 机器执行，复选框已诚实保持未勾 + 说明。用户显式授权(C)未验即合并、风险自负。**属「验证动作未在 Codex 跑」而非「代码未实现」**——host-adaptive 全部代码（resolver 宿主判定、outside-voice runner 分叉、anchor_lint 矩阵/fanout lint、emitter --host、aggregate 双代兼容）均已写出并测试覆盖。非代码缺口。

2. **[Minor·非功能] `outside-voice.sh:33` 头部契约注释 stale**——`version` 子命令 stdout 描述仍写 `"outside-voice.sh 1.2.0"`，实际 `OV_VERSION`（`:56`）已是 `1.3.0`（A1 code-review fix 再升）。仅头部文档注释漂移，`version` 命令实际输出正确。可在 done/archive 阶段随手订正，不阻塞。

3. **[deferred·design-writeback，done/archive 阶段] 5 项文档订正**（code-review-report 已登记，实现期改四件套会触设计门失鲜，MUST 在 archive 随 delta 写回）：A1 沙箱不对称登记（design 安全表 r3「两路径均无硬 FS 读边界」与实测 codex 有内核沙箱矛盾）· B1 决策记录「均查」措辞 · V3 v1 reason_code 兼容假设 · V4 ADR-0024「结构性杜绝」措辞 · V5 ADR-6「真跑一次」措辞。**均为设计文档措辞订正，非代码缺口**；运行时影响有界安全（code-review 已逐项核实）。

4. **[todolist] 两项低优改进**：C2 init.py `metrics.enabled` 重复键收紧 · V5 preflight 真探针（若选补而非订正 ADR 措辞）。非本 change scope 内的缺陷。

### 运行时生效提醒（非缺口，hand-off 事项）
合并后须在**运行 checkout**（`~/.skills/sdflow-skills`）重跑 `bash setup.sh`——`assets/hack/`（resolve-models.sh / outside-voice.sh）是 copy 非 symlink，不重跑 = 新 SKILL 调旧脚本窗口。

---

**PASS** — Claude-side 核心功能代码全部实现且有机验锚点，1426 tests + 两道 setup 门绿；唯余 Codex 真机验证（用户 C 授权 deferred）与 design-writeback 文档订正（done/archive 阶段随 delta 写回），均非代码缺口。
