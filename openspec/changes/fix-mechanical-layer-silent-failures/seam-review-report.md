# 接缝冷复审报告 — fix-mechanical-layer-silent-failures

> 对象：**仅本轮 amendment 的接缝**（`checkpoint(grill)`..HEAD，453 insertions / 8 files），不重审已定结论。
> 阵容：接缝镜 A（一致性 · sonnet）、接缝镜 B（攻击新机制 · sonnet）、跨模型 voice（codex `gpt-5.6-sol`，rc=0，`truncated=false`）。
> **本文不落 spec-review 层锚**：`declared-sites` 公式只允许 `design-voice`/`hr-tg` 两站点，为本轮补审硬塞第三站点会让 per-site 核判红——那道门是上个 change 自己加的，不绕。

## 结论

**接缝不干净，且出现「同一处错第二次」。** 建议**不要**再做第四轮就地返修，改走下方「收敛困难」处置。

## 致命 / 高危

| # | 来源 | 发现 | 已核实 |
|---|---|---|---|
| S1 | 镜A + voice | **exit 2 旧口径残留 7 处**（tasks 5.2/5.3/5.7/§7标题/7.1，design F6/F8/Risks/切片表，proposal）——与 spec 已改判的 `4` 字面对立。照 tasks 实现会**原样复现刚被推翻的 DIR-2** | ✅ grep |
| S2 | 镜A | **tasks 4.5 仍写「MUST 抽成单一函数共用」**，与同文件 3.10、design D5′、spec「MUST NOT 要求调同一函数」直接对立 ⇒ 复现 DIR-3 | ✅ grep（**已就地修**） |
| S3 | **voice** | 🔴 **rename 拓扑仍是虚构的（第二次）**：spec 称 rename 后半经 subprocess `scan --json`；实际 `_reindex_core(root, snapshot=updated)` **仅在 `snapshot is None` 时**才 `read_pool`，且文件头明写「整个 rename 不调用 recorder `scan --json`」⇒ **rename 全程 in-process**，「additive 字段保护后半」不成立 | ✅ 读码 |
| S4 | **voice** | 🔴 **退出码根本无法表达「可否重试」**：`ValueError→2` 同时覆盖 malformed JSON / frontmatter 损坏 / rename 参数错（**永久失败**）；`_die→1` 混合输入错误与瞬时失败。∴ 把 `2` 定义成「锁冲突可重试」、`1` 定义成「可收敛」，**仍会对永久故障无限重试**。码位盘点不够，须按异常类型拆码 | ✅ 读码 + 实测 |
| S5 | 镜B | **argparse 用法错误也 exit 2**（实测 `issues.py bogus-cmd` rc=2），码位盘点漏此路 | ✅ 实测 |
| S6 | 镜B | **无条件 reindex 把全仓历史阻断耦合进本 change**：阻断若源自与本次无关的既存脏数据 ⇒ 本 change 的 sweep 永久 exit 4 且「重跑无用」对它自身成立 ⇒ **done 链路被无关数据锁死** | ✅ 逻辑 |
| S7 | **voice** | **三方 code 集「完全相同」取错比较范畴**：parser 有 pool-specific 语义（缺 marker / 缺详细块**只对 bug** 产诊断）⇒ 应改 `buglist(bug)↔issues(bug)`、`todolist(todo)↔issues(todo)` 两组 parity，跨池只比声明为共有的码 | ✅ 读码 |
| S8 | 镜B | **run-id provenance 锚由谁写？** D7 刚批判「锚行是模型抄写非机械信号」，其补丁「报告落受校验 run-id 锚」**没说这个锚谁写**——两层 SKILL 是纯 markdown 编排，大概率仍是模型抄 ⇒ **同款「捕获权在被监管方手里」复发** | ✅ 逻辑 |
| S9 | voice | **sidecar 生命周期漏「无 render」合法态**：helper 缺失 / `host=unknown` 根本不调 helper、`secret-hit` 在算 `OV_TRUNCATED` 前就退出，但这些情形**仍须落 outside-voice 锚**。须定义完整状态矩阵，覆盖 helper-missing / host-unknown / preflight-fail / secret-hit / fallback-unavailable / reuse 六类 | ✅ 读码 |
| S10 | 镜B + voice | **`blocking` 坏形状未定义 fail-closed**：只区分「缺席」vs「`[]`」，未定义 `null` / object / string / 元素缺 `code`。实现若写 `data.get("blocking") or []` 会**把坏 producer 静默解释成无阻断** | ✅ 逻辑 |
| S11 | 镜B | **fixtures 分发渠道选错**：D5′ 写「随 `sdflow-init update` 分发」，但消费仓 `openspec/workflow/` 拷贝**不含 `tests/`**；真正消费方是三个 skill 自己的 pytest ⇒ 应放三 skill 共用的仓内路径（随 `setup.sh`） | ✅ CLAUDE.md |

## 被证伪（对设计有利，记录以免重提）

- **两阶段 sweep 的 TOCTOU**〔镜B〕：`main()` 对整个 sweep 持单一 `recorder_lock`，scan 子进程经 `recorder_child_env` 作 participant 加入同一锁域 ⇒ 两阶段之间**无外部写入窗口**，未找到洞。

## voice 提的一条建议（值得单独记）

**加 stale-phrase 门**：机械禁止 `前置于任何 discovery/stat/open`、`单一函数共用`、`阻断.*exit 2`、`ship.*sweep` 等**已被推翻的措辞**出现在非考古区。
——这是对本 change 反复出现的「返修不传导」问题的**机械化解法**，比再审一轮更根治。
