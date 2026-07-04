## code-review 报告 — ship-gate-hardening

> 阶段三代码审：Step1 gstack/review（scope-drift+完成度，原生）→ Step2 多镜（正确性/对抗/历史 + 双 codex cross-model）→ Step3 置信过滤+对抗裁决 → Step4 自动修/defer → 一份报告。**阶段三无人类门**，能修当场修、pre-existing defer。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="TG-09" evidence="gate decide() 是 change 生命周期决策状态机;D3 终态误判=假✅头号失效模式" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="" findings="2" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->

### 命中范围
- 栈：纯 Python 编排脚本（无 backend-go/embedded/frontend 领域清单）。清单：CR-01~09 base。
- **Step1 gstack/review（原生）**：scope-drift=无越界（branch_state 移除属 H4 在 scope 内；测试改动均相关）；完成度=5/5 计划任务全实现（gate 5/5、仓级 328 绿）。
- 镜阵：正确性镜（CR-01~09 + 活体复现）· 对抗镜（活体 git 实验）· 历史镜（git blame + 上轮 [impl-review-fix] 核验）· codex code-voice（全量 diff）· codex hr-tg（TG-09 状态机）。审 diff = `9232a9d..HEAD`（ship_gate.py +192 行 + tests）。
- 5 声 12 条原始 → 去重后 4 修 + 3 defer + 大量正面确认。

### Findings（置信 ≥80，均已当场修 [impl-review-fix]）

| 严重 | 问题 | 证据 | 置信 | 处置 |
|---|---|---|---|---|
| **high** | **core.quotePath 假✅**：git 默认 C-quote 非 ASCII 路径，`is_stale` 裸 `startswith(base)` 对中文文件名路径失配 → 拍板后偷改中文名 spec（`功能规格.md`）静默不失鲜（本项目中文名密集，realistic） | 对抗镜 Adv-A 活体复现；`ship_gate.py` is_stale 两 scope + archived_dirs_in_tree | 95 | 已修：`run_git`/`run_git_rc` 注入 `-c core.quotePath=false`（一处覆盖全 git 调用）+ 回归 `test_chinese_named_spec_edit_still_stale` |
| **high** | **archived verify 冲突锚假 SHIPPED**：D3 短路 `archived_verify_passed` 只查 `PASS in`，归档报告并存 PASS+FAIL 会 SHIPPED（active 路径有 pick_exclusive，短路绕过），违反 spec「冲突锚 MUST UNKNOWN」 | codex code-voice#1 + codex hr-tg#2（三声含预标） | 92 | 已修：改 `archived_verify_state` tri-state（pass/conflict/none），冲突→UNKNOWN + 回归 `test_archived_verify_conflict_unknown` |
| **medium** | **非 UTF-8 归档 verify 崩溃**：`archived_verify_passed` 走 `subprocess.run(text=True)` strict 解码，GBK 归档报告 → UnicodeDecodeError → **退出码 1 逸出契约集**；头注释承诺「replace 解码」但 git-show 路径绕过 | 正确性镜 Corr-1 + 历史镜 F1（双声活体复现） | 95 | 已修：`run_git`/`run_git_rc` 加 `errors="replace"`（与 Adv-A 同处一并修）+ 回归 `test_gbk_archived_verify_no_crash` |
| **medium** | **base_ref 误认同名 tag**：`rev-parse --verify main` 会把名为 main/master 的 tag 当 base 分支，违背分支语义 | codex code-voice#2 | 85 | 已修：改 `refs/heads/{base}` 限定分支 |
| **low** | **evil-merge 漏检**：仅存在于 merge commit 自身的改动 `--name-only` 不加 -m 漏检，但头注释反当「不漏检」卖点 | 对抗镜 Adv-B | 90 | 已修（文档）：头注释「已知不覆盖」老实记入 evil-merge |

### 已裁掉（反静默压制，可审计）
- **X1〔对抗镜角度 2/3/4 refuted〕**：D3 短路空仓/多同名归档（重名反模式已声明接受）/ref 树读取、集合归属 n==0 顺序/boxes 分支、闭区间双计（set 去重 + TAG_RE 贪婪 `\d+` 区分 task1/task10 + `--diff-filter=A` 使 sha 非 merge）——对抗镜实跑证伪，防御到位。裁定不成立。
- **X2〔历史镜 4 项重点担忧全清白〕**：revert 防御保留（sha 自身走同 startswith+TAG_RE 双闸）/is_stale code 分支逐字一致/branch_state 移除无悬空/plan_first_sha 未改。裁定无回归。
- **X3〔HR-TG c1/c3/c4 三条判为 pre-existing 非本次引入〕**：完成 tag 无 change 命名空间（窗口下界已部分缓解）/ freshness 只看 committed 盘面（「盘面即状态」既有设计）/ 复选框全局粒度（既有 checkboxes_all，B4 未触碰）——非"发现漏掉的洞"，是既有设计局限；裁掉"本次引入"定性，降级为 defer（不静默丢，见台账）。
- **X4〔正则 `$` 冗余 / `\d\d` 不校验月日 / run_git_rc 注释轻微错位〕**：正确性镜+历史镜标 cosmetic，逻辑正确，<80 不修。一行带过留痕。

### 修复 / defer 台账
- **自动修 5 项 [impl-review-fix]**：quotePath+errors=replace（1 处 run_git 覆盖 Adv-A+Corr-1+F1 三条）· archived verify tri-state 冲突→UNKNOWN · base_ref refs/heads/ · evil-merge 头注释。新增回归 3 条（中文名失鲜 / 冲突锚 UNKNOWN / GBK 不崩），ship 65 绿、仓级 328 绿。
- **defer 3 项 → todolist T32/T33/T34**（pre-existing 局限，源=ship-gate-hardening）：change 命名空间 tag · 工作树 dirty 新鲜度 · 复选框分段绑定。hand-off 引用。
- **voice 分桶〔M4〕**：codex code-voice 采纳 2/裁 0/defer 0；codex hr-tg 采纳 1/裁 0/defer 3；Claude 镜（正确性/对抗/历史）采纳 3（Adv-A+Corr-1+F1 合并计 + base_ref 由 code-voice 主报）/裁 3 组（X1/X2 正面确认）/defer 0。
- **T10 复核**：无「≥2 方案无客观判据」自动选——所有修复均有客观判据（测试断言/spec 契约/活体复现）。

### 结论
- 5 声独立冷审揪出 4 真缺陷（2 high 假✅/假 SHIPPED + 2 medium 崩溃/精度），**全部当场修 + 回归钉死**；3 条 pre-existing 局限 defer 入 todolist；对抗/历史镜的证伪与正面确认覆盖 B1/B2/B3/B4/D3 全部主张。仓级 328 绿、无回归。建议进 `/sdflow-done`。

<!-- ship-gate: code-review=pass -->
