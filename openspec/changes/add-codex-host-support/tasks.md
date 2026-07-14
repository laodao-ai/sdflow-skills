# tasks — add-codex-host-support

> **顺序即 design 的 Migration Plan**：契约先行（工具测试自然变红，暴露所有依赖点）→ 工具 → 聚合器 → helper → 规则/SKILL → 铺设 → 文档。
> **追溯**：每任务标注所属 capability 的 Requirement 名（本仓 spec 用中文标题作 ID）。
> **测试纪律**：`scripts/` 改动必跑对应 `tests/`；全量 `pytest` 在每个任务组末尾绿。

## 1. 契约先行（枚举单一源）

- [ ] 1.1 改 `assets/workflow/lens-metric-contract.md` 的 `lens-metric-enums` 机读块：新增 `host: claude, codex, unknown`；`runner` 收缩为 `claude, codex`（删 `claude-fallback`）〔workflow-metrics · 度量锚契约〕
- [ ] 1.2 改同文件 `lens-metric-fold` 机读块：删 `claude-fallback: outside-voice` 行，保 `codex: outside-voice` 并新增 `claude: outside-voice`（任一 runner 的 voice 都折叠到 outside-voice）〔workflow-metrics · 度量锚契约〕
- [ ] 1.3 改同文件的锚形示例 + 散文注记 + 归属规则段：行键升为 `(lens, host, runner, site)`，唯一键升为 `(layer,lens,host,runner,site,轮)`；写明「跨模型性 = `runner ≠ host` 的派生量，MUST NOT 编码进枚举值」〔workflow-metrics · 度量锚契约〕
- [ ] 1.4 跑全量 pytest 确认**工具测试如期变红**（红的位置 = 依赖契约枚举的全部落点，据此核对 design 的 scope-check 表无遗漏）——**此步的产出是一份红点清单，不是绿**

## 2. 校验工具（anchor_lint）

- [ ] 2.1 TDD：`test_anchor_lint.py` 加用例——`REQUIRED_FIELDS` 含 `host`；缺 `host` 判 missing-field；`host` 越域判 out-of-enum；`runner="claude-fallback"` 判 out-of-enum（已废弃）〔workflow-metrics · 锚字段缺失或取值越域被自检阻塞〕
- [ ] 2.2 实现：`anchor_lint.py` 的 `REQUIRED_FIELDS` 加 `host`，枚举校验加 `host`（枚举仍从契约机读块读，**MUST NOT 在脚本内复制清单**）〔workflow-metrics〕
- [ ] 2.3 TDD + 实现：**自审红线**——`lens="outside-voice" ∧ runner == host` 且未标降级 `reason_code` ⇒ 报错阻塞（新违规类型 `self-review`）〔host-adaptive-execution · 禁止自审；workflow-metrics · 自审锚行被自检阻塞〕
- [ ] 2.4 核验 `anchor_lint` **不判宿主**（ADR-1）：它只读锚行自身的 `host`/`runner` 字段做内部一致性校验，MUST NOT import 或调用 `resolve-models.sh`——加一条测试锁死此边界〔host-adaptive-execution〕

## 3. 产出工具（lens_metric_emit）

- [ ] 3.1 TDD：`test_lens_metric_emit.py` 加用例——`--host` 必填；缺失/越域（含 `claude-fallback`）⇒ fail-closed 非零退出；**MUST NOT 默认填 claude**〔lens-metric-emit · 缺 --host 或取值越域则 fail-closed〕
- [ ] 3.2 实现：`lens_metric_emit.py` 加 `--host` 参数（单一源，无 per-finding/per-row host）；行键升为 `(lens, host, runner, site)`；输出锚行带 `host=`〔lens-metric-emit · 计数由确定性 emitter 归约〕
- [ ] 3.3 更新 `tools/tests/fixtures/lens_metric_input.json` golden fixture 至新行键；核对 `MIN_LENS_ROWS` 一致性测试仍绿〔lens-metric-emit〕
- [ ] 3.4 回归：零-finding 行、共抓不计独立、同类型多实例算独立、finding 命中行不在 roster 则 fail-closed —— 四条既有 Scenario 在升维后仍绿〔lens-metric-emit〕

