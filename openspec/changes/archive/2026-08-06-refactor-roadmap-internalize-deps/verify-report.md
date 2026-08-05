---
ship-gate:
  verify: PASS
  reviewed_sha: 204dd4364df2a0e8cd013f7087a585c09efea24c
---

# Verify 报告 — refactor-roadmap-internalize-deps

- 日期：2026-08-06
- change：`refactor-roadmap-internalize-deps`
- 核验盘面：`204dd4364df2a0e8cd013f7087a585c09efea24c`（工作树另有 `tasks.md` 未提交改动 = 本轮 reconcile 回填）

## 结论

**PASS** — 10 个 Requirement 全部有 `文件:行` 机验锚点，实现期聚合覆盖需求满足；无核心缺口。
2 项未勾任务（4.5 / 6.9）为依赖后续步骤的 hand-off，不判 FAIL。

> **本 change 的锚点性质**：`sdflow-roadmap` 是纯 Markdown 编排类 skill（无 `scripts/`、无 `tests/`），
> 本 change **不改任何 `.py`**。∴ 「代码出处」锚点 = 指令文本自身的 `文件:行`；本报告的每一格
> 都由本次亲自 Read / grep 打开确认，非复选框推定。两道真机械门由本次**重跑**取证（见文末）。

## 逐需求核对表

| 需求/任务 | 出处（文件:行） | 状态 |
|---|---|---|
| **ADDED** 讨论层三态路由 | `sdflow-roadmap/SKILL.md:289-330`（gate-0 五项 `:293-307` 含通过阈值 / 商业化信号 `:309-313` / 三态图 `:315-324` / 判定点①留痕时点 `:328` / 操作者覆盖 `:330`）；路由对照表 `:332-340`；七维与裁剪表 `:357-367`（含兜底行 `:367`）；总览 `:171-194`、判定留痕总则 `:196-198` | ✅ 实现 |
| **ADDED** B 相位拷问与增量落盘 | 第零步重入探测（独立 `##`、物理位于相位 A 之前）`SKILL.md:277-285`；起手三步 `:346-355`（第 3 步按 create / continue·replan 分列，`:352-355`）；七维裁剪 `:357-369`；ADR/术语提议制 + 版本锚 + 诚实边界 `:371-379`；增量落盘 `:381-383`；停止条件三终态 `:385-393`；`## 未决项` + 承接边界 `:395`；重入协议 `:397-399`；放弃清理 create vs continue·replan `:401-406`。模板侧：`references/memo-template.md:10-25`（含 create-only 限定 + FINAL 写入时机）、`:27-38`（头部 `状态：DRAFT / FINAL` + 历史存档定位声明） | ✅ 实现 |
| **ADDED** 历史存档引用边界与存量 footage 冻结 | 规则 3 定义与禁令 `SKILL.md:216-223`（存量 footage 冻结条款 `:223`）；引用关系图 `:436`；收尾 ③ `:519`；陷阱 3 `:584-590`；模板侧 `references/task-log-template.md:86` | ✅ 实现 |
| **ADDED** review 按商业化信号分档 | `SKILL.md:461-503`：分档判据（共用词表）`:465-468`；整体 plan 调用话术 + 「缺此声明视为未按契约执行」`:470-476`；跳过授权 + `review-waived` `:478-483`；显式覆盖 `:485-487`；`未审待恢复` 不静默**且阻塞收尾** `:489-493`；处置三态标注 `:495-503` | ✅ 实现 |
| **MODIFIED** 三件套直写产出 | 规则 4 `SKILL.md:225-229`；产出模式节 `:239-273`（存量四件套兼容 `:241-247` / 缺件存量包 `:249-255` / `requirements.md` 逃生舱 `:257-259` / 生命周期判定前移 `:261-273`）；相位 C 直写与文件表 `:410-427`；收尾 ② 对缺件判「不适用」`:517` | ✅ 实现 |
| **MODIFIED** 收尾 checklist 软门 | `SKILL.md:507-529`：① Review 处置（脚本机械断言 + 信任边界声明）`:511-515`；② 最小引用图 + N/A 第三态 `:517`；③ 历史存档未被引用 `:519`；④ memo 对账（版本锚归属核验）+ 未决项闭环 `:521-523`；`FINAL` 只在四项全过后写入 `:525`；memo 不存在判「不适用」的诚实边界 `:527`；软提示纳入版本控制 `:529` | ✅ 实现 |
| **MODIFIED** roadmap.md 近细远雾分层 | `SKILL.md:441-457`（近期 1-2 阶段五节 + 取 1/2 理由 `:443`；雾区备注写「缺什么信息」`:445`；长周期依赖例外 `:447-449`；补细重判分档 `:451-453`；前序放弃视为已处置 `:455-457`）；模板侧 `references/roadmap-template.md:27,123` | ✅ 实现 |
| **REMOVED** 讨论层按规模分档路由 | 机制确已消失：`grep -n "office-hours\|三分支路由\|铺图\|preflight\|基线记录\|map 再入" sdflow-roadmap/SKILL.md` → **零命中**（唯一 `铺图` 出现在 `:223` 的「旧版本的 wayfinder 铺图路径已移除」历史陈述内）。承接锚：三态路由 `SKILL.md:315-324`、memo 增量落盘 `:381-383`、`opsx:explore` 降为上游可选步 `:291` | ✅ 实现 |
| **REMOVED** footage 落盘位置与引用边界 | 产出机制确已消失：SKILL.md 全文 `footage` 仅 7 处，全部为「存量冻结 / 不引用」语境（`:218,220,221,223,436,519,586`），无任何 map / 票 / 命名权 / 持久字段 / triage 排除机制。`openspec/matt/` 整目录已删（`ls` → No such file）；`CLAUDE.md` / `AGENTS.md` 的 matt 三区块 grep 零命中；Migration 侧 legacy 标注 `sdflow-init/assets/workflow/ff-generation-constraints.md:48-52`、演进记录 `workflow-history.md:34-50` | ✅ 实现 |
| **REMOVED** review 按项目野心分档（更名） | `grep -n "野心" sdflow-roadmap/SKILL.md` → **零命中**；承接后的新术语见 `SKILL.md:461-468`；术语词条 `openspec/CONTEXT.md:183-184`（「商业化信号（原「产品/商业野心信号」）」） | ✅ 实现 |
| **实现期聚合覆盖**（tickets 轨） | `impl-reports/task6-implementation-verification.md`：权威结论在后半「编排层收口全量跑」节 `:264-289`。三层证据 schema 齐全（unit / integration / e2e 各一行，含命令原文 · 退出码 · SHA）；**唯一「通过」层（unit）锚 `e1459716832c598f4eeb18e46e5db71dc08e59c9`，无跨 SHA 不一致**（integration / e2e 记「未覆盖」并附本仓无此层的判定依据，非 fail-closed 罢工）。锚语义为「实现期结束时聚合套件相对 merge-base 无新增失败」（2 failed 均逐条定性为 baseline），**未**表述为「最终代码通过全量回归」。该票不产 commit（干净树上 `checkpoint-commit.sh` 不建 commit），已在报告 `:7` 显式声明 | ✅ 实现 |

