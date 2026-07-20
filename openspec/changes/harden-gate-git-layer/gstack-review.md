<!-- sdflow:step1-broad-review v1 mode="native" -->

# autoplan 广审（Step1）— harden-gate-git-layer

**执行方式**：主 session 经 Skill 机制原生执行 autoplan，非子代理转述模拟。侧信道佐证：preamble 实跑
（`BRANCH=feat/harden-gate-git-layer` / `REPO_MODE=solo` / `SLUG=laodao-ai-sdflow-skills`），restore point 已落盘
`~/.gstack/projects/laodao-ai-sdflow-skills/feat-harden-gate-git-layer-autoplan-restore-20260720-200526.md`。

**scope 探测**：UI scope = **否**（4 处命中均为 `nav` 子串误匹配，无 UI 面）⇒ Phase 2 跳过。
DX scope = 是（退出码 / 诊断 / CLI 门禁，22 处命中）。

**双声**：Codex（`gpt-5.6-sol`，跨模型）+ Claude 子代理（`sonnet`，冷上下文）。首次 Codex 调用被 Bash 工具
默认 120s 外层超时掐断（外层短于内层），已按「外层 ≥ 内层」重跑取得完整输出。

---

## CODEX SAYS（CEO — 战略挑战）

**结论：不建议当前设计过门。** 已证实的 git 缺陷成立，但方案仍在加固**代理指标**，没有可靠定义「被审过的树」。

1. **〔阻断〕评审锚并未真正记录** — `report_last_sha()`（`ship_gate.py:234`）动态取「最后一次修改报告的提交」，
   而非评审时记录的 SHA；报告之后任何正文修订都会把锚前移。∴ spec 写的「已记录的旧锚经 rebase 成孤儿」
   在公共入口下并不成立。建议 producer 在 frontmatter 写显式 `reviewed_commit`。
2. **〔阻断〕锚查询保留一个直接 fail-open** — `run_git()` 把非零退出折成空串（`:169`），`report_last_sha` 用它，
   空串被解释为「报告未提交、fresh」。建议锚获取改 tri-state：`found / genuinely-uncommitted / git-failed`。
3. **〔P1〕失败语义自相矛盾，异常覆盖不完整** — spec 一处规定「进程异常」判 stale、另一处规定环境失败判
   `UNKNOWN(6)`；tasks 只捕 `FileNotFoundError`/`TimeoutExpired`，`PermissionError`（文件在但不可执行）仍逸出。
4. **〔P1 战略〕错过真正的 10x 重构，design 域论证循环依赖现状** — 「design 必须逐帧」唯一理由是既有 BR-7 按
   subject 豁免，这是拿既有代理机制证明目标必须继续依赖该代理。目标资产其实是「当前四件套是否仍等价于已批准版本」。
5. **〔P1〕四件套相互矛盾，无法作为实施合同** — proposal 仍写「两域统一」「抽共用源、design 逐字不变」，
   design 已决定两域不同原语；proposal 承诺 code 诊断含 commit，spec 明确接受无 commit SHA。
6. **〔P2〕code 诊断与现有数据通道不匹配** — `_stale_trigger_hint()` 强制读 `sha`/`subject`；两个消费方
   （`:1291`/`:1311`）立即二元解包丢掉 trigger；design 域分类实为 `frame-enum-failed`，tasks 写 `enum-failed` 却称「同名」。
7. **〔T189=P1 / B18=无问题〕** — B18 排除合理；T189 若采用目标态快照模型则是 design 新鲜度核心依赖，不能简单排除。

## CLAUDE SUBAGENT（CEO — 战略独立）

前提逐条去仓里核实（A1/A2/A3/A5/A7 全部核实为真），**未发现能推翻整个设计的前提错误**，ADR-1/2/3 论证质量高。四条 finding：

1. **〔medium〕未评估负向 pathspec 备选** — code 域可用 `git diff --quiet <锚> HEAD -- . ':!openspec'`，
   exit 0/1 直接判定，**零 Python 侧路径解析**，更贴合本仓基准 5「无界不手搓，让工具自己回答」。
   P2 诊断可懒加载（判 stale 后才取路径）。design.md 专门登记的「控制字符方向反转」坑正是 Python 侧解析带来的。
2. **〔medium〕ADR-5 无「备选（已否决）」** — ADR-1 刚论证「共用会诱导顺手统一改错方向」，ADR-5 转手让两域
   共享 `StaleResult`/`_stale_trigger_hint`，却一字未论证为何这次共享安全。
3. **〔medium〕P1 超时只堵单次调用，未堵 design 域聚合暴露面** — ADR-4 自己承认 30N 残余但未给下一步处置。
   若超时根因是系统性的（NFS 抖动 = ADR-4 自己举的例子），N 次各卡 30 秒是真实发生而非理论上界。
4. **〔low〕范围确认** — T189/B18 排除均核实为真正不同面，切分正确。全仓另有 ~8 个脚本存在同类 git 调用安全面
   （仅 `devenv_scaffold.py` 已有 timeout+异常防护），优先级排序合理，建议记独立 todolist。

## CEO 双声共识表

```
  维度                                Claude  Codex  共识
  ─────────────────────────────────── ─────── ────── ────────
  1. 前提有效？                        是      否     DISAGREE
  2. 是该解的问题？                    是      部分   DISAGREE
  3. 范围校准正确？                    是      否     DISAGREE
  4. 备选充分探索？                    否      否     CONFIRMED（均判不足）
  5. 竞争/市场风险覆盖？               N/A     N/A    N/A（内部工具）
  6. 六个月轨迹稳健？                  否      否     CONFIRMED（均指出残余）
```

**分歧根源**：Claude 镜按「本 change 的既定 scope（git 调用层）」评估，判前提成立；Codex 镜把
scope 本身当作评估对象，判「加固代理指标而未定义被审过的树」= 前提不成立。两者不矛盾——
Codex 挑战的是 scope 边界，Claude 确认的是 scope 内自洽。**该分歧升为设计门决策 Q2。**

**跨阶段主题**：两镜**独立**命中「锚点模型是未被处理的根因」（Codex 阻断-1/2；Claude 镜的 pathspec 建议虽
角度不同，但其「让工具自己回答」的方向同样指向"别用代理量反推"）。高置信信号。