## 4. 复用守卫（outside_voice_guard）

- [ ] 4.1 TDD：`test_outside_voice_guard.py` 加用例——`runner == host`（同族）⇒ 新 reason_code `same-family`、退出码非 0，MUST NOT 复用〔outside-voice-reuse-guard · 同族 fallback 段不得复用〕
- [ ] 4.2 TDD：v1 旧锚（无 `host=`，`runner="codex"`）⇒ 读作 `host="claude"` ⇒ `runner ≠ host` ⇒ 可复用（向后兼容读，**MUST NOT 罢工**）〔outside-voice-reuse-guard · v1 旧锚无 host 字段仍可复用〕
- [ ] 4.3 实现：`outside_voice_guard.py:93` 的 `attrs.get("runner") != "codex"` 改为 `runner == host` 判同族；reason_code 枚举扩至七码〔outside-voice-reuse-guard · 三判归约为单一 reason_code〕

## 5. 聚合器双代兼容（唯一读存量的组件）

- [ ] 5.1 **先固化回归基线**：跑当前 `lens_metric_aggregate.py` 对全部存量归档报告，落基线快照（改造后须逐行一致）〔workflow-retro · 改造前后对存量归档的聚合结果逐行一致〕
- [ ] 5.2 TDD：`test_lens_metric_aggregate.py` 加用例——`runner="claude-fallback"` 旧锚读作 `(host=claude, runner=claude)`；无 `host` 字段读作 `host="claude"`；新旧锚混合仓正确分组不 parse 失败〔workflow-retro · 旧锚按兼容规则读入不丢行 / 新旧锚混合仓正确分组〕
- [ ] 5.3 实现：分组键升为 `(layer, lens, host, runner, site)` + 兼容读；`render_table` 加 `host` 列〔workflow-retro · 聚合器双代兼容读锚行〕
- [ ] 5.4 回归验证：对 5.1 的基线快照，改造后除新增 `host` 列外**每行计数逐行一致**（机验，非目测）〔workflow-retro〕
- [ ] 5.5 同步 `retro_report.py` 及其测试（若引用 runner 枚举或分组键）〔workflow-retro〕

## 6. 宿主判定 helper（新组件）

- [ ] 6.1 TDD：`sdflow-init/tests/test_resolve_models.py` —— `CLAUDECODE=1` ⇒ `HOST=claude`；`CODEX_THREAD_ID=<uuid>` ⇒ `HOST=codex`；两者皆无 ⇒ `HOST=unknown` + stderr 明示；**两者同时存在 ⇒ `unknown` + 信号冲突告警**（MUST NOT 静默取其一）〔host-adaptive-execution · 宿主判定靠正信号〕
- [ ] 6.2 实现 `sdflow-init/assets/hack/resolve-models.sh`：纯 shell（ADR-1：校验侧不需要宿主判定，故无需 Python 双实现）；`eval` 导出六个变量；档位表从 `model-tiers.md` 读，**MUST NOT 内联模型名**〔host-adaptive-execution · 模型档位按机队分列〕
- [ ] 6.3 `setup.sh` 装 `resolve-models.sh` 进 `~/.sdflow/hack/` + 测试守（**dogfood 盲区**：`skill-principles.md` 曾因 setup 只拷 `*.sh` 而漏装、仓内测试全绿——本条测试 MUST 验**安装路径**，不是仓内路径）〔host-adaptive-execution〕

## 7. outside-voice 去硬编码（安全面，改动最敏感）

