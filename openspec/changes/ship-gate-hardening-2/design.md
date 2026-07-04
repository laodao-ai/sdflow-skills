# design — ship-gate-hardening-2

## Context

`ship_gate.py` 的实现完成判据（`decide()` 的 step 6/7 段）当前：

- `TAG_RE = re.compile(r"checkpoint\(task(\d+)-")`：只按 `checkpoint(task<N>-` 前缀提任务号，**无 change 归属**。
- `done_task_ids(root, sha)`：窗口 `[plan_first_sha, HEAD]` 闭区间内收所有 `checkpoint(task<N>-` 号（B1 已修）。
- `plan_task_ids` + `done_in_plan = done & plan_ids`（B4 集合归属）已把**计划外号**过滤掉——但若污染号恰好∈ 本 change plan_ids（同号任务），集合归属挡不住。
- `checkboxes_all(plan)`：全局判「无任何 `- [ ]`」，True 即辅通道放行**所有** plan task，不分段。

窗口下界 `plan_first_sha` 对跨 change 污染只做**部分**隔离：两 change 若在同一分支交错、plan 与 task 提交落进重叠窗口，同号 task 仍互相计入 → 假齐 → 假✅。checkpoint 契约由 `checkpoint-commit.sh`（producer，逐字插值 `<step>`）+ `sdflow-ship` 派发 args（规定 step=`task<N>-<slug>`）+ gate（consumer 解析）三方共识——属**版本化契约套件**〔TG-25〕。

**约束**：① gate 只读零副作用不变；② 假✅ 是头号失效模式，任何取舍向**假阴（多一次 CONTINUE_IMPL）安全、假阳（假 SHIPPED/RUN_CODE_REVIEW）禁止**倾斜；③ `checkpoint-commit.sh` 焊死单行 `-m` subject（禁 `\` 续行/heredoc）——改契约优先不动 producer 脚本；④ 向后兼容旧无命名空间标签为一等约束（proposal A1）。

## Goals / Non-Goals

**Goals：**
- T32：完成判据按 change 归属隔离任务号，新格式 change 免疫跨 change 同号污染。
- T32：旧无命名空间 `checkpoint(task<N>-)` 标签读取语义保留、不崩溃。
- T34：复选框辅通道按 `### Task <n>:` 分段绑定，一个全局 `[x]` 不放行未各自勾选的其它 task。
- ship-gate-hardening 既有 B1/B2/B3/B4 语义**逐字不变**（回归全绿）。

**Non-Goals：**
- T33 工作树 dirty 新鲜度（与盘面即状态张力，需先单独拍板——**不在本次范围**）。
- checkpoint 契约以外的 gate 判定（D3/B2/档位）。
- 彻底杜绝「两个**旧格式**change 同窗口交错」的历史残留假✅（见 Risks，记已知不覆盖）。

## Decisions

### ADR-1〔TG-23〕：change 命名空间的编码格式 — 步名内嵌 `<change>:task<N>`

**选项**：

| 方案 | 编码 | producer 改动 | 可见性 | A3 风险 |
|------|------|--------------|--------|---------|
| **A 步名内嵌**（选） | `checkpoint(<change>:task<N>-<slug>): desc` | **无**（`checkpoint-commit.sh` 逐字插值 step；命名空间由 sdflow-ship 派发 args 注入） | git log `%s` 直接可见 | change 名含 `:`/`)` 会破解析——但 openspec change 名恒为 kebab-case slug（无 `:`/`)`），天然满足；gate 额外校验 |
| B git trailer | `checkpoint(task<N>-): desc` + `\n\nChange: <c>` | **改脚本**（加第二 `-m`）+ 所有调用点 | `%s` 不含，需 `%(trailers)` | 低，但牵连 producer 脚本 + 焊死约束复杂化 |
| C 旁挂字段文件 | sidecar 记 change↔task | 新增写盘 | 不在 git log | 破坏「盘面即 git 历史」单一真相源 |

**决策：A**。理由：契约爆炸面最小（producer 脚本**零改**，命名空间落在 `sdflow-ship` 派发 args 这一既有约定点）；git log 直接可读可审计；change 名的 kebab-case 约束（openspec 强制）使 `:` 分隔天然无歧义。gate 侧 `TAG_RE` 扩展为可选捕获命名空间组，并对捕获到的 slug 校验字符集。

**新 `TAG_RE`（可选命名空间组）**：`checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`
- group(1) = 命名空间 slug 或 `None`（裸标签）；group(2) = 任务号。

### ADR-2：向后兼容归属规则 — 命名空间标签严格匹配，裸标签保留窗口语义

**计数规则**（`done_task_ids` 内，逐 subject）：

```
命名匹配 checkpoint(<ns>:task<N>-)  →  仅当 <ns> == 当前 change 才计入 N
裸标签   checkpoint(task<N>-)       →  计入（窗口 [plan_first_sha,HEAD] 语义，= 今日行为，A1 兼容）
```

- **为何裸标签仍计**（A1）：gate 中途升级时，进行中 change 的已产生裸标签不能丢（否则回退到 CONTINUE_IMPL——虽属**安全侧假阴**，但徒增摩擦）；且窗口下界已把裸标签大致框到本 change 时段。
- **为何新格式即免疫**：一旦 plan 派发命名标签，污染 change B 的标签是 `checkpoint(<B>:task<N>-)` → group(1)=B≠当前 → **正确排除**；叠加既有 `done & plan_ids`（B4），残留假✅面塌缩到「两个都用旧裸格式的 change 同窗口交错且撞 plan 号」——历史边角，记已知不覆盖。
- **假阴/假阳倾斜自检**：命名不匹配 → 排除（可能少计 = 假阴安全）；裸标签 → 计入（保今日行为，不新增假阳）。方向合规（约束②）。

