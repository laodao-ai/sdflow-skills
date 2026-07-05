# hand-off — workflow-metrics-loop

## ✅ 完成了什么（每条附机验锚点）

评审价值度量回路落地（纯价值度量，成本另立 T29）：

- **锚契约 `lens-metric v1` 权威源**：`sdflow-init/assets/workflow/lens-metric-contract.md`（字段/取值域/site 消歧/sev 定序/enum 升 v2 治理/config 门控/示范锚 fence MUST）。commit `b4b84a1`。
- **只读聚合器**：`sdflow-init/assets/workflow/tools/lens_metric_aggregate.py`——fence-aware **长度感知**嵌套核（挡 4-外层套 3-内层示范锚）、行首独占 parse、分组键含 `runner`、坏文件 try/except 不崩全局、数值非法/负值 flag、无锚显式计数、不写持久态、不跨 import ship_gate。测试 **19 passed**（真哨兵：非行首前缀防裸 in / Σ独立=20·Σfindings=50 真值防退化 / 嵌套 fence 不漏 / 坏编码不崩）。commit `74efb45`。
- **生产者落锚**：`sdflow-code-review/SKILL.md` + `sdflow-spec-review/SKILL.md` Step3 落 lens-metric 锚、voice分桶 prose 清零(活指令=0)、独立导出、自检扩枚举越域、config 门控、spec-review SR-M 拍板最终化(best-effort)。
- **surfacing 防死列**：`sdflow-maintain/SKILL.md` 收尾机械步，`出现轮数≥10` 显著提示——三分支全可达（Task7 fix 漏的"确认修复"主干经 code-review CF-3 补齐）。
- **config 门控**：源仓 `openspec/config.yaml` metrics.enabled=true / 消费仓模版 false；copy_bundle 排除 `tools/tests/` 不铺进下游（init.py + 双向断言 41 passed）。
- **dogfood 首批真锚**：本 change 的 `code-review-report.md` 落了 4 条真 lens-metric 锚（domain/adversarial/history/outside-voice），**codex 独立=2**（CF-1 runner键 + CF-6 测试部署，各 claude 镜全漏）= 独立贡献度量机制的首个活样本。
- verify **PASS**（`verify-report.md`，逐需求对码有锚点）；仓级 pytest 395 passed。

## ⏳ 未完成 / 延后（批次 `workflow-metrics-loop`，见 `openspec/issues/batches.md` + `INDEX.md`）

- **T54**（grill amendment 存活率度量）：口径未定义（amendment 无 ID/无 ground truth 链接）、需自己的 explore、非本 change；与 T29 并列 workflow-metrics-loop 伞下。
- **T55**（聚合器易用性/健壮性观察，code-review X3/X4 defer，低危）：glob 空表 vs archive 不存在无法区分；转义引号 site 值截断产生多余分组行（site 不校验已契约注明）。
- **B5**（pre-existing，**非本 change 引入**）：`test_gate_anchor_scope::test_contract_archived_corpus_anchor_hits` 既存红（main 亦红）——归档报告 ship-gate 锚在 fenced 示例块内→子串命中但行级不命中，契约测试过严。修=测试豁免 fence 内示例锚 或 报告示例锚移出 fence。**发现于本 change 期间、根因在别处。**
- **verify Minor**：`openspec/INDEX.md` 规则表未登记 `lens-metric-contract.md`（task 1.2 前半）——curated 子集可接受，功能不受损（三 SKILL 直引权威源、随 canonical 部署）。
- **ADR-6 张力遗留**：surfacing 因零持久态取幂等重提示——人已决定保留的镜下次仍被提示（可接受）；若要压制重复提示需持久登记（违 ADR-6），留观察。
- **成本维度 T29**：本 change 撤出另立，标准已在 todolist T29 grill 调研定稿（checkpoint 时间戳、phase 粒度、人类门锚剔除、墙钟非计算成本）。

## ▶ 下一阶段建议

1. **发布边界**：本 change 是 workflow bundle 源仓改动——merge 后须 **push → 运行 checkout `/sdflow-upgrade`** 激活（否则消费仓/运行 checkout 仍用旧 bundle）。
2. **数据自证**：Success Metric #2（≥2 归档 change 聚合出非空独立列）是**部署后观察项**——本 change 已产首批真锚（自己的 code-review 报告），再跑 1-2 个新 change 走完全流程即可首次真实聚合验证；届时可评 codex 独立率是否持续 > claude 镜（验 outside-voice 非冗余价值）。
3. **可开清理 change**：T29（成本度量，标准已定，可直接 propose）优先级高于 T54/T55；B5 可随任一 ship-gate 相关 change 顺手修。