- [ ] 7.1 TDD：`test_outside_voice.py` 加用例——`preflight` 探测的是 `$SDFLOW_VOICE_RUNNER` 的 CLI，**不是固定的 codex**；`HOST=codex` 时探 `claude`〔host-adaptive-execution · outside voice = 另一个机队的强档〕
- [ ] 7.2 实现：`outside-voice.sh` 的 `preflight` / `do_exec` 按 runner 分叉；**`secret_scan` / `render_prompt`（FRAME + 三条通则）/ 200KB 截断保持单份共用**，只有最终 exec 命令行一处分叉〔host-adaptive-execution · 出境安全三件套对两条路径一视同仁〕
- [ ] 7.3 TDD：**安全回归锁**——加测试断言反向路径（claude）走的是同一个 `secret_scan` 与同一个 `render_prompt`；secret 命中时**两条路径都 exit 3 拒发且不 fallback**〔host-adaptive-execution · secret 命中时两条路径都拒发〕
- [ ] 7.4 实现反向 runner 调用：`claude -p --model "$SDFLOW_VOICE_MODEL" --output-format text --disallowedTools Write Edit NotebookEdit`（只读约束等价于 codex 的 `-s read-only --ephemeral`）〔host-adaptive-execution · 只读约束按 runner 落到对应机制〕
- [ ] 7.5 实现 `HOST=unknown` ⇒ **不跑 voice** + `reason_code="host-unknown"`（fail-loud，MUST NOT 任选 runner 充作跨模型）〔host-adaptive-execution · 宿主 unknown 则不跑 voice〕
- [ ] 7.6 `outside-voice.sh` 版本号升至 1.2.0；头部契约注释同步（它是两个 review SKILL 引用的契约单一源）

## 8. 规则与 SKILL

- [ ] 8.1 改 `assets/workflow/model-tiers.md`：档位表按机队分列（Claude: opus/sonnet/haiku；Codex: gpt-5.6-sol/terra/luna）〔host-adaptive-execution · 模型档位按机队分列；spec-workflow · 模型档位映射〕
- [ ] 8.2 改 `sdflow-spec-review/SKILL.md`：锚行文法（加 `host=`）· outside-voice 调用协议引用 `resolve-models.sh` · lens-metric roster 构造带 `--host`〔spec-workflow · 跨模型 outside voice〕
- [ ] 8.3 改 `sdflow-code-review/SKILL.md`：同 8.2 + **置信豁免规则改判据**——`runner ≠ host` 豁免 <80 数值滤、`runner == host` 照过滤（`SKILL.md:172` 是旧假绿点）〔spec-workflow · outside-voice tension 不静默采纳〕
- [ ] 8.4 各编排 SKILL（ship/done/spec-review/code-review）的模型选择改引用 `SDFLOW_TIER_*` 变量，**MUST NOT 内联模型名**〔spec-workflow · 模型档位映射〕
- [ ] 8.5 SKILL 写明「Codex 宿主下 `spawn_agent` 指定 model 的 task-specific reason = 本工作流的 model-tiers（门禁步禁降档是硬约束）」〔host-adaptive-execution · 子代理不可用时镜数如实降级〕

## 9. 消费项目铺设（Codex 子代理授权）

- [ ] 9.1 `sdflow-init/assets/snippets/claude-section.md` + AGENTS.md 段加 **Codex 子代理授权声明**（多镜 fan-out + model-tiers 构成 codex 要求的显式授权）〔host-adaptive-execution · 授权声明存在〕
- [ ] 9.2 SKILL 写明「子代理不可用 ⇒ MUST 缩 roster 到实跑的镜 + 报告显著标注单镜降级」，并**如实登记该条无机械守**（ADR-4 诚实边界，MUST NOT 冒充成门）〔host-adaptive-execution · 子代理不可用则缩 roster〕
- [ ] 9.3 `sdflow-init/tests/` 加守卫：铺设产物含授权段（机验存在性）

## 10. 真机核验（假设 A1/A3 的证伪窗口）

- [ ] 10.1 **A1 核验**：在 Codex 的三种运行形态（交互 / headless / spawned subagent）各跑一次 `resolve-models.sh`，确认 `CODEX_THREAD_ID` 均存在。任一形态缺失 ⇒ 记 buglist + 在 design 补记（失效方向安全：判不出 ⇒ fail-loud，不假绿）
- [ ] 10.2 **A3 核验**：在**真实 Codex 沙箱内**冒烟 `claude -p --model opus …`（已在 Claude 宿主冒烟过 5.8s，但 Codex 的权限模型未验）。不可用 ⇒ 走 F1 同族 fallback，不阻断
- [ ] 10.3 端到端：Codex 宿主下跑一次真实评审，核对锚行为 `host="codex" runner="claude"`，且 `anchor_lint` 绿

## 11. 文档与收尾

