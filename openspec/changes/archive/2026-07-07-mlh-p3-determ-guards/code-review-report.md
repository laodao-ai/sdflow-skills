## code-review 报告 — mlh-p3-determ-guards

阶段三 whole-branch 独立冷主审（每次全跑，非高风险抽查）。DIFF_BASE=204a83e..e917de9（Task1-4）。

### 命中范围

- **栈**：纯 Python stdlib 数据类脚本（recorder/init/issues）——不命中 backend·go / embedded / frontend 任一领域清单，领域镜过通用 `code-review-base.md` CR-01~09。
- **清单**：CR-01~09（通用）。
- **trivial_shape**：NOT_EXEMPT（init.py/issues.py/todolist.py 有逻辑面）→ 照常 fan-out。
- **HR-TG**：none —— config_lint/batch lint 是 fail-closed 校验器（lint bug 易查易回退，非"运行期爆炸/数据损坏且难回退"）；归一触及共享 helper 但行为保持+测试守。code-voice outside-voice 恒跑，跨模型覆盖不缺。
  <!-- sdflow:hr-tg v1 hit="none" evidence="纯stdlib校验器,lint误判易查易回退,非HR-TG入选判据(运行期爆炸/数据损坏且难回退)" -->
- **gstack/review（Step1）**：主 session 原生执行 scope-drift + 完成度审计——scope-drift=无（全部改动映射 4 任务，`--root` 默认 None→"." 为 config_lint 探测所需的必要子改，Task2 审已核其他 mode 不受扰）；完成度缺口=1（设计自身失败模式表"config/batch 文件缺失→非零"未对 batch lint 兑现，即 F1）。
  <!-- sdflow:step1-broad-review v1 mode="native" -->
- **镜阵**：领域镜×1（中档）+ 对抗镜×2（adv-A fail-open 角度 / adv-B 归一+AST harness 角度）+ 历史镜×1（弱档 git blame）+ code-voice outside-voice（codex）。
  <!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="none" findings="4" truncated="false" -->

### Findings（置信 ≥80）

- **[致命] CR-01/fail-closed | issues.py `cmd_batch_lint`（batches.md 缺失）| 已修[impl-review-fix] F1**
  batch lint 对缺失 batches.md fail-open：`_read_batches_lines` 缺文件返 `[]` → 打印"0 条批次全部通过"、退出 0。设计**失败模式表明确要求**"文件缺失→报告+非零退出（不静默当无错）"，正是该 anti-pattern。多源收敛（codex OV-1 high + 对抗A CRITICAL 实测复现 + broad 完成度）。修：`cmd_batch_lint` 入口加 `os.path.exists` 检查→`_die` 非零（不改共享 `_read_batches_lines` 的缺失→[] 语义，`cmd_batch_add` 首建流程依赖它）。置信 95。

- **[高] CR-01/fail-closed | init.py `lint_config`:309 + issues.py `_read_batches_lines`:501 | 已修[impl-review-fix] F2**
  非 UTF-8 config.yaml / batches.md → 裸 `UnicodeDecodeError` traceback 而非 clean reason（`UnicodeDecodeError` 是 `ValueError` 子类，不被 `except OSError` 捕获；`_read_batches_lines` 原 open 无编码守卫）。**历史镜实证**：所引范式源 anchor_lint.py 恰在 commit `8f1d2bc`(mlh-p2 impl-review) 把此坑修过（`except (OSError, UnicodeDecodeError)` 标 `[impl-review-fix] F2 fail-open→fail-closed`），新代码抄范式漏抄修复——重蹈同仓已修 bug。三源收敛（域 Important + 对抗A HIGH 实测 + 历史 CONFIRMED 带 commit）。修：两处均 `except (OSError, UnicodeDecodeError)`。置信 95。

- **[高] 覆盖缺口 | test_mirror_consistency.py TWO_WAY | 已修[impl-review-fix] F5**
  一致性守卫漏守 6 个 buglist↔todolist 间 byte-identical 共享 helper（`_id_sort_key`/`validate_doc_paths`/`all_ids`/`next_id`/`_die`/`_load_json`）——design「11 个 helper=完整」审计不完整（实际共享面 ≥17，对抗B 程序化证伪 + 主 session 复验 byte-identical）。这 6 个可静默漂移，材质上过度声称"确定性守卫"。修：6 个加入 TWO_WAY（今日全 AST 等价→现有 test_two_way 覆盖并通过，扩 8→14）。`_die` 虽 3 向存在但 issues 侧 3 向 AST 等价未验，未纳 THREE_WAY（留 defer）。置信 88。

