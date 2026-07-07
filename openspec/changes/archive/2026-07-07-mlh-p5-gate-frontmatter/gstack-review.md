<!-- sdflow:step1-broad-review v1 mode="adapted" -->

# Step1 广审（broad）— mlh-p5-gate-frontmatter

**mode 说明（诚实标注）**：autoplan 的原生流程是 gstack **plan-file** review 体系（restore point / plan-file 编辑 / gstack review-log / CEO·DX 全套仪式 + routing 注入等副作用 preamble），审对象是 gstack plan file；本 change 是 **OpenSpec change 四件套**（无 gstack plan file、无 UI scope、纯机械层脚本迁移）。硬跑全套 gstack 仪式不适配且引入副作用（改 CLAUDE.md routing、写 gstack log）。故执行 autoplan 的**评审方法论核心**——跨模型 codex voice（design-voice + hr-tg voice，经 sdflow 的 outside-voice.sh）+ broad 综合视角由 Step2 领域镜/对抗镜覆盖。因非 autoplan 原生全跑，触发 sdflow-spec-review 的 outside-voice 守卫回落（reason_code=simulated-source 对等：autoplan 未原生产 codex 段）→ 自跑 design-voice + hr-tg voice。

## codex 双声 findings（进合并池，详见 spec-review-report.md 裁决）
- **design-voice（codex，5 条）**：归档双读缺「present-but-invalid 不回退」硬规则 / schema 示例三字段同列冲突 / 手写 YAML 未定义 comment·metadata / live·archive 分流混工作树域·git-tree 域 / proposal 残留 safe_load。
- **hr-tg voice（codex，3 条，TG-04+TG-08 命中）**：anchor_set 熔断 helper 未纳入迁移 / 手写解析器未锚定文件首行 --- / live·归档 frontmatter 读未钉共用同一核心。

## broad 综合视角（CEO/eng/dx 折叠，由多镜覆盖）
- 战略/范围（CEO 面）：迁移根治 B4/B5 门禁假阳，ROI 立论成立；Non-Goals（不迁家族②/不碰 bundle/门禁语义不变）边界清晰（领域镜 + 对抗C 已背书 anchor_lint 不受牵连、归档读范围收敛正确）。
- 架构（eng 面）：核心风险 = 迁移低估了 live inline 读点数量（详见 spec-review-report 簇1），退出码契约未钉死（簇3），已由对抗镜 + 接地镜深挖。
- dx 面（开发者工作流）：三 producer SKILL 模板改动量被当一行活低估（簇8），自指 dogfood 序陷阱（簇10）。
