# 设计：sdflow-rebrand

> 决策真相源 = [proposal.md](./proposal.md)（explore 2026-07-03 拍板：全量 sdflow- 前缀 + 三保留 + 去后缀 + sdflow-code-review）+ 待落 `adr/0007`（tasks 5.1，记方案对比与否决项）。术语见 [CONTEXT.md](../../CONTEXT.md)（反静默守卫 / 机队锚定）。

## 一、依赖与前置

- 依赖 `minimize-repo-footprint`（已归档）：规则全局解析就位 → 改名传播 = 权威源一次 + 消费仓 `update` 重注入；运行 checkout 已迁 `~/.skills/sdflow-skills`（改名与品牌收拢的物理前提）。
- 与 `opsx-ship-orchestrator` 的顺序关系：本 change 先行——opsx-ship materialize 时直接用新名（避免它刚写完引用又要改）。

## 二、命中触发（TG）

| TG | 命中点 | 激活 |
|---|---|---|
| **TG-14** | 改名波及安装器/部署/脚本组件 | 引用传播图（§三）+ 组件清单（§六） |
| **TG-20** | 消费仓 / 双 agent / laodao 旧仓 | proposal 利益相关方 |
| **TG-23** | 命名方案 ≥2（已拍板） | `adr/0007`（tasks 落，含 plugin 方案否决） |
| **TG-21** | VERSION 起始号 / marker 兼容窗口 | §五 D6/D3 直接裁定（低风险） |

## 三、改名映射与引用传播（组件/依赖图，TG-14）

```
  RENAME-MAP（9 改 3 留，唯一数据源，全部任务按此表驱动）
  ┌──────────────────────┬────────────────────┐
  │ opsx-project-init    │ sdflow-init        │
  │ opsx-done            │ sdflow-done        │
  │ opsx-maintain        │ sdflow-maintain    │
  │ opsx-roadmap-planner │ sdflow-roadmap     │
  │ spec-review          │ sdflow-spec-review │
  │ impl-review          │ sdflow-code-review │
  │ buglist-recorder     │ sdflow-buglist     │
  │ todolist-recorder    │ sdflow-todolist    │
  │ issues-recorder      │ sdflow-issues      │
  ├──────────────────────┴────────────────────┤
  │ 保留：embedded-test-sop / openspec-upgrade │
  │      / sdflow-upgrade                      │
  └────────────────────────────────────────────┘

  引用传播（改名要追的功能性边；文档性引用【白名单】不追）
                     ┌─ ① assets/workflow/workflow.md 步骤表 prompt（/sdflow-spec-review…）
  9 个目录 git mv ───┼─ ② assets/snippets/{claude,index}-section.md（配套 skill 表+安装句）
       │             ├─ ③ sibling 硬编码：issues.py:64-65（目录名 join）+ sdflow-done SKILL §2.1
       │             │    固定路径 + 各 recorder tests 中的路径引用
       │             ├─ ④ 12 个 SKILL.md 互相点名 + description 触发词（§五 D2）
       │             └─ ⑤ setup.sh/init.py 提示文案 + README 列表 + CLAUDE.md 正文
       ▼
  setup.sh 重跑：新名建链（install_into 自动拾取新目录）
                旧名链 = 自属 dangling → cleanup_orphans 收走（跨改名场景，测试锚定）
  消费仓：sdflow-init update → 托管区块重注入新名
  【白名单，不改】adr/ · ROADMAP 历史行 · CONTEXT 术语史 · changes/archive/ · .superpowers/
```

## 四、决策

