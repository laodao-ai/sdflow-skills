# code-review 报告 — sdflow-ship

> 2026-07-04 · impl-review 编排器（每次全跑·独立冷·强制主审）· diff = aa25c69..HEAD（22 commits + 本轮 fix 工作区）
> Step1 gstack/review 以**模拟（降级模式）**子代理执行 scope-drift+完成度审计——T25 已记原生化债务，此处显式留痕（反静默守卫）。

### 命中范围

栈: bash/python 工具链（TG-01）——领域清单零命中，仅过通用 base CR-01~09（SDD 终审已逐条过，本轮不重复计数）。
镜: Step1 审计镜（scope-drift/完成度，模拟降级）+ 对抗镜×3（运行期 git 边界 / 契约漂移假绿 / prose-脚本一致性）+ 历史镜×1。
gstack/review 结论: **无 scope 漂移**（39 文件全部归因 plan/流程产物；review.html 为 CLI hook 自动产物有据）；**完成度 16/16 落实**（逐项带证据）。
历史镜: 6 个 fix 轮范围精准、rebrand 成果零回潮、无 revert 重蹈、契约头注释本源干净——全过。

### Findings（置信 ≥80，全部已修 [impl-review-fix]）

- [高] run_git 吞错致 D9 静默失效 | ship_gate.py（原 :63-66）| 非 git 仓/git 故障被伪装成 fresh 放行，实测复现 | 置信 95 | 已修：decide() 前置 git 健全性检查 → UNKNOWN exit6 + test_non_git_root_unknown
- [高] TAG_RE 将 revert commit 误计为任务完成 | ship_gate.py（原 :131,148-150）| `Revert "checkpoint(task1-…"` search 命中，实测复现 | 置信 90 | 已修：行首 startswith + match 锚定 + test_revert_commit_not_counted
- [高] BARE 断言正则中文粘连漏检 | test_model_tiers.py:9 | "用sonnet跑" 因 `\b` 对中文 `\w` 失效而漏检，实测复现；另全大写变体绕过 | 置信 95 | 已修：`(?<![A-Za-z])…(?![A-Za-z])` + IGNORECASE
- [中高] 非 UTF-8 报告 → 未捕获 traceback | ship_gate.py 四处 read_text | GBK 报告直接崩（exit 1 无 JSON），实测复现 | 置信 90 | 已修：errors="replace"（ASCII 锚行不受影响，头注释记）+ test_gbk_report_no_crash
- [高] 熔断计数属 prose 记忆，与 adr/0006(b) 张力未声明 | sdflow-ship/SKILL.md 熔断句 | 弱模型混淆"重试计数"与"步序记忆"→ 静默无限重跑或漏计 | 置信 85 | 已修：显式例外边界声明句（步序判定已全在 gate，计数为单 invocation 短时量）；长期脚本化方案 defer→T26
- [中] 白名单整行豁免可"夹带"裸模型名 | test_model_tiers.py:24 | 裸名与引用句同行即绕过断言 | 置信 90 | 已修：删除白名单 skip（四 SKILL 引用句本身零裸名，全文零命中收紧成立）
- [中] freshness 裸键零断言锚定 | test_gate_freshness.py | 键名 typo/误删测试不红 | 置信 90 | 已修：stale/uncommitted 两断言（修复中发现原 uncommitted 用例实测走 fresh 分支——已改造为真不提交，语义纠偏）
- [中] plan 删后重建窗口锚最早 add 混入旧标签 | ship_gate.py plan_first_sha | 实测复现 | 置信 85 | 已修：取最新一次 A 记录（[0]）
- [中] RERUN_STALE/STEP_IN_PROGRESS 动态 next 未教读 JSON | sdflow-ship/SKILL.md:26 | 弱模型照摘要猜目标步 | 置信 85 | 已修：两处加「目标步=JSON next 字段值」句
- [中] gate 调用兜底句省略号致拼接错 | sdflow-ship/SKILL.md:14 | Codex 侧兜底路径不完整（主路径 404 属未激活预期，hand-off 已预置激活步） | 置信 85 | 已修：三级完整路径（claude → codex → 仓内）
- [中] merge 透传词与 done 捕获词表零字面重合 | ship SKILL:19 ↔ done SKILL:34 | "跑到 merge 前停"可能漏判误默认 merge | 置信 80 | 已修：透传句改为归一化为 done 词表短语
- [低中] plan 标题重号时 N 计数与 done 集口径不一 | ship_gate.py plan_task_count | 重号致永久 CONTINUE_IMPL（checkbox 可兜底） | 置信 85 | 已修：len(set(…))
- [低] tasks.md 复选框全未勾 | tasks.md:9-40 | 属 /sdflow-done reconcile 时序内正常态 | 置信 100 | 不修：交 done 0.3 对账（勿跳过）

### 已裁掉（反静默压制，可审计）

- X1 「新模型家族 gpt/claude-x 不在 BARE 检测」——三档体系作用域边界，设计内（对抗镜2 自证 refuted）。
- X2 「锚行契约测试包含级非区块级」——SDD 终审已 triage 可留；区块级解析成本>收益，记加固点不动。
- X3 「test_skill_text/workflow_authority 关键词脆度」——关键词类测试通性代价，误报网仍在，非新缺口。
- X4 「workflow.md "5.5→9" 与 final 查 archive 语义」——对抗镜3 自证 refuted（workflow.md:77 归档合并本属步9 产出物）。
- X5 「branch_state log 失败误判 merged」——与 run_git 修复同源根治，单列不再计。
- X6 「symlink 报告/相对 --root/plan rename」——对抗镜1 实测未复现，refuted。

### 修复 / defer 台账

自动修 12 项 [impl-review-fix]（ship_gate.py×5、tests×4、SKILL.md×4 处措辞——见上表）；
自动选推荐 1 项（附理由）：熔断计数处置 = 显式例外声明而非 gate 写状态——T10 一级协议（客观判据 = D1「gate 零副作用」为设计门拍板硬约束，写状态方案客观违约被排除；声明句为唯一不违约即时项）；
T10复核: 熔断例外声明 vs gate写attempt状态 | 对抗镜结论 通过（D1 约束客观排除后者，无需二级复核） | 零副作用是拍板红线，计数下沉另行设计
defer 1 项 → todolist **T26**（熔断重试计数脚本化方案探索，含 D1 矛盾解法候选）。

验证：`python3 -m pytest sdflow-ship/tests/ -q -W error` → **44 passed**；`python3 -m pytest -q` 全仓 → **277 passed**（均无 warning）。

### 结论

☑ 建议进 /sdflow-done（verify → hand-off → archive → commit → merge）
☑ defer 残差已入 todolist（T26；hand-off 会引用）

<!-- ship-gate: code-review=pass -->
