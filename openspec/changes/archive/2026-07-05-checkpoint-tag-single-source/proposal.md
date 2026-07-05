<!-- [spec-review-amendment] Q1=B：原「doc 正则抽取 + SKILL.md 瘦身」方案被四路冷审实质证伪（见 spec-review-report.md），
     缩到可靠内核：纯测试新增焊 producer→parser + 负例矩阵，撤销所有 doc/skill 改动。 -->

## Why

checkpoint 任务标签 `checkpoint(<change>:task<N>-<slug>)` 是 `/sdflow-ship` gate 完成判据主锚。它由 `checkpoint-commit.sh`（**producer**：把参数包成 `checkpoint($step): …`）铸造、由 `ship_gate.py` 的 `TAG_RE`（**parser**）解析。这条 **producer→parser** 链**当前无任何测试守卫**：若脚本包裹格式或 `TAG_RE` 任一漂移，标签会被 gate 静默不计入完成集（假✅/假阴家族），无人发现。ship-gate-hardening-2 曾因文案多处独立维护漏改一处（G1）。本 change 加**机械绑定测试**焊死 producer 真产的 subject 能被 parser 认，并给 `TAG_RE` 补负例矩阵封住"放松即静默保绿"的洞。

> 注：原设想「让 workflow.md/SKILL.md 文案彼此 DRY + 瘦身」经 spec-review 证伪为循环/自毁（doc 是占位符非真标签、瘦身反造读依赖）。真正 sound 且高价值的是 producer→parser 这条**真实生产链**的绑定——本 change 收敛到此。

## What Changes

- **新增 producer→parser 集成测试**（`sdflow-ship/tests/`）：在临时 git repo 中调用**真实** `sdflow-init/assets/hack/checkpoint-commit.sh demo:task1-slug "..."`，读回最后一个 commit 的 subject，断言 `ship_gate.py` 的 `TAG_RE.match` 成功且捕获组 == `("demo","1")`；裸格式 `checkpoint-commit.sh task1-slug` 同理断言 match 且命名空间组为 `None`。这焊的是**脚本真铸造的字符串 ↔ gate 真解析的正则**两站，比对文档占位符更本质。
- **新增 `TAG_RE` 负例矩阵**（`sdflow-ship/tests/`）：断言一组 **MUST NOT match** 的 subject（如 `checkpoint(task1slug)` 无尾 dash、`checkpoint(DEMO:task1-)` 大写命名空间、`checkpoint(task-1-)` 号位非法），封住"`TAG_RE` 被放松后 happy 例仍绿"的漏报（spec-review H3 实证过三种放松均静默保绿）。
- **零 doc/skill 改动**：`workflow.md` / `SKILL.md` / `ship_gate.py` **均不改**（撤销原方案的瘦身与自我声明）。既有 `test_workflow_authority.py` 的文档子串断言保留不动，作 doc↔doc 侧弱守卫。

## Capabilities

### New Capabilities
<!-- 无新能力 -->

### Modified Capabilities
- `spec-workflow`: 新增需求——checkpoint 标签的 **producer→parser 链 MUST 有机械绑定测试**（脚本真产 subject 能被 `TAG_RE` 认），且 `TAG_RE` MUST 有负例矩阵防"放松即静默保绿"。

## Impact

- **测试**：`sdflow-ship/tests/` 新增（producer↔parser 集成 + TAG_RE 负例矩阵）；`import TAG_RE` 需自注 sys.path（现测试基建无，见 tasks）。
- **代码/文档**：`ship_gate.py`、`workflow.md`、`SKILL.md` **不改**（`TAG_RE` / `checkpoint-commit.sh` 作被测锚点被引用）。
- **无运行时行为变更**：纯回归防护网。
- **部署**：仅动 `sdflow-ship/tests/` → 开发 checkout 跑 `pytest` 即可；无 `assets/` 权威源改动，无需 `sdflow-init update`。
- **scope 外**：deferred T33/T35（新鲜度越 committed 边界）；doc↔doc 文案 DRY（证伪为不值得机械化，保持现状弱守卫）。