### 治理面 / 支撑任务补充锚点（非 Requirement，但属 tasks.md 交付物）

| 任务 | 出处 | 状态 |
|---|---|---|
| 1.9 principles 托管块零字节未动 | `sync_principles.py --check` 本次重跑退出码 **0**（`✅ 20 个投放面全部与真相源一致`） | ✅ |
| 1.10 「保留」节内嵌待删机制清理 + 6.6 逐句核对 | `impl-reports/task1-skill-rewrite.md:56` 起「6.6 逐句核对」表；复核：SKILL.md 规则 1 `:204-208`、规则 5 `:231-235`、命名规范 `:533-539`、下游阶段实施 `:543-562`、陷阱 1 `:568-574`、CLAUDE.md 配合 `:618-626`、参考模板 `:630-640` 均无指向已删机制的活引用 | ✅ |
| 1.11 「实战案例：博客 v2 重建」显式处置 | 处置 = **删除**，记录于 `impl-reports/task1-skill-rewrite.md:41`；`grep "实战案例\|博客 v2 重建" sdflow-roadmap/SKILL.md` 零命中，规则 1 / 陷阱 4 的旁证括注同步移除 | ✅ |
| 2.3 long-flow-skill-paradigm 改历史注记 | `references/long-flow-skill-paradigm.md:69-71`、`:116-119`（均已改为「历史注记 … 2026-08 迭代已整体移除」） | ✅ |
| 4.1 / 4.2 / 4.3 bundle 同步 | `ff-generation-constraints.md:46-52`（前缀保留 + legacy 块）；`workflow-history.md:34-50`（A4，含 SR-33 订正后的「同批非同因」因果表述）；`config.template.yaml` 陈旧引用 grep `wayfinder\|衔接契约` **零命中** | ✅ |
| 5.1 ADR | `openspec/adr/0037-roadmap-discussion-layer-internalization-and-matt-removal.md`（编号连续于 0036；`:26-29` 明写 matt 与本重构**无因果关系**） | ✅ |
| 5.2 CONTEXT.md 三词条 | `openspec/CONTEXT.md:179-181`（历史存档，含「决策生成」改词）、`:183-184`（商业化信号）、`:187-189`（ticket 词条改历史存档语境 + `_Avoid_` 行同改） | ✅ |
| 5.3 T134 关 WONTDO | `openspec/issues/closed/todo/T134.md` frontmatter `status: "WONTDO"` + `closed_reason` 已填（`--reason` 路径） | ✅ |
| 5.4 external-dependencies | `docs/external-dependencies.md`：§5 Wayfinder 节已无（章节列表 `:70-86` 只余 gstack 系列），`:81-83` 记内化说明；§8 依赖图 `:148-149` 已改为「讨论层已内化，无其他外部依赖」 | ✅ |
| 5.5 INDEX.md 摘要行 | `openspec/INDEX.md` 的 `roadmap-planning` 行已整句重写（三态路由 / 历史存档 / checklist 四项 / 第零步重入探测），无 wayfinder / 野心 / 五项软门残留 | ✅ |
| 5.6 fable5 §4.6 | `docs/sdflow-fable5/02-module-reference.md:200-212`（三相位 + 第零步 + 三态路由 + 历史存档 + checklist 四项；wayfinder 仅以「已内化」的过去式出现） | ✅ |
| 5.7 删 drafts hand-off | `docs/drafts/` 下已无 `roadmap-refactor-handoff.md` | ✅ |
| 6.1 / 6.4 / 6.5 / 6.8 | `impl-reports/task5-residue-scan-drills.md`：6.1 结论 `:78`（非白名单残留为零）；6.4 fixture 演练 `:82` 起；6.5 真实缺件包演练 `:171-200`；6.8 六×三共 18 格逐格锚行 `:208` 起，全部有 SKILL.md 行号依据 | ✅ |
| 代码审残差闭环 | `code-review-report.md`：F1–F5 已自动修（commit `8761cf4`），F6 defer → `openspec/issues/open/todo/T266.md`；另有 `B24` / `T265` 于双轴审阶段 defer | ✅ |

