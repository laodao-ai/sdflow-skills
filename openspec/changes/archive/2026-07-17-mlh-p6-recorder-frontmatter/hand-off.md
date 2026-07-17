# Hand-off — mlh-p6-recorder-frontmatter

> 收尾产出（verify 之后 / archive 之前）。verify 判定 **PASS**（每 ✅ 附机验锚点，本段已复核锚点存在性）。日期 2026-07-17。

## ✅ 完成了什么

本 change 兑现 mechanical-layer-hardening **端态 A**：recorder 索引从字符串表迁入 versioned frontmatter，历史表冻结为 dual-read/promotion 半场。

| 需求 | 落地 | 机验锚点 |
|---|---|---|
| **SW-RI-1** Shared Frontmatter Envelope + same-file overlay + marker prose | buglist.py / todolist.py strict bytes parser/renderer；每 dated 文件一次 binary read，只解释唯一 `sdflow-issues` 子树 | 三 recorder 定向套件 `-W error` **445 passed, 2 skipped**（本轮独立复跑） |
| **SW-RI-2** 两池全局 semantic ID + exclusive snapshot lock | `recorder_lock` 三份镜像 `O_WRONLY\|O_CREAT\|O_EXCL`（issues.py:203）；20 进程并发 add 断言 ID 唯一 + 失败均报 lock occupied + 最终 scan 集合==成功集 | test_*concurrency*、20-proc 并发测试真承重 |
| **SW-RI-3** 单次 rename snapshot + provenance-backed retry | `read_rename_snapshot()` 每 dated file read/parse=1，rename 每 pool `scan --json`=0；registry-first 原子写 provenance | test_task4_rename_snapshot.py:638-639（reads==1/parses==1） |
| **SW-RI-4** reindex 可观测性 + fatal/nonfatal 分层 | frontmatter/ID/consumer JSON 损坏始终非零不改 INDEX/batches；legacy arity 默认回显、`--strict` 非零 | consumer validator raise 路径无 `.get([],)` 兜底 |
| **DG-RI-1** 三镜像一致性 | mirror THREE_WAY/TWO_WAY roster 完备（宽于 spec 最低要求） | 7.2 grep：三脚本无 `import yaml` / 无跨 recorder import / 无 `_reject_cell_unsafe` 活引用（三项全空） |

**全局验证锚**：全仓 `pytest -W error` → **1619 passed, 2 skipped**（本轮独立复跑与 tasks 声称吻合）；`openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` valid；`git diff --check` 干净。

**7.5 fold 收口**（全仓 `-W error` 面治暴露的 4 个 pre-existing 未关闭文件站点）：`sdflow-maintain/scripts/maintain_scan.py:184/:245`、`sdflow-maintain/tests/test_maintain_scan.py:224`（改 `with open`）、`sdflow-architecture/tests/test_sad_scaffold.py:525`（并发 Popen 改 `communicate()` drain）。

**dogfood 兑现**：T85/T66/T67/T146 经真实 recorder 命令提升为 same-file overlay 并置 DONE，旧表逐字节不变；T2 保持 DONE 且记录根治兑现。

**真 Windows 锚**（7.4）：Windows local-disk smoke 在 `windows-latest` run 29568476168 / commit `ba004e1` 取无 skip `2 passed`；macOS 上 2 skip 由 `skipif(platform!=win32)` 门控，非假绿。

## ⏳ 未完成 / 延后

- **批次 `mlh-p6-recorder-frontmatter`**（见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`）：
  - **T155**（OPEN→PROPOSED，本次 sweep 归入）—— 全仓 `pytest -W error` 常态化为**持久 CI 门**。本 change 是本仓第一次全仓跑 `-W error`，一次暴露 4 处潜伏 7 天的未关闭文件债；只修站点是点治，未立守卫则同类债会再潜伏。留待独立 hardening change。
- **T156**（change=`-`，独立，不挂本批次）—— sdflow-devenv 配 CI 的 P2 决策示范清一色 GitHub Actions、未显式化「硬门/软门」降级边界，对「不管什么项目都能配」承诺留平台假设漏洞。本次收尾设计讨论衍生。
- **verify Minor 缺口**：无。核心与 Minor 均无缺口（PASS）。诚实边界（Windows-only 2 skip 有真 runner 锚、network FS/power-loss 明确声明非承诺）属合法残余划分，非缺口。
- **被延后的 ≥2 方案决策**：无（本 change 收尾无待人复核的自动选项）。

## ▶ 下一阶段建议

**roadmap 状态**：mechanical-layer-hardening `roadmap.md` v3（2026-07-17）已由 task 6.4 手动回填 **P6 交付对账**（P6 标 ✅ 已交付、里程碑已写、T85/T66/T67/T146 DONE）——**roadmap 本体无需额外人工回填**。Leg 2（去字符串化）P5/P6 均已交付；roadmap 仅剩 4.A/4.D.3（embedded producer 契约未就绪，正当等待）。

> roadmap 回填草稿未生成：`roadmap_writeback_draft.py` exit 3（change 名 `mlh-p6` 前缀不匹配助手的关联规则、change frontmatter 无 roadmap marker）。若希望该助手将来自动识别 mlh 系列，可给 change frontmatter 加 roadmap marker（低优先，非阻塞；roadmap 交付记录已由 6.4 手动兑现）。

**下一个 change 种子（优先级序）**：

1. **T155（推荐先起）** — 全仓 `pytest -W error` 常态化为持久 CI 门。本仓在 GitHub → GitHub Actions required check（硬门）。属 mechanical-layer-hardening 同宗（机械层固化：一致性面焊死）。`opsx:ff` 起手，需设计触发条件 / matrix / `-W error` 覆盖范围，及与现有 `windows-recorder-smoke.yml` 的关系（并列 job 还是合成 matrix）。
2. **T156（其后）** — sdflow-devenv 多平台 CI 载体泛化（github/gitlab/gitea 探测分流 + pre-push 兜底 + 硬门/软门降级显式化）。能力级改动，走自己的设计门，可蹭 T155 的结论。

**建议顺序**：先归档 + merge 本 change 到 main → 干净后 `opsx:ff` 起 T155。
