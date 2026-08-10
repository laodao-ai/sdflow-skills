---
ship-gate:
  code_review: pass
  reviewed_sha: 3a0b07dbb9be1f04719fcdc4afa5582f631a9c67
---

# code-review 报告 — implement-workflow-optimization-2026-08-p1

## 命中范围

栈: Python/Bash + Markdown（skill 集合仓）
清单: CR-01~09（通用 base）；领域清单未覆盖（本仓不命中 TG-01/02/03）
Step1 自持 scope 审计: 16/16 tasks DONE，无 scope creep；Non-Goals 全部遵守

<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history,broad" -->

## Findings（置信 ≥80）

### [Important → auto-fix] OV#3 零分母未标「参考」

`sdflow-retro/scripts/retro_report.py:542`（修复前）：`if denom and denom < FIXRATE_MIN_SAMPLE:` — `denom=0` 时 falsy 跳过「参考」标注，违反 `FIXRATE_MIN_SAMPLE=5` 闸门。

**已修[impl-review-fix]**：改为 `if denom < FIXRATE_MIN_SAMPLE:`（commit `3a0b07d`），复审一轮通过。

### [Minor → defer] F1 endswith 子串碰撞（佐证 flag）

`sdflow-retro/scripts/retro_report.py:449`：`entry.endswith(f"-{name}")` 用后缀匹配归档目录名，change 名互为后缀时误命中。**影响仅限展示 flag**（design D2 已拍板「降为佐证 flag，不参与判定」），不影响实修率数值。同文件已有正确的 `_DATE_PREFIX` 正则可复用。

→ defer todolist（后续改用 `_DATE_PREFIX.match` 精确匹配）

### [Minor → defer] OV#2 表格行分类用整行非处置 cell

`sdflow-retro/scripts/retro_report.py:434`：`_fr_classify_status(line)` 用整行而非已提取的 `table_disp` cell。若「问题」列恰含 `已修[impl-review-fix]` 而处置列是其他值，会误判 fixed。**真实语料试算（三轮）未发现此形态**；但目标态下理论可构造。

→ defer todolist（对表格行改传 `table_disp` cell）

### [Minor → defer] F2/OV#6 残留判定单信号

`sdflow-issues/scripts/issues_v2.py:643`：`residue = old not in TERMINAL_STATUSES[pool]` 单一信号，手工损坏 closed/ 文件（将 status 改为非法值）会被误判为残留。**design D3 已接受此简化**（基准④低概率）。

→ defer todolist（可在残留分支额外校验三终态字段已 None）

### [Minor → defer] OV#1/对抗-1 timeout 覆盖缺口

`sdflow-init/assets/hack/token_snapshot.py:249-253`：`_resolve_change_dir()` 两次 git 调用在 `_install_timeout` 之前执行，最坏 ~20s 而非 10s。核心安全约束（不挡 checkpoint）已由 `|| true` + subprocess timeout 满足。

→ defer todolist（统一到 alarm 窗口内）

### [Minor → defer] OV#5 空 reason 通过

`sdflow-issues/scripts/issues_v2.py:1326`：argparse `required=True` 不拒绝空串 `--reason ""`。

→ defer todolist（加 `not reason.strip()` 校验）

### [Minor → defer] OV#4 SDFLOW_HOME 未尊重

`sdflow-init/assets/hack/checkpoint-commit.sh:47`：硬编码 `~/.sdflow/hack/`。设计选择——checkpoint 恒用默认安装路径。

→ defer todolist

### [Minor → defer] F3 docstring 不一致

`sdflow-init/assets/hack/token_snapshot.py:224-225`：`_collect` docstring 声称「唯一允许上抛的是 `_Timeout`」，但 `_accumulate_usage` 的 `except Exception` 会先吞掉它。行为等价（两分支产出相同降级行），仅文档层不符。

→ defer todolist

## 已裁掉（反静默压制，可审计）

| # | 来源 | 理由 |
|---|---|---|
| 对抗-1 | 对抗镜1 | 置信 70 < 80，已合并进 OV#1 |
| F4 | 领域镜 | 置信 40 < 80（全量重读性能，design 已接受的无状态口径） |
| 对抗-2 全部 | 对抗镜2 | refuted=true（四个关注点逐一核查无泄漏/数据错误） |
| 历史镜全部 | 历史镜 | 无新 findings（已知问题修复均已稳定） |

## 修复 / defer 台账

自动修 1 项 [impl-review-fix]：OV#3 零分母「参考」标注（commit `3a0b07d`）
defer 7 项 → todolist（F1 endswith / OV#2 整行分类 / F2 残留单信号 / OV#1 timeout / OV#5 空 reason / OV#4 SDFLOW_HOME / F3 docstring）

## outside-voice

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="6" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="code-voice" -->

## 结论

- [x] 建议进 /sdflow-done
- [x] defer 残差已入 todolist（hand-off 会引用）