- **D1 映射表驱动 + 白名单反向断言**〔adr/0006 机械活确定性〕：改名与文本 sweep 全部按 §三 RENAME-MAP 执行（tasks 写死确切命令 = 等效脚本化，可复核可重放）；收尾验证用**反向法**——全仓 grep 每个旧名，命中文件不在白名单即 FAIL（防"改哪些文件靠记忆"的遗漏模式，比正向清单可靠）。
- **D2 触发等价表**：9 个改名 skill 的 description 重写产出一份 `trigger-map.md`（随 change 留档）：每行 = 旧触发短语集 → 新 description 中的对应短语 + slash 新名。**约束：原触发场景语句全保留**（如"记一下这个 bug"仍触发 sdflow-buglist），只换 slash 名、荡涤旧名指称；等价表即评审面（spec-review 逐行核对）。
- **D3 marker 永久兼容**：新写入 `.sdflow-skills`；`.laodao-skills` **永久**识别为自属（一行判断成本换绝不误伤存量 Windows copy；不设兼容窗口——OQ2 裁定）。
- **D4 sibling 机制不变、只换字面**：issues.py 的"按脚本自身位置上溯 SKILLS_ROOT 再 join 目录名"机制保留，仅 :64-65 两个目录名字面换新（`sdflow-buglist`/`sdflow-todolist`）；sdflow-done SKILL §2.1 固定路径同步。**不借机抽象**（如把目录名做成 env/config——YAGNI，改名不是重构窗口）。
- **D5 git mv 保历史**：9 目录一律 `git mv`（rename 检测保 blame 连续性）；文档性引用白名单不改（历史记录原则，同 proposal Non-Goals）。
- **D6 VERSION = `0.9.0`**（OQ1 裁定）：rebrand 后基线，1.0 留给 opsx-ship + Phase C 齐后。setup.sh 输出 `sdflow-skills v0.9.0`。

## 五、风险 → 缓解

- [断言遗漏：某功能性文件漏 sweep] → D1 反向法（白名单外任何旧名命中即 FAIL），且断言进 tasks 为独立验收步。
- [触发精度回退：description 重写丢触发场景] → D2 等价表逐行对照 + 设计门人审 + 收尾抽查 3 条真实触发语句。
- [消费仓托管区块过时引用旧名] → 旧链已被孤儿清理收走 → 失灵是**响的**（skill not found）而非静默错版本；`sdflow-init update` 重注入即愈，提示文案写明。
- [本会话/运行中 agent 的 skill 列表 stale] → 改名生效于 setup 重跑 + 新会话；运维注意写进 hand-off（本 session 后半段勿再调旧名）。
- [Codex 侧发现延迟] → setup.sh 同轮覆盖 `~/.codex/skills`，与 Claude 侧同步；收尾双侧 readlink 验证。

## 六、组件清单（TG-14）

| 组件 | 动作 |
|---|---|
| 9 个 skill 目录 | `git mv` 按 RENAME-MAP |
| 12 个 SKILL.md | 互引换名；9 个 description 重写（D2 等价表） |
| `issues.py:64-65` + recorder/issues tests | sibling 目录名字面换新（D4）+ 路径引用修正 |
| `setup.sh` | 品牌输出 `sdflow-skills v$VERSION`；marker 写 `.sdflow-skills`、识别含 `.laodao-skills`（D3）；孤儿清理跨改名测试锚定 |
| `VERSION`（新建） | `0.9.0`（D6） |
| `assets/workflow/workflow.md` + `assets/snippets/×2` | 步骤表 prompt / 托管区块表 / 安装句换名 |
| `opsx-project-init/scripts/init.py`（→ sdflow-init） | 尾句提示"安装配套 skill"路径与名、测试内路径 |
| `README.md` / `CLAUDE.md` 正文 / `openspec/INDEX.md`（如涉及） | 列表与叙述换名（托管区块经 update --dev 重注入） |
| `openspec/ROADMAP.md` | `extract-sdflow-repo` 行更名 `sdflow-rebrand` + supersede 注记 |
| `adr/0007`（新建） | 命名方案决策记录（含 plugin 否决） |

## 七、迁移顺序与回滚

```
  ① git mv ×9（一次提交，保 rename 检测）
  ② 文本 sweep（RENAME-MAP × 功能性引用面①-⑤）+ description 重写（D2 等价表同产出）
  ③ 品牌三件（setup.sh 输出/VERSION/marker 兼容）
  ④ 测试修正 + 新增（孤儿清理跨改名 / marker 兼容）→ 全量 pytest
  ⑤ 白名单反向断言（D1）
  ⑥ 本机激活：setup.sh 重跑 → 双侧 readlink 新名、旧链清零（真实输出留档）
  ⑦ update --dev 同步 instance + 文档收尾（adr/0007 / ROADMAP / README）
  回滚 = git revert 改名提交 + setup.sh 重跑（链随目录名自动还原；无数据迁移，纯可逆）
```

## Compliance

无 DB/外部服务（D-2/TG-24 N/A）；孤儿清理仅收自属链、marker 兼容防误伤（"绝不动非自属产物"红线）；行为零变化承诺（proposal Non-Goals）——测试套件全量通过即其锚点。