## 本次亲自重跑的机械门（不依赖报告自述）

| 门 | 命令 | 退出码 | 盘面 |
|---|---|---:|---|
| principles 一致性 | `/usr/bin/python3 hack/sync_principles.py --check` | **0**（`✅ 20 个投放面全部与真相源一致`） | `204dd436` |
| change 结构合法性 | `openspec validate refactor-roadmap-internalize-deps --strict --type change` | **0**（`Change '…' is valid`） | `204dd436` |

> 两道门在 Task 6 报告中锚于 `379de34`；本次在**含代码审修复（`8761cf4`）之后**的 HEAD 上重跑，仍绿
> ⇒ 覆盖了 Task 6 之后的 SKILL.md / 模板改动，消除了该时效缺口。
> 全量 pytest **未重跑**（本机 >280s，且本 change 自 merge-base 起 `.py` 改动为 0 ⇒ 输入集与 Task 6
> 收口跑逐字节相同），以 Task 6 收口证据（`e145971`，`2 failed, 2449 passed, 10 skipped`，2 条均 baseline）为准。

## 缺口清单

### 核心缺口（FAIL 项）

**无。**

### Minor 缺口（可接受 / deferred）

1. **`docs/external-dependencies.md` 的行号引用漂移**（`:142-144` 指 `sdflow-roadmap/SKILL.md:459/460`，实际 review 分档节现位于 `:461-468`）。属 `T265`（跨文件行号引用脆弱耦合）已登记的同类问题，不阻塞。
2. **F6 — 直接生成路径（第①态）中途缺判据时无「回退相位 B」转换定义**：已 defer 至 `openspec/issues/open/todo/T266.md`（带 `source_change`）。
3. **`tasks.md` 6.2 的 baseline 登记回填**：第 2 条 baseline（`test_subprocess_encoding_contract.py::test_text_mode_subprocesses_declare_utf8_and_replace`，`assert sites >= 200` 实测 189）已在本轮 reconcile 中回填进 `tasks.md:71`（工作树未提交改动，随本次 done 一并落）；其根因（排除清单漏 `.claude`、硬编码阈值）已记 `B24`，本 change 不修（不改任何 `.py`，修它属加宽）。
4. **指令层无自动化测试面**：`tasks.md` §6 测试覆盖图与诚实边界声明已如实登记——三态路由 / 七维裁剪 / 增量落盘 / 重入 / 放弃清理均无机械门覆盖，唯一防线是人读（6.6 逐句核对 + 6.8 十八格）。**这是合法的残余划分，不是本次可补的缺口**；本报告的每格锚点即按此标准逐条打开确认。

### Hand-off（未勾项，非缺口）

| 任务 | 内容 | 依赖 |
|---|---|---|
| `4.5` | 合并后在运行 checkout（`~/.skills/sdflow-skills`）重跑 `setup.sh` / `/sdflow-upgrade` 还原 | 依赖 push → 运行 checkout pull → setup 链路；本次收尾**不 push**，本轮无法完成 |
| `6.9` | archive 后对提升进 `openspec/specs/roadmap-planning/spec.md` 的结果重跑 6.1 词表扫描 + 逐 Requirement 与 SKILL.md 对码 | 依赖本次 done 的 archive 步；archive 完成后由主 session 补跑并回填 |

---

**PASS**
