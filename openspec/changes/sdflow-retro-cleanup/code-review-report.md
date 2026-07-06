## code-review 报告 — sdflow-retro-cleanup

> 轻量清理批 T58-T61（4 项落在 `sdflow-retro/scripts/` 两脚本 + tests）。每次全跑独立冷主审：
> Step1 gstack/review（原生）→ Step2 领域镜×1 + 对抗镜×2 + 历史镜×1 + code outside-voice（codex）→ Step3 对抗裁决 → Step4 自动修/defer。

### 命中范围

- **栈**：dev-tooling / python 数据类 skill（无专属 domain 清单 → 用通用 CR-01~09 base）
- **清单**：CR-01~09（重点 CR-07 可观测 / CR-08 常量 / CR-09 测试质量）
- **diff base**：`f70b52c`（origin/main），评审目标聚焦 `8a8c98a..HEAD`（本 change 5 个 cleanup commit）
- **gstack/review（Step1 原生）**：**scope-drift 干净**（cleanup commit 精确落 `sdflow-retro/scripts/**` + change 目录，无旁溢；diff 里 `checkpoint-commit.sh` 删除 + `trivial_shape.py` 新增全属 `8a8c98a` 另会话 sdflow-init update，非本 change）；**完成度全**（T58-61 + 收尾 4/4 带反证测试，符合 tasks.md）
- **HR-TG 判定**：本 change（文本解析/常量/subprocess/死码）不命中 HR-TG 子集任一 → hit="none"

### Findings（置信 ≥80）

| # | 严重 | CR | 位置 | 问题 | 镜 | 置信 | 处置 |
|---|---|---|---|---|---|---|---|
| F1 | **高** | CR-09/CR-02 | `lens_metric_aggregate.py:39` | **爆点1**：闭合 fence 前缀匹配不校验尾部，`` ``` extra `` 被误当合法闭合 → 状态失同步（既漏真锚又混假锚，污染扩散到文件剩余部分，聚合表无 flag 暴露）。CommonMark 规定闭合行 marker 后只能有空白。**T58 把此缺陷扩大到 `~~~`** | 对抗镜1 | 高 | 已修[impl-review-fix] |
| F2 | 中 | CR-08 | `lens_metric_aggregate.py:17` | **爆点2**：`_FENCE_OPEN` 用 `\s*` 吞任意前导空白（含 ≥4 空格 / tab）→ CommonMark 缩进代码块（≥4 空格）被误判 fence 开启，吞掉其后 fence 外真锚。收紧为 ` {0,3}` | 对抗镜1 | 高 | 已修[impl-review-fix] |
| F3 | 中 | CR-02 | `lens_metric_aggregate.py:80-86` | **T61 契约洞**：「返空不抛」只覆盖 `is_dir()`，未覆盖 `glob()` 遍历——is_dir 在父目录 EACCES 抛 OSError、或 glob 中途 PermissionError，call-site catch 已删 → 冒泡崩 build_report。两处独立异常源 | 对抗镜2(is_dir) + codex(glob) | 高 | 已修[impl-review-fix]（try 覆盖整个扫描阶段） |
| F4 | 低 | CR-08 | `retro_report.py:324` | **domain F1**：surfacing_block docstring 仍写死「≥10」散文，与 T59 共享常量脱钩（阈值改则文档撒谎） | 领域镜 | 高 | 已修[impl-review-fix]（改引用 `LMA.REVIEW_ROUNDS_THRESHOLD`） |

### 已裁掉 / 已覆盖（反静默压制，可审计）

- **X1（domain F3 建议补 call-site 回归测试）**：**裁掉=已覆盖**。build_report/surfacing_block 无 archive 路径已由既有 `test_surfacing_block_fixed_prefix`（空 tmp_path）+ `test_build_report_coverage_counts`（无 archive 目录的 repo）经删 catch 后的代码路径锁定，另新增 `test_aggregate_is_dir_oserror_returns_empty` + `test_aggregate_glob_oserror_returns_empty` 直接钉死扫描阶段异常契约 → 无需额外测试。记录不静默丢。
- **对抗镜2 证伪项（可审计）**：T60 「无历史路径/merge-base/无效 sha 虚警刷屏」全证伪——只读命令 `git log -- <不存在路径>` rc=0、代码无 merge-base 调用、所有 sha 来自 git log 真实输出恒合法；stderr 只在**真故障**（空仓/非 git 目录 rc=128）写。历史镜：CF-4/CF-2/F1 不变量全保留、无 revert 冲突、无重蹈旧 review。

### 修复 / defer 台账

- **自动修 4 项[impl-review-fix]**：F1（闭合尾部校验）、F2（缩进 0-3 空格）、F3（try 覆盖 is_dir+glob 整个扫描阶段真正兑现"返空不抛"）、F4（docstring 去硬编码 10）。均补反证哨兵测试（F1/F2/F3 修前 FAIL 修后 PASS；F4 纯文档）。
- **defer 1 项 → todolist T62**：T60 `_run_git` 留痕在**系统性 git 损坏**下 O(commits) 无节流放大（seed_mass_shas per-sha 调用；仅真故障下噪声、非虚警、view-only 不中断 → 低危 DX）。hand-off 会引用。
- **无 ≥2 方案 T10 复核项**（4 项修复方向唯一、有客观判据=反证测试）。
- **测试**：全 58 绿（含 `-W error` 零 warning），dogfood 幂等无漂移、健康仓无 stderr 噪声。

### 度量锚（lens-metric，config metrics.enabled=true）

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="文本解析/常量/subprocess/死码，不触 DB迁移/安全/并发等 HR-TG 判据" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="ok" findings="1" truncated="false" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="3" 采纳="1" 裁掉="1" defer="1" 独立="1" sev="致0/高0/中0/低3" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="2" sev="致0/高1/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="step1" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->

> 注：F3 由对抗镜2（is_dir 面）+ codex outside-voice（glob 面）收敛到同一契约洞，dedup 合并为一条 → 两镜均不计独立。T60-throttle 由 domain + adversarial 双命中 → defer、不计独立。

### 结论

- ☑ 建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）
- ☑ defer 残差已入 todolist（T62，hand-off 会引用）

<!-- ship-gate: code-review=pass -->
