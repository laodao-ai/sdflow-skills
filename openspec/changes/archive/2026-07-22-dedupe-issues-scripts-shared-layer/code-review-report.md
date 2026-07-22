---
ship-gate:
  code_review: pass
  reviewed_sha: 2bb4c7638e6bcf0e0111ad3f4ff320ee08062e99
---

## code-review 报告 — dedupe-issues-scripts-shared-layer

分支级冷层强制主审（每次全跑·独立冷视角）。6 张 ticket 已各过 per-ticket 双轴审 + fix + re-review；本层是**独立冷兜底网**，实测抓出 per-ticket 层结构性看不见的**跨票整合缺口**。

### 命中范围
- 栈: Python stdlib 工具脚本（无 backend/embedded 领域 delta 命中）· 清单: `code-review-base.md` CR-01~09
- diff base: `43a60fd..HEAD`（71 文件 +22131/-4959，核心 = 三脚本 6141 行合并为单一 `sdflow_issues_core` package）
- HR-TG 命中: TG-06（跨模块共享数据模型边界·D-6 反转独立分发）+ TG-26（并发/共享可变状态·recorder_lock/token 收进共享 core）
- **gstack/review（Step1 scope-drift + 完成度）**: 71 文件全映射本 change 声明范畴，**无顺手多改**；6 ticket 全交付匹配 proposal/design goals。（一处例外：fix 子代理误落 `code-review-fix2.md` 到仓根 → 本层 scope-drift 当场抓、已 `git mv` 修正到 change dir）

<!-- sdflow:step1-broad-review v1 mode="native" -->

### 子代理能力锚
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

<!-- sdflow:hr-tg v1 hit="TG-06,TG-26" declared="TG-06,TG-13,TG-14,TG-23,TG-26" evidence="三脚本合一为单一 sdflow_issues_core package = D-6 反转独立分发(TG-06); recorder_lock/atomic_write/委派 token 收进共享 core 三池共用 = 共享可变状态(TG-26)" -->

### Findings（置信 ≥80）

**[高] CR-01/CR-05 recorder 委派 token 错误路径泄漏（3 镜收敛 + 实测复现）** | `sdflow-issues/scripts/issues.py:1215-1222` | `main()` 里 `_core._ACTIVE_RECORDER_TOKEN`/`_ACTIVE_RECORDER_CHAIN` 复位不在 try/finally——`_die()`→`sys.exit` / `args.func` 抛异常跳过复位，脏 token 留在 `sdflow_issues_core` **进程内单例模块全局**。**dedup 放大**：合并前三脚本各持独立全局（隔离），合并后共用一个 core 单例 → 泄漏面扩为「同进程内任何后续直调 `read_pool`/`_scan_pool` 读脏值 → 抛 `RecorderLockError: delegation denied`、根本没碰目标仓」。实测复现：`main()` 跑失败命令后 `read_pool(repo2)` 抛 delegation denied。测试大量直调绕 main()、conftest 无 autouse 复位、**现靠执行顺序侥幸绿**（通则③目标态：T211/T208 defer 落地即真 bug）。**置信 95（live repro）** | ✅ 已修 [impl-review-fix]（try/finally + conftest autouse 复位 fixture）

**[高] node-id baseline「冻结」可游戏化** | `sdflow-issues/tests/test_task6_coverage_gate.py:125` | `test_baseline_is_frozen` 只查 `len>=2000` + 含 7 allowlist——删其它 baseline 条目只要总数不跌破 2000 就不被抓（逐 node 对账检不到被删项），重新引入 design 反对的可游戏化计数门。**置信 90（cross-model code-voice，读码确认）** | ✅ 已修 [impl-review-fix]（钉死精确 count=2093 + 文件 sha256，任何 baseline 改动必过断言 = 强制显式审查）

**[中] thinness 守把 missing helper 当成功** | `sdflow-issues/tests/test_determinism_guards.py:300` | 遇 `_MISSING` 直接 continue——从薄入口删任意 roster helper 不反红，违 spec「每个 helper 从薄入口解析 __module__=='sdflow_issues_core'」。**置信 85（cross-model + 呼应 T4 re-review）** | ✅ 已修 [impl-review-fix]（每薄入口定义 expected-export roster，先断言存在再校验 identity；内部 underscore helper 显式移出 roster）

