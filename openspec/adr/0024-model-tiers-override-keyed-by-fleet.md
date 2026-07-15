# 0024 · model-tiers 消费仓覆盖按机队分键：档位是相对机队的相对词，覆盖没理由是唯一 host-agnostic 的一层

> 状态：**Proposed**（2026-07-15，grill `add-codex-host-support` 收敛时立）——待该 change ship 后升 Accepted。
> 关联：`openspec/changes/add-codex-host-support/design.md`（G4）· `adr/0006`(c)（机队锚定）· CONTEXT「机队锚定」「宿主」· `model-tiers.md`（覆盖段所在）。

## Context

消费仓可在 `openspec/config.yaml` 的 `model-tiers` 段**覆盖**档位映射（per-repo）。存量格式是**扁平**的——`strong/mid/light` 各一个模型名，因为写它时**只有 Claude 一个机队**。

`add-codex-host-support` 引入第二个机队（Codex）后，宿主决定用哪个机队（Claude Code 宿主 → Claude 机队；Codex 宿主 → Codex 机队）。此时扁平覆盖出问题：一份写着 `strong: opus` 的存量覆盖，到了 **Codex 宿主**下会被拿去喂一个 codex `spawn_agent`——**`opus` 不是 Codex 机队的模型，会炸。**

grill（2026-07-15）锚目标态判定：这不是「现在还没有仓写过 Codex 覆盖所以不用管」（基准 2 禁此），而是**目标态下 Codex 宿主 + 存量扁平覆盖的必然错配**。

## Decision

**覆盖也按机队分键**，与档位「相对机队」的本质对齐：

```yaml
model-tiers:
  claude: { strong: …, mid: …, light: … }
  codex:  { strong: …, mid: …, light: … }
```

1. **读取**：`resolve-models.sh` 按当前宿主所属机队读对应段；无当前机队的覆盖段 ⇒ 回落 `model-tiers.md` 的机队缺省，MUST NOT 报错。
2. **向后兼容**：存量**扁平**格式（`model-tiers.strong: …`）读作 **Claude 机队**的覆盖（历史事实：所有存量覆盖都写于 Claude-only 时期）。与锚行 v1→v2 兼容读同构。
3. **错配防呆**：分键后不再可能把 `opus` 塞进 codex 段——机队与模型名的归属由 schema 结构保证，非运行时判断。

## 为何这样（判据）

- **档位本就是相对机队的相对词**（`adr/0006(c)`）——「强档」在 Claude 机队 = opus、在 Codex 机队 = sol。缺省已按机队分列（本 change task 8.1），覆盖是缺省的同构层，**没有理由是唯一 host-agnostic 的写法**。
- **扁平→Claude 的兼容读是事实、非假设**：存量覆盖全部写于只有 Claude 的时期，读作 Claude 机队覆盖是还原它当时的真实意图，不是猜。

## 代价（如实记）

- 消费仓 config schema 变（扁平 → 分键）——但**扁平仍合法**（兼容读作 Claude 段），无强制迁移；仓在上 Codex 宿主前补 `codex:` 段即可。
- `config_lint` / `config.template.yaml` 需同步认识分键格式（本 change scope 内）。

## 被否方案

- **`resolve-models` 忽略「模型名不属当前机队」的覆盖 + fail-loud 回落 + 告警**：较省 schema 改动，但把「错配」留到**运行时**才发现（且「模型名属不属某机队」本身需要一张机队→模型名的表，又是一个漂移面）。分键在 schema 层结构性杜绝错配，优于运行时探测。
- **维持扁平、host-agnostic**：目标态下 Codex 宿主必错配（见 Context），基准 2 禁以「现在没仓写 Codex 覆盖」松绑。
