---
ship-gate:
  code_review: pass
---

## code-review 报告 — async-outside-voice

### 命中范围

栈: Python stdlib 工具脚本 + Markdown 指令文档（skills 仓）
清单: CR-01~09（`code-review-base.md`）
⚠️ **领域清单未覆盖（F13 显式降级登记）**：`code-checklists/domains/` 仅有 backend / backend-go / embedded* 五份，
本仓命中栈无对应清单 ⇒ **本轮未做领域清单审**，未宣称通过。补充判据取本仓 `CLAUDE.md` 五条设计/分析基准 + `openspec/rules/doc-authoring.md`。

diff base = `97f562eed0a2f6955eb440b8d0c3c472c05cbc4f`（28 commits，39 files，6246 insertions；其中 18 个文件是 `impl-reports/` 下的评审报告与 diff 包）

**gstack/review（Step1）结论**：
<!-- sdflow:step1-broad-review v1 mode="native" -->

```
Scope Check: CLEAN（一处已声明 fold）
Intent: Claude 宿主把 outside-voice exec 移出关键路径，Codex 保持同步 + 诚实降级
Delivered: 两评审 SKILL 的 host-adaptive async 段 + 字节等值门 + declared-sites per-site 核 + 实证
Plan items: 31/31 DONE（superpowers-plan.md）；tasks.md 0 勾（正确——archive 阶段才勾）
```

scope 外候选逐条判定：tracker 登记 / config 键 / bundle 副本同步 / anchor_lint+tests / setup.sh 挂载 **均在 tasks 明列范围内**；
唯一真 fold = `sdflow-buglist/tests/test_task5_delivery_contract.py` 的潜伏缺陷修复（卡收尾门、3 行 additive、implementer 已自陈）。

### TG 判定与 HR-TG 交集

<!-- sdflow:hr-tg v1 hit="TG-06,TG-08,TG-09,TG-16,TG-17,TG-26" declared="TG-06,TG-08,TG-09,TG-16,TG-17,TG-26" evidence="voice 单站点生命周期状态机(TG-09)、并发后台任务+barrier(TG-26)、出境信任边界与 secret_scan(TG-17)、外部 runner 调用方式变更(TG-08)、900s/300s 超时预算(TG-16)、declared-sites 锚成为下游消费仓共享数据契约(TG-06)" -->

HR-TG∩ ≠ ∅ ⇒ 已单开领域专属 cross-model（见下）。

### 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

（第三镜为历史镜，按跨层共用三 token 词表借用 `grounding` 记「第三个 fan-out 镜跑了」；镜的精确身份见 lens-metric 的 `lens="history"`。）

### outside-voice

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="claude" reason_code="exec-error" findings="1" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

**exit 1 → exec-error → 同族降级**。诚实登记：本次跨模型第二意见**未取得**，findings 计 1 条来自同族降级路径的实测产出（见下 C1）。
按「collect 只取结构化状态、MUST NOT 采信后台文件原始 stderr」——此处只记结构化字段：`rc=1`、`OV_TRUNCATED=true`、stderr 1 行。

> **这次失败本身就是最重的一条 finding**（C1）——根因见下。

**site="hr-tg"（HR-TG∩≠∅ 触发）：`rc=0`、未截断 ⇒ 真跨模型第二意见到手**，3 条 findings 全部采纳（含 1 条 critical 直接证伪了本轮 C2 的首版修法）。
context 34KB（刻意压在 200KB 截断线下以规避 C1/B9）。

> 🔴 **这一站点是被本 change 自己新加的 per-site 机械核逼出来的**：报告初版只落了 `code-voice` 锚，
> 旧的家族级门（有 ≥1 条 outside-voice 锚即过）判 **CLEAN**，而新的 `check_declared_sites` 判
> **`site-missing-anchor: hr-tg`** —— 正是它被造出来要防的「并发 2 站点漏收一个」。**门抓到了造门的人。**

### Findings（置信 ≥80）

