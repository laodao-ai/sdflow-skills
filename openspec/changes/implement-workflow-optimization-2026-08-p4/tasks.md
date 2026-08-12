# Tasks · implement-workflow-optimization-2026-08-p4

> Requirement 追溯记号：HAE-1/2 = host-adaptive-execution delta 两条；SW-1/2/3 =
> spec-workflow delta 三条（组装序 / 派发二维 / defer 入池）；IO-1/2 = impl-orchestration
> delta 两条（gate 两门 / implement+done 接 effort）。优先序按 proposal TG-19：P0 → P1 → P2。

## 1. B25/B26 修复 + ship_gate 机械门（P0）

- [ ] 1.1 B25 诊断定案（Open Q1）：在 rsp 归档报告的 roster/findings 数据上重放
      `lens_metric_emit.py` 调用，判定「未调用 vs 调用失败未记录」，结论记入
      impl-report（不阻塞后续任务）〔IO-1〕
- [ ] 1.2 ship_gate 锚存在门：`metrics.enabled=true` ∧ code-review 报告缺
      `layer="code-review"` lens-metric 锚或缺机械引用核落盘段 ⇒ 判「该步进行中，重跑」+
      修复指引；config 缺省/false=放行、存在坏=fail-closed 三态分治；fence-aware 口径
      复用既有解析〔IO-1〕
- [ ] 1.3 ship_gate defer 对账门：defer 台账行 `T\d+|B\d+` id + 池文件**文件系统**存在性
      判定；spec-review 报告 design 门同款锚存在检查〔IO-1〕
- [ ] 1.4 gate 测试群：双向 config 态（缺省放行/开启拦截/坏值 fail-closed/**config.yaml
      文件整体不存在=放行** `[spec-review-amendment]`）× 缺锚/缺 `sdflow:ref-check` 锚/defer
      无 id/池文件缺失/**id 存在但池文件 `change` 属另一 change**/**描述列旧票号不误抓
      （窄化提取负例）**/**聚合摘要句不假阳**/fence 假阳负例矩阵 `[spec-review-amendment]`〔IO-1〕
- [ ] 1.5 sdflow-code-review SKILL：Step4 defer 改「当场 recorder add（显式
      `source_change`）+ 返回 id 写台账」；台账改机读结构（表格行 + 专用 id 列，单元格全内容 =
      单 id）+ 聚合摘要句改写移出 gate 检测范围 `[spec-review-amendment]`；Step3 引用核结果
      落 `sdflow:ref-check` 结构化锚（含全通过/零 findings 轮次）、Step5 义务措辞与门对齐
      `[spec-review-amendment]`；recorder 失败 fail-loud 条款〔SW-3〕
- [ ] 1.6 按 1.1 结论修复 emitter 落盘直接成因（若为条款缺陷则改 SKILL Step5，若为
      调用失败则修脚本/路径）；本 change 自身 code-review 即为门的首个 dogfood〔IO-1/SW-3〕

## 2. 面 A · effort 分档（P1）

- [ ] 2.1 A1 最小实测：探针定义**手工临时放置** `~/.claude/agents/`（不经 install_agents，
      验证完删除；结论对官方定义外推有效——两者均纯 frontmatter 声明 `[spec-review-amendment]`）；
      以 frontmatter `effort: low` 派探针子代理，生效信号用 **token 用量/耗时 + 输出规模多信号**
      对比（输出规模单独作判据假阴/假阳皆易 `[spec-review-amendment]`），确认 effort 经
      subagent_type 生效；失效 ⇒ 停下按 `adr/0043` Considered Options 备选重估
      （止损点，不带病继续；原「memo K1 备选」指引有误——K1 无备选内容 `[spec-review-amendment]`）
      〔HAE-2 前置〕
- [ ] 2.2 `model-tiers.md` 加 effort 表列 + `effort-tier-defaults` 机读块（仅 claude 三键；
      表格与机读块两处不漂移）；`resolve-models.sh` 提取/导出 `SDFLOW_EFFORT_*` +
      `effort-tiers.claude.*` config 覆盖（有界键路径、值域校验、非法回落告警）+
      头注释变量清单 6→9；⚠️ effort 分支 MUST NOT 复用 model tier 的 unknown 回落/
      `_resolve_tier` 告警路径，codex/unknown 显式初始化空串（`set -u`），负例测试先行
      `[spec-review-amendment]`〔HAE-1〕
