---
ship-gate:
  code_review: pass
  reviewed_sha: fd6d08d8c12578e5b8bf2d482200d68fe695fca2
---

## code-review 报告 — implement-workflow-optimization-2026-08-p3

### 命中范围

- **栈**: Python + Markdown（数据类 skill）
- **清单**: CR-01~11（code-review-base）+ CR-LLM-01~02（domains/llm）
- **Step1 scope 审计**: scope-drift 无实质越界（F2/F3 噪声归 diff 边界）；完成度 17/19 DONE + 1 PARTIAL（setup.sh 验证不可验）+ 1 NOT-DONE→已修（roadmap 回填）
- **HR-TG**: hit=[TG-07]（新增 skill）→ hr-tg outside voice 已执行
- **trivial_shape**: NOT_EXEMPT（exit 1）

<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="TG-07" declared="TG-01,TG-07" evidence="新增 sdflow-upstream-watch/ 顶层 skill 目录" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history,broad" -->

### Findings（已采纳，6 项，均已修 [impl-review-fix]）

| # | 来源 | 严重度 | 问题 | 修复 |
|---|---|---|---|---|
| 1 | 对抗1+领域 | Important | `cmd_advance` 的 `report_path.read_text()` 无异常保护，非 UTF-8 内容裸崩溃 | 包 try/except (OSError, ValueError) → AdvanceGateError |
| 2 | 对抗2 | Important | `_diff_dirs_sha256` 内 OSError 穿透 `_collect_source_safe`，丢掉已采集的版本对照数据 | except 扩为 (CollectError, OSError) |
| 3 | 领域 | Important | CollectError 消息含 Path.home() 绝对路径，模型转录进 git 跟踪报告泄露用户名 | 新增 `_tildify()` helper，全部 CollectError 路径统一脱敏 |
| 4 | 领域 | Important | SKILL.md 缓存路径模板 `<source>.git` 与实际 `superpowers-marketplace.git` 不匹配 | 按源分别列出真实路径 |
| 5 | code-voice+hr-tg | Important | `_observed_anchor` 对 status=ok 源不校验观测值非空，可写 null 锚 | 写锚前校验 anchor_sha/anchor_version 非空 + 2 条新测试 |
| 6 | scope 审计 | Minor | roadmap 阶段 3 里程碑回填未做 | 补 roadmap.md + task-log.md 回填 |

### 已裁掉（5 项）

| # | 来源 | 理由 |
|---|---|---|
| X1 | 对抗1-F2 | yq 挂起概率极低（本地二进制），即使触发也是 fail-loud 非静默。基准④ |
| X2 | 对抗2-F2 | 与采纳 #2 同方向的泛化（元数据/git 分步隔离），#2 已修复唯一实质丢数据场景。基准④ |
| X3 | code-voice-4 | cwd 守卫子串 `laodao-ai/sdflow-skills` 足够唯一，伪匹配概率极低。基准④ |
| X4 | 对抗2-F3 | facts 同秒覆盖概率极低（手动触发），且 facts 是 .gitignore 临时产物。基准④ |
| X5 | 对抗2-F4 | write_anchors 非原子写——断电截断概率极低，anchors 可再生（重跑一轮即恢复）。基准④ |

### defer（2 项 → todolist）

| # | 来源 | 内容 | 去向 |
|---|---|---|---|
| D1 | code-voice+hr-tg | advance 报告/facts 绑定强度改进（run_id/facts digest、拒绝旧 facts 重放） | todolist（超本 change scope，设计定的是零解析子串校验） |
| D2 | code-voice+hr-tg | superpowers 采集器误报其他插件变更为 delta（marketplace.json 共享文件噪声） | todolist（分诊层会压噪，改进开 todo） |

### 修复 / defer 台账

- 自动修 6 项 [impl-review-fix]（commit af1f7ae + checkpoint fd6d08d）
- defer 2 项 → todolist
- 复审 1 轮（硬上限），无新 Critical/Important

### 结论

☑ 建议进 /sdflow-done
☑ defer 残差已记录（D1/D2 待入 todolist）

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->
