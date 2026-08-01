---
ship-gate:
  code_review: pass
  reviewed_sha: 93e01503d64d2f897a8c1312b4f6a5edeab1f056
---

## code-review 报告 — shared-yaml-subset-parser

### 命中范围

栈: python-toolchain（sdflow-skills 仓自身的 Python 脚本 + shell）
清单: CR-01~09（通用 base，无领域 delta——非后端/嵌入式/前端）
gstack/review: scope-drift=CLEAN, 完成度=8/8 task groups complete

<!-- sdflow:step1-broad-review v1 mode="native" -->

### 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

### HR-TG 判定

<!-- sdflow:hr-tg v1 hit="none" declared="" -->

无 TG 命中，HR-TG∩=∅，不需要领域 cross-model。

### Findings（置信 ≥80，含跨模型豁免）

**F1 [Important] CR-01/CR-02 roadmap_writeback_draft.py 重复键检测丢失（fail-closed→fail-open 回归）**
`sdflow-done/scripts/roadmap_writeback_draft.py:read_verify_state` 迁移到 yq 后丢失了 `ship-gate:` 块内 `verify:` 键的重复键检测。yq 对重复键静默取最后值，输入 `"---\nship-gate:\n  verify: PASS\n  verify: FAIL\n---\n"` 旧行为 `("malformed", None)` → 新行为 `("good", "FAIL")`。置信 90。
已修 [impl-review-fix]：加 frontmatter 内 ship-gate 块 verify 重复键预扫描。

**F2 [Important] CR-01 anchor_lint.py exit-code 契约击穿（多镜确认）**
两份 `anchor_lint.py` 的 `_yq()` 用 `sys.exit(1)` 处理 yq 未安装/身份校验失败，绕过 `main()` 的统一异常映射；`_metrics_enabled()` 未捕获 `_yq()` 抛出的 `RuntimeError`/`JSONDecodeError`，exit=1 与 `EXIT_VIOLATION=1` 撞码。对抗镜1 实测复现：config.yaml 含未闭合引号时 RuntimeError 逸出，退出码 1 被下游误判为"锚检查发现违规"而非"环境故障"。置信 95。
已修 [impl-review-fix]：`sys.exit(1)` → `raise RuntimeError`；`_metrics_enabled()` 包 `try/except RuntimeError → MetricsError`。

**F3 [Medium] ship_gate.py yq subprocess 缺 timeout 和 OSError 收敛（跨模型豁免）**
`ship_gate.py:238,260` 的 yq `subprocess.run` 未传 `timeout`、未捕获 `OSError`；对照同文件 git 通路（`:242`）已有等价保护。置信 80。
Defer → todolist（yq 是本地操作极少挂起，概率低影响小；与 git 路径的不一致性是事实但非阻断）。

**F4 [Low] yq 最低版本运行时不验证（跨模型豁免）**
运行时 `_yq()` 只检查 mikefarah 身份，不校验 `>=4.16.0`（`--front-matter` 的能力下限）。`setup.sh` 检查过但用户可绕过。置信 75。
Defer → todolist。

**F5 [Low] CI 下载 yq 无完整性校验（跨模型豁免）**
`mechanical-gates.yml:73` 用 `curl -sSL` 下载 release asset，无 SHA-256 校验。版本已钉死但无内容完整性保证。置信 70。
Defer → todolist。

### 已裁掉（反静默压制，可审计）

**历史镜 H1-H4**：历史镜发现 4 个模式（sys.exit 契约违反、set-e 容错、grep gate rename、指引精度），但全部已在本分支内的后续 commit 修复。确认修复到位，不产生新 action。属于开发期快速迭代修复模式分析，非遗留问题。

**对抗镜2**：NO FINDINGS。6 个关注点逐一核实，全部 refuted（null/empty 区分合理、front-matter 模式实测正确、值传递安全、golden test 覆盖正确、预扫描衔接自洽、model-tiers 既有盲点非新引入）。

### 修复 / defer 台账

自动修 2 项 [impl-review-fix]：
- F1：`roadmap_writeback_draft.py` 加 ship-gate 块内 verify 重复键预扫描
- F2：`anchor_lint.py`（两份）`sys.exit(1)` → `raise RuntimeError` + `_metrics_enabled()` 包 `RuntimeError → MetricsError`

Defer 3 项 → todolist：
- F3：ship_gate.py yq subprocess 加 timeout/OSError（低概率，④ 简化）
- F4：运行时 yq 版本校验 ≥4.16.0（低概率，setup.sh 已覆盖）
- F5：CI yq 下载加 SHA-256 校验（安全加固类）

复审 1 轮（硬上限）：修复 diff 无新 Critical/Important，通过。

### 度量锚

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致0/高2/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="3" 采纳="0" 裁掉="0" defer="3" 独立="0" sev="致0/高0/中0/低0" -->

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="true" -->

<!-- sdflow:declared-sites v1 declared="code-voice" -->

### 结论

☑ 建议进 /sdflow-done
☑ defer 残差已入 todolist（hand-off 会引用）