| # | 严重度 | 项 | 证据 | 处置 |
|---|---|---|---|---|
| C1 | **Critical** | 200KB 截断按字节切断多字节 UTF-8 → codex 拒收整个 prompt → 该次 voice efficacy=0 | `outside-voice.sh:160,162`；本轮实地触发（rc=1，`invalid byte at offset 107475`）；复现：`head -c 102400` 该 context → 非法 @102399，残字节 `\xe6` | **defer → B9(P1)**（脚本零改动是本 change 显式 Non-Goal） |
| C2 | **Critical** | 退出码走 stdout 不可信：wrapper 被回收未发时，voice 正文一行伪造即成唯一来源 → 被杀的运行拿到跨模型信用 | 两 SKILL async 段 ⑤；正文出现该字样的概率在本 change 上是 1（自指） | **已修（首版修法被跨模型 voice 证伪后替换）**〔impl-review-fix〕：见 C2' |
| C2' | **Critical** | **首版修法（per-run nonce 哨兵）无效**：nonce 取自仓内 `.outside-voice/<run-id>` 目录名，而 runner 被授予仓库**读取**能力（claude `--tools "Read,Grep,Glob"` / codex read-only sandbox）⇒ **无需猜，枚举目录即可**；进程列表亦可能暴露含 nonce 的祖先命令。把认证建立在「模型读得到的字符串」上无效 | hr-tg 跨模型 voice 第 1 条（critical）；`outside-voice.sh:41-44,209-224` | **已修**：退出码改走 **runner 写不了的 sidecar** `{run-dir}/<site>.rc`（四旗承重墙只给只读工具集、无 Write/Bash ⇒ 写不了）；**stdout 哨兵整套废弃**。文件缺席 = 任务被回收 ⇒ exec-error，诚实降级。实测三态：正常落 rc / 被杀缺席 / 内容非数字皆按预期 |
| C3' | **Important** | C3 的修复**只写了 prose、没改矩阵**：矩阵 async 行条件仍是 `host=claude ∧ background="available"`，降级行也只覆盖 `background="unavailable"` ⇒ 执行者照矩阵走仍会复现被回收 | hr-tg 跨模型 voice 第 2 条（high） | **已修**：async 行条件补 **∧ 主 session 已确证**；降级行改为「`background="unavailable"` **或** 主 session 未能确证」 |
| C5 | **Important** | 四件套仍描述旧协议（裸哨兵三条、单条件 async），与代码审后的实现**不自洽** | hr-tg 跨模型 voice 第 3 条（high）；`design.md:40-42`、`tasks.md:16`、`spec.md:7,22-24` | **defer → T167**（改四件套触设计门失鲜）；**archive 阶段 MUST 同步 delta spec**，清单已写进 T167 |
| C3 | **Important** | 后台能力自探对「轮次终结回收」结构性失明：探针同轮次内取回 ⇒ 子代理上下文必报 available，长任务照样被吞 | 两 SKILL async 段 ②；B8 实证 | **已修**：async 条件改为**两个**（探针过 **且** 确证主 session），无法确证即 sync 降级；附 702s 主 session 实证依据 |
| C4 | **Important** | 等值门在目标态下基本不跑：`setup.sh` warn-only、默认 `python3` 无 pytest、CI 只跑一个 Windows smoke ⇒ ADR-5「机械等值门一次封死漂移面」的承诺不成立 | `setup.sh:236-241`；`.github/workflows/` 仅 `windows-recorder-smoke.yml` | **已修**：新增 `.github/workflows/mechanical-gates.yml`，三门（parity / principles / 全套件）各自独立跑、各自能红 |
| M1 | Minor | `_hr_tg_intersect_nonempty` 用 `anchor_prefix` 识别 hr-tg 锚，与 `check_hr_tg` 的整行严格正则形成**第二识别源**（docstring 自称同源） | `anchor_lint.py:534` | **已修**：改用 `_HR_TG_ANCHOR_FULL_RE` 同源 |
| M2 | Minor | `except EmitError:` 吞掉 `_parse_site_csv` 区分的两种原因（空 cell / 域外记号） | `anchor_lint.py:592` 附近 | **已修**：`as e` + `detail=str(e)` |
| M3 | Minor | helper 被 SIGTERM 时 runner 子进程 reparent 到 PID1 存活，脱离 harness 回收域跑满内层超时，输出写进已删 fd | 对抗镜实测 `39014 1 timeout -k 10 60 sleep 45` | **defer → B10(P2)**（需动脚本，Non-Goal）。**同时校正 design**：对抗镜实测 bash 在 SIGTERM/SIGHUP 下**会**跑 EXIT trap ⇒ design.md:118 的 workdir 泄漏面比其以为的**窄**，真正泄漏的是 runner 进程 |
| M4 | Minor | end marker 边界未与 start 侧对称硬化 | `check_async_branch_parity.py:73` | **defer → T166**：尝试硬化时遇到**无法解释的 extract 行为矛盾**（同进程内用模块自身 END_LINE 算出 `ends=[]`，extract 却正常返回；已排除字节码缓存 / 模块遮蔽 / 重复定义）⇒ **撤回该硬化，不合入解释不了的门**，带完整复现留查 |

