## Context

`add-sdflow-spec` 归档后，T233–T238、T240–T242 留下源仓行为与叙述不一致。最关键的两处是：FF-0 把 session `cwd` 当成命令实际仓；`SKILL.md` 把常驻流程、未启用外派和故障百科一并注入。

## Goals / Non-Goals

**Goals:**

- 让 FF-0 只在可证明作用仓就是 payload 仓时执行三分支判定，并使未判定可见但不自动授权。
- 将 `sdflow-spec` 的常驻执行契约压到 18,000 Unicode 字符以内，保留按需资料的确定加载路径。
- 订正 Codex、终审追溯和 A/B grill 信号的诚实边界，并关闭已完成的归档台账。

**Non-Goals:**

- 不做 T239 的下游 rollout，不重启外派模式，不解析 shell 语法。

## Decisions

### D1：FF-0 采用“保守识别 + 无决策审计”

[spec-review-amendment] 只有整条命令完整匹配一条直接 literal 创建调用（`openspec new change <合法字面量>` 或 `openspec change new <合法字面量>`，保留既有空白、单双引号与 `--json` 变体）时，才把 payload `cwd` 作为判定仓并进入原三分支。命令串含创建字样但不是该有限 grammar 的单条直接调用——包括 `cd`/`pushd`/`env -C`/shell wrapper、复合运算符、换行、前后散文或动态名——统一输出仅含 `hookEventName` 与 `additionalContext` 的 JSON，不设置 `permissionDecision`。既有“多处可识别创建调用必须拆开”的 deny 在此 cwd 判定前保留。

[spec-review-amendment] 未判定 context 使用有限原因码 `cwd-ambiguous` 或 `change-name-unparseable` 加人类可读说明。这避免把 `allow` 当作日志而跳过宿主权限，也不靠“危险结构全覆盖”的负向黑名单假装证明无界 shell；实际仓语义继续由 shell 和 review 负责。

```text
命令含创建字样？
├── 否 → silent pass
└── 是
    ├── 多处有界创建调用/名字不一致 → 既有 stacking deny
    ├── 完整匹配单条直接 literal 调用 → payload cwd 上执行 FF-0 三分支
    │   ├── protected → deny
    │   ├── feat/{same-change} → pass
    │   └── other feature → fresh ack ? consume+pass : deny
    └── 其余形态 → additionalContext(reason_code)，无 permissionDecision
```

### D2：入口薄化但不稀释执行契约

[spec-review-amendment] `SKILL.md` 保留四条通则、frontmatter、Phase 0/A/B/C、C.1 四判、终审、`openspec validate --strict`、`sdflow-spec-grill`/`sdflow-spec-generate` 两个 checkpoint、出口三步，以及“何时读哪个 reference”的条件与相对路径。未启用的外派协议、详细降级诊断和演进依据移入三个 reference。新增测试以 Python `len()` 验证入口不超过 18,000 Unicode 字符，并以 resident-contract token map 逐项锚定上述语义；只保留空标题或无加载条件的链接不得通过。

### D3：宿主和追溯按证据边界改写

[spec-review-amendment] Codex 没有本 session 可调用的 Skill 执行面，因而只记录“用户显式触发被接受”，不把接口缺席误写成模型调用被拒。终审以整个 change 目录为追溯边界，`decision-memo.md` 是被砍候选和理由的合法唯一载体。本 change 只订正 T132 未来 gate 的 A/B 输入契约与台账描述，不实现或关闭 T132：A 需要身份/hash/必填节有效的 `decision-memo.md` 加 `checkpoint(sdflow-spec-grill)`；B 需要既有 `checkpoint(grill)` 或未来 gate 明确认可的 `sdflow:grill-done` 锚。

## Components

| 组件 | 职责 | 技术/部署 |
|---|---|---|
| [spec-review-amendment] FF-0 hook | 有限识别、三分支 deny/pass、undecided context | Python；canonical 在 `sdflow-init/assets/hooks/`，由 `sdflow-init update --dev` 安装到全局 hook |
| [spec-review-amendment] `sdflow-spec` 入口 | 常驻三相位执行契约与按需 reference 路由 | Markdown skill；`setup.sh` 铺 Claude/Codex skill |
| [spec-review-amendment] versioned references | 承载未启用外派、详细诊断、演进依据 | 仓内 Markdown，随 skill symlink/copy 分发 |
| [spec-review-amendment] contract tests | 守行为、resident tokens、体量、canonical/台账一致性 | pytest，focused + full suite |
| [spec-review-amendment] issue ledger | 逐票终态与证据 | `openspec/issues/todolist/`，T132/T239 保持后续 |

## Failure Modes and Observability

| 场景 | 检测 | 处理 | 可见性/测试 |
|---|---|---|---|
| [spec-review-amendment] 直接 literal 调用 | 完整 grammar 命中 | 原三分支 | deny reason 或 silent pass；覆盖三分支/ack 回归 |
| [spec-review-amendment] 作用仓不可信 | 命中创建字样但非直接 grammar | fail-open，不做 allow/deny | `additionalContext` 含 `cwd-ambiguous`；覆盖 `cd`、`pushd`、`env -C`、wrapper、compound、decoy |
| [spec-review-amendment] change 名动态 | 无法读出唯一合法 literal | fail-open，不展开 shell | `additionalContext` 含 `change-name-unparseable`；覆盖变量、命令替换、glob |
| [spec-review-amendment] 多处创建调用 | 有界 occurrence/name 计数冲突 | 保留 stacking deny | 既有多调用回归测试 |
| [spec-review-amendment] 全局安装未刷新 | source 与 hook/skill 落点不一致或 setup 报相关 skipped | 验收失败，重跑对应安装命令 | source→installed 字节/symlink 与 settings 注册断言 |

## Risks / Trade-offs

- [spec-review-amendment] [复合/包装调用未被强制拦截] → 正向 allowlist 之外统一注入稳定未判定原因；不假装知道实际仓。
- [spec-review-amendment] [reference 漂移] → 测试检查 resident-contract token map、入口加载条件、相对路径与文件存在；按需资料随仓版本化。
- [Codex 宿主接口变更] → 文案不作永久否定；后续出现可调用接口时补正反实测。

## Migration Plan

1. 在 canonical 源仓修改 hook、skill、references、workflow/specs 与测试。
2. [spec-review-amendment] 运行受影响测试与全量 pytest；运行 `python3 sdflow-init/scripts/init.py update --root . --dev` 刷新 dogfood workflow 与全局 hook，再运行 `bash setup.sh` 刷新 skills/global bundle。逐项比对 canonical hook 与 `~/.claude/hooks/ff0-branch-guard.py`、settings 注册，以及 Claude/Codex skill 的 symlink target（Windows 则比内容/hash）；相关 `skipped` 或不一致均判验收失败。
3. 本 change 不向下游执行 update；T239 保持为独立 rollout 待办。
4. [spec-review-amendment] 回滚时还原同一提交；先以回滚后的 `init.py update --root . --dev` 刷新 hook/workflow，再以回滚后的 `setup.sh` 刷新 skills/global bundle。

## Open Questions

无。用户已确认薄入口 + reference 与 18,000 Unicode 字符门。

## Compliance

不新增外部服务、持久化数据或凭据处理；hook 只处理本机 PreToolUse payload。
