# Tasks: sdflow-ship

> 真相源 = [proposal.md](./proposal.md) + [design.md](./design.md)（§三 gate 决策图 / §五 D1-D7）。全部未勾（ff 生成，实现在阶段三）。
> 需求 ID：**R-SS-1** 编排台账确定性（ADDED）· **R-SS-2** 模型档位映射（ADDED）· **R-SS-3** 阶段三连续+决策协议（MODIFIED）· **R-SS-4** 阶段二串行纪律（MODIFIED）。
> 机队锚定〔adr/0006〕：步序判定全脚本化（ship_gate.py + pytest），模型只执行 gate 判定与每步内部判断。

## 1. ship_gate.py（R-SS-1，先契约后实现，TDD）

- [ ] 1.1 契约头注释定死：D2 双输出（首行人读 + JSON{verdict,next,missing,reason}）、退出码 0/3/4/5、D5 机判锚点正则（`设计门拍板` / `结论[：:]\s*(PASS|FAIL)` / `建议进 /sdflow-done` 与 blocker 判）；入参 `--change <name>`（定位 openspec/changes/<name>/）+ `--root`；只读零副作用〔R-SS-1〕
- [ ] 1.2 实现 §三决策图全逻辑：pre-flight（报告在+拍板行）→ 5.5 条件（proposal TG-02 标注 grep）→ 6/7（superpowers-plan 存在 + 完成判据双通道：复选框全勾 ∨ SDD ledger 全 complete；双缺=UNKNOWN 停）→ 8（code-review-report 结论区）→ 9（verify 结论行）→ final（hand-off+archive+分支态）〔R-SS-1〕
- [ ] 1.3 pytest 全盘面态（tmp_path 构造 change 目录）：未过门拒跑 / 拍板行在则过 / TG-02 命中与否 / plan 缺→next=writing-plans / 复选框未全→继续实现 / 双缺→UNKNOWN / blocker→exit4 / verify FAIL→exit5 / PASS→next=done / 全通→SHIPPED；锚点正则字面断言〔R-SS-1〕

## 2. sdflow-ship skill（R-SS-3）

- [ ] 2.1 新建 `sdflow-ship/SKILL.md`：frontmatter（name/description 触发词：「ship 这个 change」「阶段三跑到 merge」「过完设计门了，跑起来」「/sdflow-ship」等）；正文 = chain 序列 + **每步前后 MUST 调 ship_gate 并遵判定**（禁 prose 步序）+ 门禁上抛话术（exit 3/4/5 各自的停法与转述格式）+ 逐步 checkpoint 约定（`~/.sdflow/hack/checkpoint-commit.sh`）+ 不越两人类点声明〔R-SS-1/3〕
- [ ] 2.2 D3 决策协议节（T10 认领）：三级协议全文 + 「禁自评置信唯一依据」+ 复核记录进 code-review-report 的格式约定〔R-SS-3〕
- [ ] 2.3 权威源 `assets/workflow/workflow.md`：阶段三步骤表加编排入口行（`/sdflow-ship {change}` 一次驱动 5.5→9；手动逐步为 reference）；决策 4 按 D3 改写（去"有把握自动选"）〔R-SS-3〕

## 3. model-tiers（R-SS-2，T11 认领）

- [ ] 3.1 `assets/workflow/config.template.yaml` 加 `model-tiers` 段：三档职责清单 + 各档 default（strong: opus / mid: sonnet / light: haiku）+ 段头注释（真相源声明、消费仓可改映射）〔R-SS-2〕
- [ ] 3.2 四个编排 SKILL.md（sdflow-ship/done/spec-review/code-review）模型选择节改引用：「档位职责与映射见 config.yaml model-tiers；无该段按内联缺省 opus/sonnet/haiku」——**保留各自现有职责表述，只把具体模型名替换为档位词+缺省注**；grep 断言四文件零裸"用 Sonnet/Haiku 作为规则措辞"残留（引用注除外）〔R-SS-2〕

## 4. T20 顺路（R-SS-4）

- [ ] 4.1 `sdflow-spec-review/SKILL.md` Step2 首句加 MUST 串行句 + 历史并行补救句（design D6 全文）〔R-SS-4〕

## 5. 测试与断言

- [ ] 5.1 全量 `python3 -m pytest -q` 全绿无 warning（233 + ship_gate 新用例）
- [ ] 5.2 grep 断言：workflow.md 无"有把握自动选"旧句；四 SKILL.md 模型节引用 model-tiers；spec-review Step2 含 MUST 串行句——命令与输出留档 change 目录 `assert-log.md`

## 6. 文档收尾与债务闭环

- [ ] 6.1 README Skills 列表加 sdflow-ship 行；ROADMAP：`opsx-ship-orchestrator` 行更名 `sdflow-ship`（materialize 注记+状态推进）；`adr/0004` 按其自带条款加标题注记（"落地名 sdflow-ship，见 adr/0007 命名规范"一行，不改历史正文）
- [ ] 6.2 债务闭环：T10/T11 set-status DONE（evidence=本 change commit + 文件:行）、T20 set-status DONE（evidence 同）；reindex 刷新 INDEX/批次
- [ ] 6.3 `update --dev --root .` 同步 instance；hand-off 预置：真实激活 = merge+push 后新会话 `/sdflow-upgrade`（沿 rebrand 模式），首次真实 ship 演练建议挑批次 T21-T24 的收尾小 change 当试车对象