**[中] validate_pool_spec fail-closed 有洞 + 外部锚漏字段** | `sdflow-issues/scripts/sdflow_issues_core/__init__.py:138-167` | 只查 keys/实例类型/terminal⊆status——`issues_dir=""`/空 `specific_values`/`value.pool` 与 key 不符/非法前缀均返 True；EXPECTED_CONTRACT 外部锚漏 pool/requires_block/枚举/状态/终态（T2 派生化后逐值对照 tautology、只剩此锚却漏这些字段）。**置信 85（cross-model hr-tg，读码确认）** | ✅ 已修 [impl-review-fix]（validator 补 `value.pool==key` + 字符串维非空 + 枚举/状态/终态非空 4 类 fail-closed；新增 EXPECTED_ENUMS 外部字面锚钉枚举/状态/终态/pool/requires_block + 3 mutation 反红）

**[中] specific_values 双真相源（POOL_SPEC vs PoolStrategy）无一致性守** | `sdflow-issues/scripts/sdflow_issues_core/__init__.py:1843,1867` | `specific_values` 同存于 POOL_SPEC（集合，add 判合法）与 STRATEGY.specific_values_ordered（有序，lint/提示用），可漂移「add 收但 lint 拒」，无守卫。**置信 85（cross-model hr-tg）** | ✅ 已修 [impl-review-fix]（单一源化：共用有序 tuple 常量、POOL_SPEC.specific_values 由其派生）

**[中] detect_change subprocess text 无 utf-8** | `sdflow-issues/scripts/sdflow_issues_core/__init__.py`（`detect_change` git subprocess.run） | `text=True` 未指定 `encoding="utf-8"`——Windows 非 UTF-8 locale 下 git 输出解码可能崩（已知 Windows CI 陷阱）；本次合并迁入 core 放大到全池共用。历史遗留非本次新增。**置信 80（历史镜）** | ✅ 已修 [impl-review-fix]（补 encoding="utf-8"，面治扫 core 内同类 git subprocess）

### 已裁掉（反静默压制，可审计）
- 对抗镜①（并发）: `recorder_lock` O_EXCL 原子获取 + identity+token 双核验释放 + env-var 委派链 + atomic_write + frozen POOL_SPEC/PoolStrategy 全部正确、有真并发多进程测试锚定 → **并发面 refuted 无真爆点**（token 错误路径泄漏另由 F1 采纳）。
- 领域镜候选（`_promotion_insertions` require_block=False 仍建 minimal block / `_scan_pool` stderr 子串匹配 / `cmd_add` next() 无 default）: 逐字节比对 43a60fd 前旧脚本，**均合并前既有原始行为、非本次 diff 引入** → 裁掉（未改动行既有问题，不在本 change scope）。
- <80 滤除: 无（cross-model findings 豁免同族置信滤直通对抗裁决；Claude 镜 findings 均 ≥80）。

### 修复 / defer 台账
- **自动修 6 项** [impl-review-fix]: F1(token try/finally+autouse)·F3(baseline 钉死)·F4(thinness 存在性)·V2(validator fail-closed+外部锚)·V3(specific_values 单一源)·F5(encoding)。两段源码提交 `5cc7748`(F1/F3/F4/F5) + `5ce875a`(V2/V3) + 位置修正 `2bb4c763`。
- **defer 3 项**:
  - T210〔F2·code-voice〕: CLI 等价 harness 升 frozen golden（stdout+落盘+exit 全字节对账）。等价性 T2 已 byte-identical 证过、旧脚本已删无法 live before/after → 前向 test 硬化，非 correctness bug。
  - T211〔V1·hr-tg〕: recorder token 改 ContextVar/显式 RecorderLockState 上下文栈隔离。今日全 CLI 独立进程不可达；与 T208（消 issues 自调用子进程→in-process）同期才成真问题，绑定 T208。
  - （T208 既有 AD-7 defer，T211 追加其 in-process 前提的 token 隔离范畴）
- **T10 复核**: 无「≥2 无客观判据方案」需对抗镜复核——所有采纳项有客观判据（实测复现 / 读码确认 fail-open / 契约违背），defer 项有明确后置理由。

### 度量锚（lens-metric，metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="2" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="2" sev="致0/高0/中2/低0" -->

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="true" -->
<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->

### 结论
- ☑ 建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）
- ☑ defer 残差已入 todolist（T210/T211，hand-off 会引用）
- **冷层价值实证**：3 镜收敛 + 2 次 cross-model voice 抓出 6 轮 per-ticket 双轴审全漏的 6 条真发现（F1 token 泄漏有实测复现、F3 baseline 可游戏化、guards 弱于宣称），全部当场修复 + 全套件 2143 绿。