### 已裁掉（反静默压制，可审计）

- **X1 · 对抗镜1「manifest 并发追加会撕裂」** → 裁掉：单写者（主 session）+ `O_APPEND` 单次 <PIPE_BUF write 原子。对抗镜自己实测后 refuted。
- **X2 · 对抗镜1「run-id 两轮并行互踩」** → 裁掉：`mktemp -d` 原子占坑 + 字面串回取，实测同秒两次必得不同目录（Task 1 已实证）。
- **X3 · 对抗镜2「等值门测试可能不施力」** → 裁掉：该镜因本机 `python3` 无 pytest 而**未能验证**，属工具环境误判；编排层已用 `/usr/bin/python3` 独立跑过变异测试（4 个变异各致 ≥1 用例变红）。**但其衍生的 C4（门在 CI 不跑）成立并已修。**
- **X4 · 领域镜 F4「dogfood 自指」** → 裁掉：方向是 fail-closed 而非假绿，且已有用例覆盖 fence 内场景。
- <80 置信滤除：无（本轮各镜 findings 均有 file:line 证据或实测复现）。

### 修复 / defer 台账

- **自动修 6 项**〔impl-review-fix〕：C2'(退出码改 sidecar，废弃 stdout 哨兵)、C3+C3'(主 session 确证条件 + 矩阵行同步)、C4 CI 泳道、M1 识别口径同源、M2 报错细节保留。
- **defer 5 项**：B9(P1 UTF-8 截断)、B10(P2 孤儿 runner)、T166(end marker 异常待查)、T167(archive 阶段同步 delta spec)、以及先前登记的 T157/T158/T160–T165。
- **一次自我证伪**：C2 的首版修法（nonce）在同一轮内被 hr-tg 跨模型 voice 推翻并替换为 sidecar。**这正是 cross-model 层的价值**——同族镜（含我自己）全都默认了「随机后缀 = 猜不到」，只有跨模型那面镜子问了「它需要猜吗」。
- **T10 复核**：无「无客观判据的 ≥2 方案」自动选——C2/C3/C4 的修法均由对抗镜给出且有客观判据（可构造反例 / 可实测），M4 因无法解释而**撤回**（非自动选）。

### 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="4" sev="致0/高2/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="4" 采纳="2" 裁掉="1" defer="1" 独立="2" sev="致0/高0/中0/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="claude" site="code-voice" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="3" 采纳="3" 裁掉="0" defer="1" 独立="3" sev="致0/高2/中0/低0" -->

> 本轮最高价值镜 = **outside-voice(hr-tg) 跨模型**（3 findings 全采纳、全独立，其中 1 条 critical **推翻了本轮已经落地的一个修法**）与**对抗镜**（4 findings 全采纳，含 2 高危）。历史镜与 broad 各 0 findings（历史镜结论：本次改动与历史同向演进、无重蹈覆辙）。

### declared-sites

<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->

### 门禁复核

- `pytest -q` → **1667 passed, 2 skipped**
- `check_async_branch_parity.py` → ✅ 两段逐字节一致（含本轮新增的 nonce 与主 session 条件）
- `sync_principles.py --check` → ✅ 20 个投放面一致
- 全局软链未被改动（仍指向运行 checkout）

### 结论

- ☑ **建议进 `/sdflow-done`**
- ☑ defer 残差已入 buglist（B9/B10）/ todolist（T157/T158/T160–T166），hand-off 会引用