- [ ] 2.3 resolver 测试：三宿主态（claude 导出/codex 空值/unknown 空值）× 覆盖生效 ×
      非法值回落 × eval 契约〔HAE-1〕
- [ ] 2.4 5 个 `sdflow-effort-{low,medium,high,xhigh,max}` agent 定义（排他 description +
      `model: inherit`）放进既有 `sdflow-spec/agents/`（设计门拍板 Q2=C/Q1=B：install_agents
      守卫/manifest **零改动**，新增 `.md` 自动纳入 `[spec-review-amendment]`）；假 HOME 测试
      加 effort 定义专项断言（铺设幂等/不覆盖他人/孤儿清理/Windows skip 沿既有骨架）；
      同步 CLAUDE.md/design 对该目录的描述 + 目录内一行注记〔HAE-2〕
- [ ] 2.5 四个编排 SKILL 派发条款接 effort（表格加档列 + subagent_type 构造 + 空值回落 +
      门禁步不低于 high 铁律句 + tier-resolution unset 清单扩含 `SDFLOW_EFFORT_*` 三变量
      `[spec-review-amendment]`）；`sdflow-done` 三步子代理同步〔SW-2, IO-2〕
- [ ] 2.6 bundle 同步：config.template `effort-tiers` 段示例 + claude-section 说明 +
      `init.py lint_config` 扩 `effort-tiers` 结构/值域校验（与 resolver 同口径 + 测试
      `[spec-review-amendment]`）+ scope-check 表全组复查（防部署副本漂移）〔HAE-1〕

## 3. 面 B · dispatch prompt 构造（P2）

- [ ] 3.1 `render-review-prefix.sh`（assets/hack）：固定序 cat 通则区块 + 内嵌通用契约段
      （含 T103 封顶句）+ base checklist；源缺失 fail-loud；byte-stable golden 测试
      （连续两跑逐字节同 + 源缺失非零退出）〔SW-1〕
- [ ] 3.2 两评审 SKILL 镜派发段改三段组装序（段① = 脚本输出原文一句引用；段②③ 界线
      显式化）；SKILL 内与段①重复的散文契约收敛为引用〔SW-1〕
- [ ] 3.3 setup.sh 布署链验证：`render-review-prefix.sh` 随 hack 拷贝就位（改 assets/hack
      必重跑 setup 的既有纪律照抄进 SKILL 提示）〔SW-1〕

## 4. 实现验证收尾

- [ ] 4.0 自审窗口 `[spec-review-amendment]`：触发本 change 自身 code-review/verify **之前**，
      在开发 checkout 跑 `bash setup.sh`（全局窗口层，时间盒）——否则自审调用运行 checkout
      的旧 gate/旧 SKILL，dogfood 自证不成立（对抗镜机器实测软链指向）；自审完毕回运行
      checkout 重跑 setup 还原，还原动作记入 impl-report
- [ ] 4.1 全仓 `/usr/bin/python3 -m pytest -q` 绿（新增测试群全数纳入）
- [ ] 4.2 retro 再生冒烟：`retro_report.py` 跑通、本 change token-log 锚在列；anchor_lint
      对既有报告语料 CLEAN（gate 新门不破坏度量链路）
- [ ] 4.3 roadmap 阶段 4 回填（子任务表 + 快照行）+ task-log 里程碑；B25/B26 池状态按
      实况 set-status（FIXED + evidence）；T105/T103（面 A）、T98/T124（面 B）机制层交付后
      同步 set-status DONE + evidence 指向实现/测试（p3 6.2 先例；观察性验收②③继续走
      D4「不阻塞归档」路径不冲突 `[spec-review-amendment]`）

## 测试覆盖图（TG-18）

| code path | 测试类型 | 落点 |
|---|---|---|
| effort 机读块提取 + 导出 + 覆盖 | 契约 pytest（bash 真跑） | `hack/tests/`（resolver 既有测试群旁） |
| install_agents 4 定义铺设/守卫/孤儿 | 假 HOME 真跑 bash | `hack/tests/test_install_agents.py` 扩面 |
| render-review-prefix byte-stable | golden pytest | 新 `hack/tests/` 或 skill tests/ |
| ship_gate 锚存在门 + defer 对账门 | 单元 + fixture 报告矩阵 | `sdflow-ship/scripts/` 对应 tests/ |
| SKILL 派发条款（散文层） | anchor_lint / 双轴审语义层 | 评审期 |
| A1 effort 生效 | 一次性人工探针（记 impl-report） | task 2.1 |
