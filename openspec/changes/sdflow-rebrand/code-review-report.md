# code-review 报告 — sdflow-rebrand

> 2026-07-03 · impl-review 编排器（每次全跑·独立冷·强制主审，经运行 checkout 旧名版本执行——D4 设计内）
> diff base `70b5c0a` → `296c65f`（20 commits）· 第零步 resolver 真实调用 `source=local-pin`

## 命中范围

- 栈：bash + python + Markdown → 无 domains 领域清单命中，过 CR-01~09 base。
- 镜面：gstack 审计（scope-drift + 完成度）+ CR 清单镜 + 对抗镜×2（升级切换路径 / 断言与测试盲区，均实测复现型）+ 历史镜。
- gstack 审计：**PASS，无 scope-drift**（106 diff 条目全归位），计划 25 项 100% 有实现证据；3 观察项（主 spec 已 sweep→归档勿叠加、单测试文件 rename 检测断裂、MARK_TOKENS 计划偏差已授权）。
- 历史镜：无推翻近期决定；反复改动均为递进/校准非摇摆。
- 升级切换对抗镜：**四方向全部实测未爆**——合并后首次 /sdflow-upgrade（18 旧链精确清零 + canonical 接管提示）、真·老式消费仓 update（token 迁移零重复区块、告警堆叠无错乱）、dangling canonical 窗口（resolver exit 2 显式降级）、Codex sibling 同级共装不变量。

## Findings（置信 ≥80，已裁决）

| # | 严重度 | CR | 问题 | 证据 | 置信 | 处置 |
|---|---|---|---|---|---|---|
| 1 | 高→defer | — | `install_into` 对既有软链零所有权校验：同名异物软链被 `ln -snf` 无声覆盖且报 "✓ installed"（与 T18 可见性问题**不同轴**——这是所有权校验缺失） | 盲区镜沙箱复现；测试网确无"同名异物软链"态 | 90 | **defer→T24**（理由：未改动行既有行为；laodao→sdflow 迁移曾依赖该替换语义，加严判据会破坏 dev↔runtime 切换——需专门设计"何为自属目标"，不宜在行为零变化的改名 change 顺手改） |
| 2 | 中 | CR-09 | `OUR_NAMES`（21 名）定义未接线、`ours` 循环变量未用——D5 白名单实际仅 1/21 端到端验证，`OUR_LEGACY_NAMES` 拼错测试不红 | test_setup_sdflow.py:112-131 | 85 | ✅ 已修[impl-review-fix]：全名单参数化三类断言（9 旧名→清 / 12 现存名→链 / 名单外→不动），296c65f |
| 3 | 低中 | CR-09 | `test_version_line_branded` 硬编码 `v0.9.0`——/tag 升版即误红 | 同文件 :121-123 | 85 | ✅ 已修[impl-review-fix]：动态读 VERSION 拼期望 |
| 4 | 中 | — | assert-log 对 `opsx-init:` token 的保留"恰好没被 pattern 撞上"而非显式判定——"零残留"用词与核验范围不完全对等 | 盲区镜第 11 轴分析 | 85 | ✅ 已修[impl-review-fix]：assert-log 追加「marker token 显式判定」节（刻意设计 Task 0.2，改 token 会使存量区块失配；现状计数 13 处留档） |

## 已裁掉 / 备注（反静默压制，可审计）

- **X1** 盲区镜"pattern 网非系统枚举"的元批评 → 批注不立项：网的构成（RENAME-MAP 9 名 + laodao 轴 + 本次 token 显式判定）已覆盖全部已知品牌字面量族；"穷举旧仓所有字面量"无封闭定义，边际收益归 `workflow-metrics-loop` 类机制债，本 change 不再加轴。
- **X2** gstack LOW"test_setup_sdflow.py rename 检测断裂" → 忽略：整文件重写致相似度 <50%，纯 git 溯源观感，无功能影响。
- **X3** `ld-update`/laodao 旧仓 `update` skill 并存 → 非残留：adr/0007 双品牌过渡决策显式豁免。
- **过程事故披露**（升级切换镜自报）：一次沙箱漏重定向 HOME，真实 `~/.claude/hooks/change-review-stub.py` 被旧版覆盖约 1 分钟，已按仓内源逐字节恢复（该 hook 旧名仅在注释、功能靠正则；恢复版即合并后应有内容；settings.json 未受影响）。无残留。
- **<80 滤除**：无（各镜证伪失败方向均如实申报：语境挪移未发生、测试账目 224→233 逐 commit 复算吻合、断言零弱化、大小写/下划线变体零命中、Codex sibling 未爆）。

## 修复 / defer 台账

- 自动修 **3 项** `[impl-review-fix]`（296c65f：测试版本解耦 / OUR_NAMES 全名单接线 / token 显式判定行）；测试 233 passed 无 warning。
- 自动裁 **1 项**（记理由）：Finding 1 defer 而非当场修——见表内理由，判据设计候选已写入 T24。
- defer **1 项** → **T24**（install_into 软链所有权校验设计）；另 T21-T24 均已挂本 change，随 opsx-done sweep 入批次。
- **转交 opsx-done 两条**：①archive delta 对码时主 spec 已被本分支 sweep，勿重复叠加（gstack 审计 INFO#1）；②hand-off 按 tasks 5.5 四项 + 真实激活步骤（merge+push 后新会话 /sdflow-upgrade）。

## 结论

☑ **建议进 `/opsx-done`**（verify → hand-off → archive → commit → merge）。
☑ defer 残差已入 todolist（T21–T24，hand-off 将引用批次）；无 buglist 级残留。
