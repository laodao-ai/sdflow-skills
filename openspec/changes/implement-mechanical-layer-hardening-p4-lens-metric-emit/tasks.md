# Tasks: lens-metric 计数确定性 emitter

> 实现走 TDD（先写失败测试 → 最小实现 → 绿）。脚本落 `sdflow-init/assets/workflow/tools/lens_metric_emit.py`（bundle 权威源），测试落 sibling `tests/`。禁 import yaml / lens_metric_aggregate / ship_gate（消费仓无）；**禁读 config**（门控外置 ADR-10）。
> 〔spec-review-amendment〕两次面治：Pass 1 输入契约（行键粒度 + 权威 schema + 坏输入穷举）；Pass 2 单一源系统扫。

## 1. 契约枚举 + 折叠块读取（单一源，follow anchor_lint）

- [ ] 1.1 写失败测试：`load_enums` 从 `lens-metric-enums` fenced 块读 layer/lens/runner + sev-format 正则；缺块/空块 → `EnumsError`（fail-closed）。
- [ ] 1.2 实现 `load_enums`（重实现 fence-aware 读取，MUST NOT import anchor_lint/aggregator）；测试转绿。
- [ ] 1.3 写测试断言：emitter 内**无**硬编码 layer/lens/runner/折叠清单（均从契约读）；`sev` 输入级从 `sev-format` 模板解析、非硬编码〔C15〕。`verdict` 枚举 MAY 本地常量，但代码注释须引 design ADR-11 豁免理由。
- [ ] 1.4 〔ADR-7〕在 `lens-metric-contract.md` **新增 `lens-metric-fold` 机读块**（同 enums 块格式，`原始镜名: canonical-lens` 映射，**只列非恒等**：`对抗镜1/2/3→adversarial`、`领域镜→domain`、`历史镜→history`、`接地镜/完整性镜→grounding`、`codex/claude-fallback→outside-voice`、`autoplan子声/gstack-adv→broad`）；补 prose 注记「折叠单一源=此块；恒等由 `raw∈lens_enum` pass-through 承载、不列本块」（**不改枚举、不升版本**）。
- [ ] 1.5 〔ADR-7〕写失败测试 + 实现 `load_fold` 从 `lens-metric-fold` 块读映射；缺块 → fail-closed；**读入后自校验 codomain⊆`lens-enum`**、越界 fail-closed〔C3〕；重复/冲突 raw 键 → fail-closed〔C14〕。

## 2. 归约核心（折叠 + 归属 + 独立 + sev rollup，行键粒度）

- [ ] 2.1 写失败测试：单条 `采纳` finding、`hits=[{raw:"domain"}]` → 输出一行行键 `(domain,claude,—)` 锚，`findings/采纳=1`、`独立=1`、`sev=致0/高1/中0/低0`（若 sev=高）。
- [ ] 2.2 〔ADR-7〕实现折叠 `fold(raw)= raw if raw∈lens_enum（恒等 pass-through）; elif raw∈load_fold; else fail-closed`（非脚本内硬编码）；测 `domain` 恒等直通、`对抗镜2` 映射、未知 raw fail-closed（不静默塞 broad，SR-E）。
- [ ] 2.3 〔ADR-8〕写失败测试 + 实现归属：per-finding 每 hit 折叠成**行键 `(lens,runner|claude,site|—)`**（集内去重），每命中行键记 `findings/{采纳|裁掉|defer}` +1。
- [ ] 2.4 〔ADR-8〕写失败测试 + 实现独立：`|去重行键集|==1 ∧ verdict==采纳` → 该行键 `独立` +1；共抓（集大小≥2，如 `(domain,claude,—)`+`(outside-voice,codex,hr-tg)`）不计任一独立。
- [ ] 2.5 写失败测试 + 实现「同类型多实例算独立」：`hits=[{raw:"对抗镜1"},{raw:"对抗镜2"}]` 折叠后同为 `(adversarial,claude,—)`、去重集 size==1 → `adversarial` 行 `独立` +1。
- [ ] 2.6 写失败测试 + 实现 sev rollup：每行键按**采纳项** sev 级累加成 `致N/高N/中N/低N`（四级定序、零写 0、分隔恒 `/`）；裁掉/defer 项不计入 sev；**自校验不变量 `Σ(致+高+中+低)==采纳`**、不符 fail-closed〔C12〕。
- [ ] 2.7 〔ADR-8〕写失败测试 + 实现 outside-voice site 分行：`hits` 带 `{raw:"codex",runner:"codex",site:"hr-tg"}` vs `site:"code-voice"` 各落独立行键；非 outside-voice runner=claude/site=—（由 fold 恒定补）。
- [ ] 2.8 〔ADR-1/ADR-5 升行键〕写失败测试 + 实现 **roster 恒落行**：为 `roster` 中每个**行键**落一行，零-finding 行落全零行（runner/site 取自 roster 行键）；被调即视 metrics-on、roster 缺 `broad`/`outside-voice` → fail-closed（对齐 anchor_lint MIN_LENS_ROWS）。
- [ ] 2.9 〔C4 反方向〕写失败测试 + 实现不变量：**所有 finding 折叠出的行键 MUST ⊆ roster**，否则 fail-closed 报明「finding 命中行 X 不在 roster」（杜绝静默漏计）。

## 3. 输入校验 fail-closed（schema 驱动穷举）

