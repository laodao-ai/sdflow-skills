---
ship-gate:
  code_review: pass
  reviewed_sha: 867c97566ca9990d55015ced7bf2ccf5ad1605ba
---

## code-review 报告 — fix-windows-encoding-crash

### 命中范围

栈：Python / Bash / GitHub Actions；清单：CR-01~09（无适用领域 delta）。
gstack/review 原生 scope-drift/完成度审计：5/5 tickets 完成；发现草稿末尾两个范围外空白行并已自动清理。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-14,TG-18,TG-23" -->

### 子代理能力锚

Codex 能力探针实际返回 `PROBE_CODE_REVIEW_OK`；该结论是主 session 语义观察，不是机械门。

<!-- sdflow:fanout-capability v1 host="codex" subagents="available" mirrors="domain,adversarial,grounding" -->

### Findings（置信 ≥80）

- [高] canonical / dogfood mirror 漂移 | `sdflow-init/assets/workflow/tools/trivial_shape.py:214` | Task 3 后 canonical 新增 UTF-8 解码但镜像未再次同步 | 置信 96 | 已修[impl-review-fix]：正式 update 同步并增加 parity 回归。
- [高] Windows CI 可在第五门失败时假绿 | `.github/workflows/windows-recorder-smoke.yml` | setup 为 warn-only，原步骤只拒绝异常文本 | 置信 93 | 已修[impl-review-fix]：GBK job 直接严格运行编码卫生检查器。
- [低] scope drift | `docs/drafts/20260712.md` | 分支带入两个无关尾部空白行 | 置信 100 | 已修[impl-review-fix]。

### 已裁掉（反静默压制，可审计）

- X1 历史镜建议把存在性检查升级为执行路径/顶层语义验证。裁掉：`design.md` 明确选择整文件存在性检查并拒绝语义扫描；采纳会加宽已批准目标，不是实现缺口。
- <80 项：无。

### 修复 / defer 台账

自动修 3 项[impl-review-fix]；自动选推荐 0 项；defer 0 项。修复提交：`9823969`。

### Outside voice

Windows 上后台 cross-model helper preflight 未通过 POSIX gate，按协议运行同族只读 fallback；fallback 独立命中两项已采纳 finding。未转录 helper stderr 内容。

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="codex" runner="codex" reason_code="preflight-error" findings="2" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="code-voice" -->

### 陈旧重审补记（2026-07-29）

- 审查范围：`98239697b5b9fe496bd0ae7c175b1812bc9c5099..dbb8763856c0297a9868b75f8f516f7ccbca0abd`。
- 首轮终验发现 Windows probe 在空目录直接 `update` 必败；修复为先 `init` 铺设再以 GBK `update`，领域镜与对抗镜复核 CLEAN。
- 对抗镜另发现 cp936 console 路径经 warn-only `setup.sh` 可假绿；已改为直接运行 fail-closed 编码门，并保留重定向 setup 日志异常断言。
- 最终领域镜发现常驻测试未守 `chcp 936` 的同 step 顺序；已用连续块断言封闭。最终领域/对抗复核均 CLEAN，聚合验证 18 passed、1 deselected，证据统一锚定 `dbb8763856c0297a9868b75f8f516f7ccbca0abd`。
- 远端 `windows-latest` 尚未实际运行，按契约记为未覆盖，不伪报通过；不构成已证实的代码 finding。
- 强终验进一步证伪 Git Bash 不解析裸 `chcp`；最终改为 `chcp.com 936`。领域镜与对抗镜均在 Git Bash 实跑返回 0，并验证严格 checker 后续可达；连续块测试同步钉死可执行名与顺序。最终复审 SHA 为 `ca6d17c519dea841e4a59c846e41b2a16afbb3a6`，结论 CLEAN。
- `sdflow-done` 的真实 issues sweep 随后暴露 `_scan_pool` 动态 `**kwargs` 站点仍回落 GBK。`867c97566ca9990d55015ced7bf2ccf5ad1605ba` 已补 UTF-8/replace 与嵌套 reindex→scan 回归；对抗镜在 cp936 复现旧崩溃并验证新路径正确解码 emoji，全仓动态 kwargs 站点重扫无遗漏。领域镜确认代码 CLEAN，并据新事实把四件套计数校正为 16 站点 / 15 编辑点。最终结论 CLEAN。

### 度量锚

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="codex" runner="codex" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="0" sev="致0/高2/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="codex" runner="codex" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="codex" runner="codex" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="codex" runner="codex" site="—" findings="1" 采纳="0" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="codex" runner="codex" site="code-voice" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="0" sev="致0/高2/中0/低0" -->

### 结论

☑ 建议进 `/sdflow-done`　□ defer 残差已入 buglist/todolist
