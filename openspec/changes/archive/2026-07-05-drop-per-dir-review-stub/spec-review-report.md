# spec-review 报告 — drop-per-dir-review-stub（轻设计审）

> **深度裁定**：小范围、纯机械产物移除，**不命中任何领域栈**（config 明写不涉 backend·go / embedded / frontend），
> 唯一有权衡的设计点 = ADR-1（退役 hook 反注册）。据"深度由触发决定"原则跑**轻设计审**：不做多镜 fan-out，
> 由主 session 读码接地 + 人类逐条过 ADR 拍板。以下记录该门的裁定与接地证据。

## 命中范围
- 栈：纯 Python skill 脚本（sdflow-init / sdflow-roadmap）。无领域镜。
- 触发：无 TG-18（非嵌入式）→ RUN_SOP 将 SKIP；无 domains → 无领域清单。

## grill —— 本次跳过（显著呈现，记忆 grill-not-skippable）
- **判定：跳过**。理由：① 产物移除近乎机械；② 唯一设计点 ADR-1 已由用户逐条过目并 `同意`；
  ③ 设计事实已读码接地（见下）。**兜底**：下游 verify（终门）+ sdflow-code-review（每次全跑独立冷主审）。
- 用户在轻量路径下明确接受此跳过；若后续需要仍可补跑 grill 再回设计门。

## 接地证据（主 session 读码，非多镜）
| 断言 | 证据 | 结论 |
|---|---|---|
| init.py hook 安装"只增不减"、无移除路径 | `grep uninstall/remove/pop` on `sdflow-init/scripts/init.py` → 0 命中；`ensure_global_hook` 仅追加 | ✅ 成立 → ADR-1 问题诊断真实 |
| review UI 每目录 stub 与根锚同源、scope 由 pathname 推 | 读 `change-review-stub.py` / `gen_review_stub.py` 头注释（engine.js 从 `window.location.pathname` 推 scope） | ✅ 根锚一份即可导航 → 每目录 stub 冗余 |
| 无 spec 需求专述 hook/stub 行为（除 bundle 部署需求列 hooks） | `grep` spec.md：仅「workflow bundle…」需求枚举含 hooks；spec.md:99 讲根锚 | ✅ delta 只需 MODIFY 该一条 |
| root anchor 保留即能力不回退 | `copy_review_tool()` 铺根 review.html+serve.sh 不动；engine bundle 随 tools/ 不动 | ✅ Non-Goal 成立 |

## 决策登记区
```
[自动决策] D1  轻设计审（无多镜 fan-out）—— 小范围+无领域栈，深度按触发下调；接地由主 session 读码承担
[需拍板→已拍板] Q1  ADR-1 退役 hook 反注册 vs 替代 B/C/D —— 用户选 A（RETIRED_HOOKS 自愈），已 `同意`
[已裁掉] （无）  轻审无 reviewer finding 需裁
```

## 结论
- ✅ 建议进实现（退出 explore 后：手工实现 5 任务 / 或薄 SDD → sdflow-code-review 薄跑 → sdflow-done）。
- 设计事实已接地，ADR-1 获批，spec delta（MODIFIED workflow-bundle 需求 + 2 新 Scenario）validate 通过。

<!-- ship-gate: design-approved -->