- [ ] 3.1 写失败测试：非法 JSON / 缺必填字段（无 `hits`/`verdict`）→ 非零退出 + stderr 含被拒字段名 + 失败类别；MUST NOT 产锚、MUST NOT exit 0。
- [ ] 3.2 写失败测试 + 实现：`verdict` 越域（如 `通过`）/ 折叠后 `lens` 越域 / `runner` 越域 / `sev` 级非法 → fail-closed。
- [ ] 3.3 〔ADR-9〕input schema **无 per-finding `layer`**；写测试断言 finding 无 layer 字段、锚 layer 恒取 `--layer`。
- [ ] 3.4 〔C11〕写失败测试 + 实现：`hits:[]` present-but-empty → fail-closed（非空数组），MUST NOT 使该 finding 0 贡献。
- [ ] 3.5 〔C12〕写失败测试 + 实现：`verdict==采纳` 缺/空 `sev` → fail-closed（条件必填）。
- [ ] 3.6 〔C7〕写失败测试 + 实现：`site` 含 `"`/换行/`-->`/`=` → fail-closed（消毒防注入绕过 anchor_lint）。
- [ ] 3.7 〔C13〕写失败测试 + 实现 **all-or-nothing**：一批 findings 第 N 条坏 → stdout **无任何锚行** + 非零退出（先全校验再整体 emit，前 N-1 行 MUST NOT 已写出）。
- [ ] 3.8 〔C14〕写失败测试 + 实现：roster 重复行键 → fail-closed。
- [ ] 3.9 〔ADR-10〕写测试断言 emitter **不读 config**（门控外置，无 `--metrics-on`/无 config 读取路径）；被调即视 metrics-on。

## 4. 产出↔校验/聚合一致性（ADR-2 / ADR-4 / ADR-11）

- [ ] 4.1 〔C5 收窄〕写测试（emit-then-lint）：emitter 对合法输入产锚 → 跑 `check_lens_metric` 断言无违规（**或**对预置 outside-voice/hr-tg/step1-broad-review 三 MANDATORY 锚族 + emitter 行的完整报告跑 `anchor_lint --layer L` 断言 exit 0）。MUST NOT 断言「emitter 单独输出过 anchor_lint 整门 exit 0」。
- [ ] 4.2 〔C3 守卫方向修正〕写一致性测试（源仓）：① `fold_codomain ⊆ enums.lens` **且** `enums.lens` 每值可被 fold 命中（双向）；② `lens_metric_aggregate.LENS_ENUM==enums.lens` 且 `LAYER_ENUM==enums.layer`（纳硬编码副本入守卫，C23）。
- [ ] 4.3 〔C10〕写等价性测试：`emitter.load_enums(contract) == anchor_lint.load_enums(contract)` 逐字段（layer/lens/runner 集合 + sev 正则）相等。
- [ ] 4.4 〔C17 分叉①=B〕写一致性测试：emitter 的 mandatory-rows 强制集 `== anchor_lint.MIN_LENS_ROWS`（守二者漂移，不提升契约块）。
- [ ] 4.5 〔F5/C9〕写幂等测试：同一输入两次 emit 字节一致；**跨独立 subprocess** 调用比对（或参数化 `PYTHONHASHSEED=0/1/random`），堵单进程 set 序假绿盲区；输出行序按确定键（如 lens enum 序+runner+site）。

## 5. 两审 SKILL 落锚步接 emitter

- [ ] 5.1 改 `sdflow-spec-review/SKILL.md` Step3 落锚步：由「手折叠+手数+手写锚」改为「构造**行键 roster + hits findings**（引权威 input schema）→ 调 `lens_metric_emit` → exit 0 才落 stdout」；**门控关时不调 emitter**〔ADR-10〕；**保留**残余信任边界声明（分类正确性 + roster 完备性 + JSON 誊写仍是主 session 边界）。
- [ ] 5.2 改 `sdflow-code-review/SKILL.md` Step3-5 落锚步：同 5.1（含行键 roster 构造 + 门控 + exit 码检查）。
- [ ] 5.3 核对两 SKILL 落锚步：emit 与 `check_lens_metric`/anchor_lint 两步都在；引 golden fixture 作构造示范。

## 6. 契约注记 + 部署

- [ ] 6.1 `lens-metric-contract.md` 补「计数由 `lens_metric_emit` 从结构化 findings 归约产出」注记 + 「独立在折叠到**行键**后计」精化（**不改枚举、不升版本**）。
- [ ] 6.2 `pytest sdflow-init/tests/`（或脚本 sibling tests）全绿；`pytest -W error` 无 warning。
- [ ] 6.3 本仓 dogfood：跑一次 `bash setup.sh` 使 bundle symlink 生效；**跑一轮两审端到端**验证 emitter 被真实调到、锚过 anchor_lint〔广审 F9：别只验单测绿而留 SKILL 侧集成空〕。

## 7. 验收对账

- [ ] 7.1 逐条核对 specs（lens-metric-emit R1-R3 + workflow-metrics MODIFIED Scenario）均有**机械测试锚点**；**区分**「机械测试锚点（pytest）」vs「文档保留锚点（诚实声明类 Scenario，靠 SKILL/契约 prose 保留）」，后者 MUST NOT 在 verify 阶段当 pytest 假绿〔spec-review-amendment X2〕。
- [ ] 7.2 确认 D-6：未改锚形/枚举/版本；套件一致性由 4.1（check_lens_metric）+ 4.2（fold codomain 双向 + aggregator enum）+ 4.3（load_enums 等价性）+ 4.4（MIN_LENS_ROWS）四测试守。
- [ ] 7.3 golden fixture（合法输入 + 期望锚输出）落库，供 SKILL 落锚步与测试共引〔ADR-6〕。
