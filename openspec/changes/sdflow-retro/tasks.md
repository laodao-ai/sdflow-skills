# Tasks — sdflow-retro

> 前置：grill MUST 先定 OQ1（边界机制，倾向 (a)git-log-path + (c)阶段词表）、OQ2（聚合器归属，倾向留 bundle 引用）、OQ3（报告 schema / change 类型判据）。下方任务按**推荐方向**排；grill 翻案则相应调整。

## 1. change 边界 + 阶段墙钟核（时间维，TDD）
- [ ] 1.1 `retro_report.py`：change 发现（扫 `openspec/changes/*/` 活动 + `openspec/changes/archive/*/` 归档，取 change 名）
- [ ] 1.2 边界检测：`git log --follow -- <change 路径>` → 该 change 提交 (sha, ts, subject)；归属靠路径不靠 tag〔D1〕
- [ ] 1.3 阶段词表映射：checkpoint 前缀 → 阶段（ff/grill/spec-review/impl-review/done-verify/done-archive/task*）；映射不出 → "unknown 阶段"桶〔C 词表〕
- [ ] 1.4 阶段墙钟：相邻 checkpoint ts 差，标注"阶段级 elapsed（含人时间）"口径〔adr/0009〕
- [ ] 1.5 git 硬化：`core.quotePath=false` + `errors="replace"`（承 trivial_shape 口径），畸形输出不崩

## 2. 镜价值维吸收 + join
- [ ] 2.1 接入 `lens_metric_aggregate.py`（OQ2：留 bundle 经 resolve-workflow 引用 / 或移入 scripts——按 grill 定）
- [ ] 2.2 per-change join：把该 change 归档报告的 lens-metric 锚（采纳率/独立率）挂到该 change 复盘行；无锚 → 标"无度量锚"不阻塞
- [ ] 2.3 change 类型分类（OQ3）：读该 change 评审报告的 `hr-tg` 锚 + 阶段Δ → 琐碎/routine/HR-TG（不新造判据）

## 3. 报告合成（view-only 再生）
- [ ] 3.1 `openspec/retro/report.md` 生成：per-change 行（阶段Δ + 镜价值 + 类型）+ 聚合段（阶段占比 / 成本双峰散点）
- [ ] 3.2 顶部覆盖计数：覆盖 N / 有镜锚 M / 边界不可解析 K，缺口显性〔fail-safe〕
- [ ] 3.3 N≥10 待复评镜 surfacing 显著呈现（surfacing 正主迁入 retro）
- [ ] 3.4 幂等：源无变化二次运行产出等价报告（无漂移）

## 4. SKILL.md 编排
- [ ] 4.1 `sdflow-retro/SKILL.md`：frontmatter（name/description，触发"复盘/评估 workflow/成本/镜价值"）+ 编排（调脚本→再生报告→显著呈现待复评）
- [ ] 4.2 数据类 skill 约定：机械活交脚本、SKILL 只判断编排

## 5. maintain 瘦身（策略 B，级联）
- [ ] 5.1 `sdflow-maintain/SKILL.md` 步骤 5：内联聚合 surfacing → 薄指针「跑 `/sdflow-retro` 看完整复盘（含 N≥10 待复评镜）」；不丢归档后自动提醒 cadence
- [ ] 5.2 核对 maintain 回归纯 INDEX.md 本职（description 若提聚合则同步）

## 6. 测试覆盖（TG-18，数据类必测）

```
  测试覆盖图（retro_report.py）
  [+] change 边界检测
    ├── [★★★] 活动 change / 归档 change 各归属正确
    ├── [★★★] 裸历史标签仍靠路径归属（不受 tag 影响）
    ├── [★★] 前缀映射不出 → unknown 桶
    └── [★★] change 无提交历史 → 标"不可解析"不崩
  [+] 阶段墙钟
    ├── [★★★] 相邻 Δ 计算正确 + 含人时间口径标注
    └── [★★] 单 checkpoint change（无 Δ）不崩
  [+] 镜价值 join
    ├── [★★★] 有锚 change 挂上采纳率/独立率
    └── [★★★] 无锚 change 标"无度量锚"不阻塞时间维
  [+] 报告合成
    ├── [★★★] 覆盖计数正确（N/M/K）
    ├── [★★] 双峰/占比聚合数值正确
    └── [★★★] 幂等：二次运行等价（无漂移）
```

- [ ] 6.1 `tests/test_retro_report.py`：上图各分支（合成 git fixture + 合成归档报告）
- [ ] 6.2 若聚合器移入（OQ2）随迁 `test_lens_metric_aggregate.py`；若留 bundle 则复用其现有测试
- [ ] 6.3 全量 `pytest` 零回归（含 spec-workflow gate 相关既有测试——本 change 不改 tag 格式，MUST 验 ship_gate 测试仍绿）

## 7. 部署 + 收尾
- [ ] 7.1 `setup.sh` 装新 skill（含 openspec/retro/ 落点说明）；README「Skills 列表」+ CLAUDE.md 同步新增 skill
- [ ] 7.2 dogfood：对本仓跑 `/sdflow-retro` 生成首份 `openspec/retro/report.md`，自洽核对（本 change 自身也进复盘）
- [ ] 7.3 merge 后 push → 运行 checkout `/sdflow-upgrade` 激活