- [ ] 11.1 同步 `docs/workflow-map.md`(:141,:150) + `docs/workflow-map.html`(:555,:563) 的字段表与枚举
- [ ] 11.2 全量 `pytest` 绿 + `bash setup.sh` 两道门（`sync_principles --check` / `gen_workflow_guide --check`）绿
- [ ] 11.3 逐面核对 design 的 **scope-check 表 9 面**全部改完（基准 3 面治：留任何一面 = 契约漂移）

---

## 测试覆盖图（TG-18）

```
  code path                                  │ 单元 │ 集成 │ 契约/回归 │ 真机
 ────────────────────────────────────────────┼──────┼──────┼───────────┼──────
  resolve-models.sh   宿主判定（4 分支）      │  ✅  │      │           │ 10.1
    ├ CLAUDECODE=1        → claude           │ 6.1  │      │           │
    ├ CODEX_THREAD_ID     → codex            │ 6.1  │      │           │
    ├ 皆无                → unknown+stderr   │ 6.1  │      │           │
    └ 冲突（两者皆有）    → unknown+告警     │ 6.1  │      │           │
  ────────────────────────────────────────── │      │      │           │
  outside-voice.sh    runner 分叉            │      │  ✅  │           │
    ├ preflight 探目标 runner CLI            │ 7.1  │      │           │
    ├ exec → codex（正向，现有）             │      │ 7.2  │           │ 10.3
    ├ exec → claude（反向，新增）            │      │ 7.4  │           │ 10.2
    ├ 🔒 secret_scan 两路径共用（安全锁）    │ 7.3  │      │           │
    ├ 🔒 render_prompt 两路径共用（安全锁）  │ 7.3  │      │           │
    └ HOST=unknown → 不跑 voice              │ 7.5  │      │           │
  ────────────────────────────────────────── │      │      │           │
  anchor_lint         锚行校验               │  ✅  │      │           │
    ├ host 必填 / 枚举                       │ 2.1  │      │           │
    ├ claude-fallback 判越域（已废弃）       │ 2.1  │      │           │
    ├ 🔴 自审红线 runner==host               │ 2.3  │      │           │ 10.3
    └ 🔒 不判宿主（ADR-1 边界锁）            │ 2.4  │      │           │
  ────────────────────────────────────────── │      │      │           │
  lens_metric_emit    行键升维               │  ✅  │      │  golden   │
    ├ --host 必填 / fail-closed              │ 3.1  │      │           │
    ├ 行键 (lens,host,runner,site)           │ 3.2  │      │   3.3     │
    └ 四条既有 Scenario 回归                 │      │      │   3.4     │
  ────────────────────────────────────────── │      │      │           │
  outside_voice_guard 复用判定               │  ✅  │      │           │
    ├ runner==host → same-family（新码）     │ 4.1  │      │           │
    └ v1 旧锚兼容读（不罢工）                │ 4.2  │      │           │
  ────────────────────────────────────────── │      │      │           │
  lens_metric_aggregate  双代兼容            │  ✅  │      │  🔁 5.1   │
    ├ claude-fallback → (claude,claude)      │ 5.2  │      │           │
    ├ 无 host → host=claude                  │ 5.2  │      │           │
    ├ 新旧混合分组                           │ 5.2  │      │           │
    └ 🔁 存量归档聚合逐行一致（回归基线）    │      │      │   5.4     │
  ────────────────────────────────────────── │      │      │           │
  setup.sh            安装面                 │      │  ✅  │           │
    └ ⚠️ 验安装路径而非仓内路径（dogfood 坑）│      │ 6.3  │           │
```

**图例**：🔒 = 边界锁（防实现漂移回旧行为）· 🔴 = 本 change 的核心红线（自审）· 🔁 = 回归基线（存量数据零丢失）· ⚠️ = 已知 dogfood 盲区

**覆盖缺口（诚实登记）**：`host-adaptive-execution` 的「子代理不可用时镜数如实降级」**无自动化测试**——ADR-4 已论证其无确定性信号，归语义层（靠 SKILL 指令 + 人读报告 + 事后 host 分组可发现性）。**MUST NOT 为它硬造一个假机械测试。**