### ADR-3：T34 复选框按 Task 分段绑定

`checkboxes_all(plan)`（全局布尔）→ `checkbox_done_ids(plan)`（每 task 号集）：

- 按 `TASK_TITLE_RE`（`^### Task (\d+):`）的匹配位置把 plan 正文切成**段**，每段归属其 task 号。
- 某 task 号 ∈ checkbox_done 当且仅当**其段内**存在复选框且**全部已勾**（段内无 `- [ ]` 且有 `- [x]`）。
- 完成集合并：`done_ids = checkpoint_done_ids ∪ checkbox_done_ids`，再 `done_in_plan = done_ids & plan_ids`（B4 不变）。
- **保留** `plan 未提交且无任何复选框 → UNKNOWN 双通道不可判` 分支（sha 空 ∧ 全 plan 无框）。

### 决策逻辑〔TG-12〕：完成判据数据流（改动点标 ★）

```
plan.superpowers-plan.md
   │  TASK_TITLE_RE → plan_ids {计划号集}
   │  ★T34 分段 → checkbox_done_ids {段内全勾的号}
   ▼
git log [plan_first_sha, HEAD] 闭区间(B1)
   │  逐 subject: startswith("checkpoint(") 且 ★新 TAG_RE
   │     ├─ 命名 <ns>:task<N>  ─ ★ns==change? ─是→ 收 N ; 否→ 弃(假阴安全)
   │     └─ 裸   task<N>        ─ 收 N (A1 窗口语义)
   ▼  = checkpoint_done_ids
done_ids = checkpoint_done_ids ∪ checkbox_done_ids      ★合并
done_in_plan = done_ids & plan_ids                      (B4 不变)
   ▼
plan_ids - done_ids == ∅ ? ─是→ 进 code-review 门
                          └否→ CONTINUE_IMPL(done_tasks=sorted done_in_plan)
```

### 协议套件 scope-check 表〔TG-25〕：改一处契约牵连的一组

| 契约点 | 文件 | 本 change 改动 | 兼容义务 |
|--------|------|---------------|---------|
| **格式产出（producer 约定）** | `sdflow-ship/SKILL.md` RUN_PLAN→writing-plans 派发 args | step `task<N>-<slug>` → `<change>:task<N>-<slug>` | 新 change 起用；旧 change 已产标签不回改 |
| **产出脚本** | `sdflow-init/assets/hack/checkpoint-commit.sh` | **零改**（逐字插值 step，命名空间在调用侧） | — |
| **解析（consumer）** | `sdflow-ship/scripts/ship_gate.py` `TAG_RE`/`done_task_ids` | 可选命名空间组 + 归属规则 + 分段复选框 | 裸标签保留计入（A1） |
| **规范** | `openspec/specs/spec-workflow/spec.md` 完成判据需求 | +命名空间隔离/分段绑定 Scenario | 既有 B1-B4 Scenario 不变 |
| **头注释「已知不覆盖」** | `ship_gate.py` 头部 | +双旧格式同窗残留 + T33 停置 | — |

> **scope-check**：以上 5 点必须同批改齐——漏 SKILL 派发 args = 新格式永不产生；漏头注释 = 残留假✅无声。tasks 逐点建任务，verify 逐点核。

## Risks / Trade-offs

- **[两个旧裸格式 change 同窗口交错且撞 plan 号 → 残留假✅]** → 缓解：新格式 change 全免疫；该场景需两 change 都不用新格式且同分支交错同号——实操罕见（每 change 独立 feature 分支是既定纪律）。记入 `ship_gate.py`「已知不覆盖」，不在本次根治（Non-Goal）。
- **[change 名含非 kebab 字符破坏 `:` 解析]** → 缓解：openspec 强制 change 名 kebab-case；gate `TAG_RE` 命名组限 `[a-z0-9][a-z0-9-]*`，非法即不匹配命名分支（退化为裸/不计，假阴安全），不崩溃。
- **[gate 中途升级致进行中 change 已产裸标签语义变化]** → 缓解：ADR-2 裸标签保留计入 = 今日行为，无回归。
- **[T34 分段解析边界（段内无框 / plan 未提交）]** → 缓解：保留 UNKNOWN 双通道不可判分支；段内无框 = 该 task 仅凭 checkpoint 主锚判，不因分段新增假阳。

## Migration Plan

1. gate 解析先落地（读双格式）→ 再改 `sdflow-ship` 派发 args 产新格式：**读容忍先行**，避免"先产新格式但 gate 还不认"的窗口。
2. 无数据迁移（无持久状态；纯 git 历史读取）。旧标签原地兼容，无需回填。
3. **回滚**：`ship_gate.py` + SKILL + checkpoint 契约均 git 版本化；坏则 `git checkout <prev>` + `setup.sh`（SKILL/脚本走 symlink/拷贝生效）。
4. 部署边界：改 `sdflow-ship`（skill 本体 symlink，pull 即生效）；`checkpoint-commit.sh` 本 change **零改**故无 `~/.sdflow/hack/` 重装窗口。

## Open Questions

- 无阻塞性未决项。ADR-1/2/3 已定；T33 显式停置（Non-Goal，另拍板）。

## 规则/边界合规声明

- **destructive-commands**：不适用（gate 只读、本 change 不引入写操作/删除）。
- **dev/runtime checkout 纪律**：改 `sdflow-ship` skill 本体 + 测试；测试须在开发 checkout 跑 `setup.sh` 后 pytest（skill symlink 即时生效，本 change 不改 `assets/hack/` 脚本故无拷贝窗口）。
- **契约兼容边界**：T32 属契约变更，向后兼容（A1）为一等约束，scope-check 表 5 点同批改齐。
