---
impl-pipeline: tickets
---

## Global Constraints

以下逐字摘自该 change design.md 的 MUST/MUST NOT/SHALL 硬约束与 Compliance 条款：

- **Goals 边界**：裁决协议改动收敛在两个评审 SKILL 的 Step3 段 + 一个新机械脚本；处置机制收敛在一个数据文件 + `retro_report.py` 一处消费；终态快照零新采集路径。
- **Non-Goals**：不改 lens-metric 锚**字段集**（合法组合矩阵扩展除外〔设计门 Q1〕）；不改 Step1/Step2 编排结构（roster 段只加派发条件行）；范围级 Non-Goals 见 proposal。
- **DD1 解析手段**：`retro_report.py` 读取 YAML 走 yq（同 `anchor_lint.py` `_yq()` idiom，承 adr/0036），**MUST NOT `import yaml`**——保持仓内「零第三方依赖 + YAML 读取点收敛」惯例。
- **DD1 错误语义**：文件缺失 = 零注记照旧 flag（向后兼容）；yaml 坏 / disposition 非法 ⇒ fail-loud 非零退出（宁红勿静默）；未命中键 ⇒ 告警不阻断。淘汰态 = roster 段整段移除该镜派发逻辑，yaml 条目保留作历史注记。
- **DD2 锚行必落**：条件化派发判「本轮不派」的镜 MUST 照落锚行（`runner="none"`、`findings=0`）。`condition-not-met` **不作为锚字段**——跳过成因由 `mirror-dispositions.yaml` 的 `condition` 字段（机读）+ 报告散文承载。
- **DD4 输入契约**：validator 脚本**只吃结构化 JSON**（`{file, line, quote}` 或 `evidence_pack`），**MUST NOT 解析 markdown 散文**。输出三态 pass/fail/uncheckable。脚本级崩溃 = 显式降级（`[ref-check-unavailable]`），MUST NOT 静默 fail-open。
- **DD4 引文核验**：引文 MUST 命中所报行（或显式行范围），MUST NOT 只检查整文件子串匹配。
- **DD5 三类归因法**：重裁不一致项归因三类——①历史误标②模型方差③协议缺陷。红线 = ③类 = 0。
- **DD6 处置表**：grounding **恒跑**（Q3 拍板撤回降采样）；history 降采样；具体阈值与判定命令随 roster 段落盘。
- **Risks 上界兜底**：合并池 > 100 条时分批裁决（每批 ≤50，批间携带已裁清单防重复采纳）。
- **Migration Plan 步序**：commit B（裁决面）→ 历史重放（部署门）→ commit A（roster 面）→ done 终态快照 → 集成收尾。commit A / B 互相独立可分别 revert（C3）。
- **Compliance**：四条通则；DOC-1（正文即最终态）；premise-verification（代码事实均实读核验）；lens-metric contract §enum 扩展治理（DD2 升版本）；报告工具反静默方向 adr/0016。

### Task 1: Validator 机械脚本

**Blocked-by:** none
**R-ID:** R-裁决

新建 findings 引用核验机械脚本（落 bundle `tools/` 同类脚本旁），实现三查 + 三态输出 + 崩溃降级。

**行为**：
- 输入：结构化 JSON，每条 finding 带 `{file, line, quote}` 或 `evidence_pack` 机读字段
- 三查：① 引用路径存在 ② `file:line` 落在文件行数内 ③ 单行引文命中所报行或显式行范围（MUST NOT 只检查整文件子串）
- 三态输出：`pass`（三查全过）/ `fail`（结构化字段在、任一不过）/ `uncheckable`（引用为证据包/设计层引用，非干净 `path:N` 形态 ⇒ 不裁，原样直进强档裁决）
- 「无引文且无证据包」（结构化字段确认皆缺）→ 机械裁掉
- 脚本级不可恢复错误（crash / 输入 JSON 畸形）→ 显式降级：整批标 `[ref-check-unavailable]` 直进裁决 + 报告显著标注机械门未生效，MUST NOT 静默呈现全部 pass
- 输出遵循消费型信号校验器输出诚实（不 emit 裸通过码）

- [x] 正例（路径存在+行号合法+引文命中该行）返回 pass
- [x] 三种失败态（路径不存在/行号越界/引文不在所报行）各返回 fail
- [x] 无引文且无证据包态返回机械裁掉信号
- [x] uncheckable 态（证据包/设计层引用/行范围外形态）返回 uncheckable
- [x] 脚本级崩溃（输入 JSON 畸形/意外异常）→ 显式降级标 `[ref-check-unavailable]`
- [x] 输出码形态符合信号内诚实
- [x] pytest 覆盖上述 6 个场景

### Task 2: 合法组合扩展 + Roster 条件化 + 处置系统

**Blocked-by:** none
**R-ID:** R-roster, R-裁决, R-处置

实现 DD2 合法组合矩阵扩展 + DD1 处置记录 + DD6 roster 条件化 + retro_report.py 处置注记——四件串联成一条「让镜可以条件化跳过且跳过可审计」的垂直切片。

**A. 合法组合矩阵扩展（DD2/设计门 Q1）**：
- lens-metric contract 升版本，新增合法组合「普通镜行 `runner="none"` ∧ `findings=0`」
- emitter 非-outside-voice 分支接受该组合（原强制 `runner==host` 加旁路）
- anchor_lint 普通镜行校验同步接受该组合
- emitter 输入侧兼容（findings JSON 含置信字段时不报错）

**B. 处置记录（DD1）**：
- 创建处置数据文件（yaml，DD1 schema: `{layer, lens, host, runner, site, disposition, condition, date, rationale}`）
- 填入 DD6 拍板后的 13 面镜处置（1 降采样 + 11 保留 + 1 不适用，grounding 恒跑）