- **[中] batch 优先级正则过匹配 | issues.py:707 | 已修[impl-review-fix] F3**
  `^(P\d|—)` 对 `P10`/`P40` 捕获 `P1`/`P4` 前导 token → 误判合法通过（P10/P40 非合法优先级）。双源收敛（codex OV-3 + 对抗A MEDIUM 实测复现）。修：`^(P[0-4](?!\d)|—)`——**主 session 复验**：拒 P10/P40/P5/P7，仍过 `P1 ★`/`P2（T10 已 DONE）`/`—（已闭合）`/`P2`（零假阳基线不破）。置信 90。

- **[低] 测试覆盖缺口 | test_config_lint.py | 已修[impl-review-fix]（minor 折入 F 修复轮）**
  域镜指出 config_lint 的 `_git_root_or_dot()` 自动探测路径 + config 文件不存在场景无自动测试（原 8 用例均显式传 `--root`+预写文件）。修复轮补 2 个 config-lint 测试。置信 82。

### 已裁掉（反静默压制，可审计）

- **X1（F4，codex OV-4 medium + 对抗A LOW-MED）** `metrics.enabled` 拒绝合法 YAML 行内注释 `enabled: true # x` = 假阳——**裁掉（paradigm-consistent）**：主 session 复核所引范式源 anchor_lint.py 的 `_ENABLED = r'^\s+enabled:\s*(true|false)\s*$'` **同样拒绝行内注释**（不匹配→MetricsError）。config_lint 拒注释是与姊妹校验器**一致的有意严格**；若"修"成接受注释反而使两者对同一 config 判定分歧（更糟）。非缺陷。是否两者都该容忍注释=设计级决定 → defer T73。
- **<80 滤除（一行带过，不静默丢）**：CI 能抓的 import/格式/类型未进任何镜；对抗镜多项攻击"held up"（config.yaml 缺失 config_lint 正确退 1 / `P1 ★` 装饰后缀有意不校验 / `enabled:  true` 多空格正确接受 / importlib 加载零副作用 / 归一后 71 测试零回归 / 删除证伪真 AttributeError / PRIORITIES 值断言真捕漂移）——均确认 sound，无 finding。

### 修复 / defer 台账

- **自动修 5 项 [impl-review-fix]**（F1 致 / F2 高 / F5 高 / F3 中 / 测试缺口 低）——均 T10 级①（客观判据：构造坏输入断言退出码/通过态可测），按测试 RED→GREEN 落地，仓级 627 passed 零回归、4 目录 389→396。
  - 三镜+主次记理由（F1 为例）：**系统镜**=fail-closed 校验器缺失文件静默过=守卫失效（主）；**用户镜**=CI/坏 checkout 后 batch lint 假绿零信号（次）；**开发循环镜**=设计失败模式表已明写、修复对齐自身契约（次）。主次判定：系统镜（守卫完整性）为主。
- **自动裁 1 项**：F4（paradigm-consistent，见已裁掉 X1）。
- **defer 4 项 → todolist**：
  - T70（对抗A LOW）：config_lint tab 缩进 model-tiers 子键隐形→越域 fail-open（边缘 YAML）。
  - T71（对抗B LOW）：`_ast_no_doc` 空体函数坍塌理论假过（当前不可利用）。
  - T72（codex OV-2 high，但对抗A 判为文档化边界）：batch 条目整行缺失 优先级:/计划: 字段不校验（实现有意窄化值语法层）——考虑补结构完整性校验。
  - T73（F4 派生）：metrics.enabled 两校验器是否都该容忍行内注释=设计级决定（须同步改防分歧）。
  - 另 `_die` 3 向 AST 等价纳 THREE_WAY 与守卫动态发现全共享 helper 之完备性=F5 残差，随 T70-73 池后续评估。

### 度量锚（lens-metric，config metrics.enabled=true）

<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="7" 采纳="4" 裁掉="1" defer="2" 独立="1" sev="致1/高2/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="4" 采纳="2" 裁掉="1" defer="1" 独立="0" sev="致1/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致1/高0/中0/低0" -->

> 独立合计=2（域镜唯一捕测试缺口·低 / 对抗镜唯一捕 F5 守卫覆盖缺口·高）——冷独立层实测兑现 load-bearing：SDD 各任务审全绿，冷主审+codex 抓 5 真 bug（含致命 F1 fail-open + 高危 F5 守卫过度声称）。

### 结论

- ☑ 建议进 /sdflow-done —— 5 findings 全自动修（致1/高2/中1/低1）+ 4 defer 入 todolist（T70-73）+ 1 裁掉（paradigm-consistent）。仓级 627 passed 零回归。
- ☑ defer 残差已入 todolist（hand-off 会引用 T70-73）。

<!-- ship-gate: code-review=pass -->
