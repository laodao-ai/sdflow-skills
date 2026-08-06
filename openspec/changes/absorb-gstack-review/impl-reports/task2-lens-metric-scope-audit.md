# Task 2: lens-metric 折叠源改认 scope-audit 并给出旧版修法指引

## 做了什么

三处改动，均在 `sdflow-init/assets/workflow/` 权威源（未触碰仓根 `openspec/workflow/` 部署副本，理由见「Concerns」）：

1. **`lens-metric-contract.md`**
   - `## 机读折叠` fence 块（`lens-metric-fold`）：`gstack-adv: broad` 行替换为 `scope-audit: broad`（不共存，纯替换）。
   - `## 折叠表（canonical 投影）` 散文行同步改述：`autoplan(CEO/Eng/DX/design)+gstack-adv→broad` → `...+scope-audit→broad`；并按本文档既有惯例（如 `add-codex-host-support` 的追加式变更注记）追加一条 `〔absorb-gstack-review：...〕` 括号注记，说明本次替换的来龙去脉。

2. **`tools/lens_metric_emit.py`**
   - `fold_hit()` 内「未知 raw 镜名」fail-closed 分支（原 line 102）追加可操作指引：`（若本仓 openspec/workflow/ 为旧版，请先跑 sdflow-init update）`。

3. **`tools/tests/test_lens_metric_emit.py`**
   - 新增 4 条测试（TDD：先跑基线 56 绿 → 新测试先红 1 条 → 实现 → 复跑全绿 60）：
     - `test_fold_hit_scope_audit_maps_to_broad`：`scope-audit` 经 `fold_hit` 折叠出 `("broad", host, host, "—")`。
     - `test_fold_hit_gstack_adv_no_longer_recognized`：`gstack-adv` 不在 fold_map 内、`fold_hit` 对它 fail-closed（回归锁「替换非新增」）。
     - `test_fold_hit_unknown_raw_error_mentions_update_hint`：未知 raw 名报错文案含 `sdflow-init update` 与 `openspec/workflow/` 两个子串。
     - `test_reduce_scope_audit_raw_folds_to_broad_anchor`：端到端走 `reduce()`，`raw="scope-audit"` 的 finding 归约后落在 roster 的 `lens="broad"` 行（`findings="1"` `采纳="1"` `独立="1"` `sev="致0/高0/中1/低0"`），验证下游 `lens="broad"` 锚行接口不变。

## 验收标准逐条核验

| # | 验收标准 | 证据 |
|---|---|---|
| 1 | 折叠机读块含 `scope-audit: broad` 行，且不再含 `gstack-adv` 行 | `grep -n "gstack-adv\|scope-audit" sdflow-init/assets/workflow/lens-metric-contract.md` → fence 块内仅剩 `66:scope-audit: broad`，无 `gstack-adv:` 行 |
| 2 | 契约文档中描述折叠关系的散文与机读块一致（无 `gstack-adv` 残留） | `## 折叠表（canonical 投影）` 散文行已改 `+scope-audit→broad`；文档内剩余 `gstack-adv` 字样仅出现在新追加的历史注记括号内（`〔absorb-gstack-review：...〕`），是既有惯例的变更记录，非当前折叠关系描述——与 `add-codex-host-support` 一处保留 `claude-fallback` 的方式同构 |
| 3 | 原始镜名 `scope-audit` 经折叠后产出 `lens="broad"` 的锚行 | `test_reduce_scope_audit_raw_folds_to_broad_anchor`（新增，绿） |
| 4 | emitter 遇未知原始镜名时报错文案含「若本仓 `openspec/workflow/` 为旧版，请先跑 `sdflow-init update`」（有测试断言） | `test_fold_hit_unknown_raw_error_mentions_update_hint`（新增，绿）；`lens_metric_emit.py` line 99-105 |
| 5 | `test_lens_metric_emit.py` 既有 fold 用例全绿 | 全文件 60/60 绿（56 原有 + 4 新增），见下方命令输出 |

## 跑过的测试

```
/usr/bin/python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -q
............................................................             [100%]
60 passed in 0.34s
```

TDD 红→绿证据：改 emitter 前单独跑新 3 条 `-k "scope_audit or gstack_adv_no_longer or update_hint"` → `1 failed, 2 passed`（`test_fold_hit_unknown_raw_error_mentions_update_hint` 断言 `"sdflow-init update" in ...` 失败，因原报错文案不含该串）；改完 → 3 条全绿。

按 TDD 契约（`Blocked-by: none`）本票只跑单元层，未跑集成/e2e。另额外跑了一次全量 `sdflow-init/ hack/` 套件核对无意外回归（非本票要求，超出 TDD 契约范围但作为安全网执行）：

```
/usr/bin/python3 -m pytest sdflow-init/ hack/ -q
（全绿，含数个 skip，exit 0）
```

## Concerns

- **仓根 `openspec/workflow/lens-metric-contract.md` 与 `openspec/workflow/tools/lens_metric_emit.py` 两份部署副本未同步改动**——按票面提示先查证：`test_lens_metric_emit.py` 的 `CONTRACT`/`SCRIPT` 常量固定指向 `sdflow-init/assets/workflow/`（`TOOLS = Path(__file__).resolve().parent.parent`，即测试文件所在目录的上两级，恒为 assets 侧），不消费仓根副本，故未同步。此外本 change 自身 `tasks.md` 6.3 已把「仓根 `openspec/workflow/` 孤儿副本清理（lens-metric-contract.md / WORKFLOW-GUIDE.md，非 pin 死件、grep 假阳来源）」列为 spec-review-amendment 认领的 defer 项（issues 池 todo），确认这两份副本本就是待清理的孤儿、非当前维护对象，不属本票范围。
- 未触碰 `anchor_lint.py` 的 `mirrors-unknown-token` 报错文案与 SKILL「skew 探测」段的新信号——tasks.md 2.5 把这两项与本票 emitter 指引并列，但本票 brief（`task2-brief.md`）的 5 条验收标准只覆盖 emitter 一处，判断这两项由其他票（SKILL.md/anchor_lint 相关）承接，未越界代做。