**C. SKILL roster 段条件化（DD6）**：
- 两评审 SKILL roster 段：降采样镜（code-review history）加派发条件行，给出阈值具体取值与判定命令
- 条件跳过轮落锚 `runner="none" findings="0"` + 报告一行说明

**D. retro_report.py 处置注记（DD1 消费）**：
- 读处置数据文件，命中镜行内追加处置注记
- 错误语义分治：缺失=零注记 / 坏yaml=fail-loud / 未命中键=告警不阻断
- 解析走 yq（MUST NOT `import yaml`）

- [x] contract 含新合法组合且版本号已递增
- [x] emitter 接受 `runner="none" ∧ findings=0` 普通镜行不报错
- [x] anchor_lint 对该组合判合法
- [x] emitter 对含置信字段的 findings JSON 兼容
- [x] 处置数据文件含 13 面镜完整记录且 schema 合规
- [x] 降采样镜条件阈值为具体数值与命令，非定性词
- [x] retro_report.py 对命中镜行追加处置注记
- [x] retro_report.py 对缺失/坏yaml/未命中键三态各正确处置
- [x] pytest 覆盖 retro_report.py 处置注记四态

### Task 3: 裁决协议重写 + 联动核查

**Blocked-by:** 1,2
**R-ID:** R-裁决, R-voice, R-全跑

重写两评审 SKILL 的 Step3 裁决段为「机械前置 + 二元裁决 + 置信降排序」，联动核查全仓消费点。

**A. sdflow-code-review Step3 重写**：
- 删除：<80 数值滤、置信封顶 ≤50、跨模型豁免矩阵条款
- 新增：接入 validator 机械前置（三态处理）+ 二元裁决（采纳/裁掉/defer + critique）+ 置信仅排序
- 「已裁掉」区新增 `[ref-check]` 来源标记
- frontmatter description Step3 括注改「机械引用核+二元裁决」（显式删「(<80 滤除)」）
- Step2 各镜 prompt 输出契约改为强制结构化字段（`{file, line, quote}` / `evidence_pack`）
- 合并池 > 100 条时分批裁决（每批 ≤50，批间携带已裁清单防重复采纳）

**B. sdflow-spec-review Step3 对齐**：
- 裁决动作层对齐同 A 的三层协议
- 保留「拿不准 → 决策登记区」路由并与置信数字脱钩
- Step2 输出契约同步改结构化字段

**C. spec-workflow 主 spec 联动核查**：
- grep 全仓「置信过滤 / <80 / 豁免」消费点，逐处改齐或确认不动

- [ ] sdflow-code-review Step3 不含 <80 数值滤/封顶 ≤50/跨模型豁免矩阵
- [ ] sdflow-code-review Step3 含 validator 接入 + 二元裁决 + [ref-check] 标记
- [ ] sdflow-code-review frontmatter description Step3 括注已更新
- [ ] sdflow-code-review Step2 各镜 prompt 要求结构化 findings 输出
- [ ] sdflow-spec-review Step3 裁决动作层与 code-review 三层协议对齐
- [ ] sdflow-spec-review 保留「拿不准→决策登记区」路由
- [ ] 全仓 grep「置信过滤/<80/豁免」无遗漏残余消费点

### Task 4: 历史重放部署门

**Blocked-by:** 1,3
**R-ID:** R-裁决

对历史归档报告重跑新裁决协议，验证误杀率红线。

**行为**：
- 选 3-5 份归档评审报告，`git worktree` checkout `reviewed_sha`
- 提取 findings → 逐条过 validator 脚本 + 强档二元重裁 → 与历史裁决对表
- 不一致项逐条归因入三类：①历史误标/口径漂移（剔除分母，记归因证据）②模型方差（复裁一次，二次仍不一致才计入）③协议缺陷（真误杀）
- 产出重放报告（一次性，不进常驻资产）
- **关门判据**：③类（协议缺陷）= 0；①②类如实报数不挡部署
- 噪声重入率标「参考」（C4 语料限制如实写明）

- [ ] 选取 3-5 份归档报告并完成重放
- [ ] 重放报告含逐条归因（三类分类 + 证据）
- [ ] ③类（协议缺陷）= 0
- [ ] 重放脚本/流程落 impl-reports/replay/（非常驻资产）

### Task 5: Done 终态快照接线

**Blocked-by:** none
**R-ID:** R-快照

在 sdflow-done 收尾流程接入终态 token 快照采集点。

**行为**：
- sdflow-done 第三步（Archive）起手前、change 目录尚在原位时，调 `token_snapshot.py --step done-final`（anchor=true）
- 追加进 change 目录 token-log.jsonl，随 archive 搬走
- 失败显式降级不挡收尾（同既有口径）
- 残余盲区（archive/commit/merge 自身用量）在契约文档如实声明
- host 判定补丁：codex/unknown 宿主不走 Claude transcript mtime fallback，直接落显式降级行
- `done-final` step 值入契约文档
- retro join 对该行可读（冒烟）
- 已知边界声明：done 收尾跨 session 重试时 token 统计可能重复计入（view-only 精度边界）

- [ ] sdflow-done SKILL 第三步起手含 token_snapshot 调用接线
- [ ] 失败显式降级不挡收尾流程
- [ ] codex/unknown 宿主不走 Claude mtime fallback，直接显式降级
- [ ] done-final step 值记入契约文档
- [ ] retro join 对 done-final 行可读

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，同时验证集成一致性。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] bundle 权威源一致性：所有规则改动确认落 bundle 权威源（非仓内副本）
- [ ] sync_principles.py --check 绿
- [ ] anchor_lint 全绿（真实锚样本回归）
- [ ] 全仓 pytest 绿
