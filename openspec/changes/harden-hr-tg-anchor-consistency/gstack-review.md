<!-- sdflow:step1-broad-review v1 mode="simulated" -->
# 广审（Step1）— harden-hr-tg-anchor-consistency

> **mode="simulated"（诚实降级）**：autoplan 是 gstack **plan-file** 评审管线（期待 `~/.gstack` design doc + plan file），与 OpenSpec change 架构错配，原生跑会去 offer /office-hours 且是无关 detour。据 sdflow-spec-review 降级路径，广审由 fresh 子代理承担（CEO/design/eng/DX 完整性 + scope-drift 视角适配 OpenSpec），非原生 autoplan。侧信道佐证：autoplan SKILL.md 首段即要求 gstack plan file / ~/.gstack design doc（本 change 无此产物）。

## 广审 findings（完整性 / scope 内聚 / 取舍 / DX / 验收）

- **[中] 部署 skew 描述过窄**：bundle（tools，per-repo 手动 `sdflow-init update`）vs skill-local（SKILL.md，全局瞬时 `setup.sh`）双速率；下游消费仓 SKILL 新（传 `--trigger-catalog`）+ tools 旧 → argparse 报错。仍 fail-closed 响亮，但 design Risks 责任边界写窄（只提本仓 dev/runtime，未覆盖下游消费仓）。→ 采纳（design Risks 补澄清）。
- **[低] docs 失真**：`docs/workflow-map.md` + `docs/workflow-skills/{sdflow-spec-review,sdflow-code-review}.md` 写死 anchor_lint 调用串（workflow-map footer 自称 ground truth）；加必需参数后即刻过时，tasks 未覆盖。→ 采纳（tasks 补 docs 同步）。
- **[低] declared 序列化顺序未定**：M2「逐元素一致」未定序（hr_tg_intersect 已 numeric sort，见 test_dedup_and_sorted_numeric）。→ 采纳（并入跨文件一致性守卫，两侧同序）。
- **[低] 新增 TG 类 change 自指评审顺序**：评审"新增 TG"的 change 时，$RULES_ROOT/trigger-catalog 尚无新 TG，`declared="TG-27"` 被 M-new fail-closed。fail-safe（宁挡不误放），代价仅重跑。→ 采纳（design 注一句，不改判据）。
- 完整性 / scope 内聚 / 验收标准：**站得住**（M1–M4+M-new 面治闭环、T137/T139 剥离有据、Success Metrics 可证伪）。

（详细 findings 归入 spec-review-report.md 合并池，本文件仅 Step1 广审留档。）
