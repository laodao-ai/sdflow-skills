# hand-off — async-outside-voice

> 异步人类再入口 + 下个 change 种子。verify 判 PASS 之后、archive 之前产出。
> 每条「完成」均已复核锚点存在性（非搬运 verify 的 ✅）。

## ✅ 完成了什么

| 交付 | 锚点（已复核存在） |
|---|---|
| 两评审 SKILL 的 host-adaptive async 调度段（marker 圈定、站点无关） | `sdflow-spec-review/SKILL.md` / `sdflow-code-review/SKILL.md` 的「outside-voice helper 调用协议」节；`check_async_branch_parity.py` exit 0 |
| 机械等值门（两段字节相同，漂即红） | `hack/check_async_branch_parity.py` + `hack/tests/test_async_branch_parity.py`（26 用例）；实测破一字节 → exit 1 + 精确行号 |
| 等值门接进 CI（此前 warn-only + CI 不跑 ⇒ 目标态下形同虚设） | `.github/workflows/mechanical-gates.yml`（parity / principles / 全套件三门各自独立跑） |
| declared-sites per-site 完整性核（补家族级门盲区） | `anchor_lint.check_declared_sites`；`test_ds_*` 系列；**实战验证：它抓到了本次 code-review 报告自己漏收 hr-tg 站点**（旧家族级门判 CLEAN） |
| per-run 不可变 context 路径 + dispatch manifest | 两 SKILL context 构造节（`mktemp -d` 原子占坑 + 同调用内取回字面 run-id + `printf` 落真制表符） |
| 退出码经 **runner 不可写的 sidecar** 取得 | 两 SKILL ④⑤；delta spec「退出码不可被 runner 伪造」Scenario；sidecar 三态实测（正常落 rc / 被杀缺席 / 内容非数字） |
| async 三条件（host=claude ∧ 后台可用 ∧ **主 session 已确证**） | 两 SKILL 执行模式矩阵行；delta spec 头条 Requirement + 降级 Scenario |
| 收益面端到端实证 | voice 421s > 300s 同步窗口 ⇒ 同步分支必被杀而 async 跑到 exit 0；真 exit 124（900s 撞天花板）；主 session 后台 702s/exit 0/ppid 稳定 |
| 承重墙零改动 | `git diff main...HEAD -- sdflow-init/assets/hack/outside-voice.sh` = 0 行；锚契约全笛卡尔 golden 对拍 sha 相同 |

## ⏳ 未完成 / 延后

> ⚠️ **本段逐条列 ID，未引用批次** —— `issues.py sweep` 在本轮**静默失效**（exit=0 但 tagged 0 项、批次未建），
> 根因已立 **B11(P1)**。修好 B11 后可重跑 sweep 归批。

**Bug（buglist）**

| ID | 优先级 | 一句话 |
|---|---|---|
| B8 | P2 | 子代理上下文轮次终结会回收其在飞的后台任务（主 session 702s 实证不受影响）⇒ 后台任务 MUST NOT 由子代理跨轮次等待 |
| B9 | **P1** | `outside-voice.sh` 200KB 截断按字节切断多字节 UTF-8 → codex 拒收整个 prompt → 该次 voice efficacy=0。**本轮实地咬中**（code-voice 挂在这里） |
| B10 | P2 | helper 被 SIGTERM 时 runner 子进程 reparent 到 PID1 存活，脱离 harness 回收域跑满内层超时 |
| B11 | **P1** | `issues.py sweep` 对 canonical/overlay 模式条目视而不见 ⇒ done 收尾的 defer 分诊静默丢失 |

**Todo（todolist）**：T157（proposal 旧路径形态，**本轮已就地修**）· T158（run-id 新鲜度可机械化）· T160（3600 上界依据回写 design / DOC-1 理由入正文待拍）· T161（等值门只覆盖 marker 内，圈外相似段漂了不红）· T162（Codex 方向 efficacy=0 架构性无解）· T163（DRY 全抽取：async 段抽单一源注入）· T164（context 路径未引用的 shell 注入面）· T165（**R1 Scenario 1 的真实模型 >300s 未证**——本轮用 PATH shim 控 runner 返回时刻，编排路径全真但推理负载非真实模型）· T166（end marker 硬化时遇无法解释的 extract 行为矛盾，**已撤回该硬化**，带复现留查）· T167（archive 阶段同步 delta spec，**本轮已就地做**）

**被延后的决策**：无「无客观判据的 ≥2 方案」自动选。唯一一次方案替换（哨兵 nonce → sidecar）有客观判据（runner 有仓库读权限，可枚举取得 nonce），非拿不准。

**verify 的 Minor 缺口**：两 SKILL 的哨兵时代死文本（**本轮已清**）· `tasks.md` 旧协议描述（**本轮已附实况注记**）· 真 exit 124 的证据取自替换前的通道（代际差，sidecar 侧有三态实测未重跑 124，风险低）。

## ▶ 下一阶段建议

**优先级 1 — 开一个 `fix-outside-voice-robustness` change，一次清掉 B9 + B10**
两者都在 `outside-voice.sh`（本 change 的显式 Non-Goal 故未动），同一文件、同一类问题（截断与进程生命周期），
合并一个 change 做完符合「一个 change = 一个完整阶段结果」。B9 是 **P1 且已实地致 efficacy=0**，应最先做。
B9 修法方向：截断后按 UTF-8 字符边界回退（推荐 `iconv -c` 让工具自己回答）；B10：`trap … EXIT INT TERM` + 后台 runner + `wait`。

**优先级 2 — B11 单独快修**
它让 done 的 defer 分诊静默失效，**影响每一个后续 change 的收尾**（不只本仓）。修法：scan 按文件头 `mode` 分派读取路径；
并把「scan problems 非空」升级为非零退出——当前 exit=0 正是它静默的直接原因。

**优先级 3 — T163（DRY 全抽取）**
等值门已守住漂移，但两份逐字副本仍是维护负担；抽单一源注入后，T161（圈外不覆盖）一并消失。

**不建议现在做**：T158 / T164 / T166 属机械化加深与待查项，无紧迫性；T165 需一次自然长推理场景，等真实评审自然触发即可。

### roadmap 回填

`roadmap_writeback_draft.py` 未产出草稿（本 change 非 roadmap 驱动，无关联标记）。若后续认为它属某 roadmap 阶段，请手动回填。
