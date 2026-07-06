# Tasks — sdflow-retro

> grill 定 OQ1-3（边界靠 pre-archive 路径不改 tag / 聚合器移进 skill / 不做语义分桶）；spec-review 冷镜实测修订了边界引擎（D8-D13，见 design）。下方任务已并入修订。

## 1. change 边界 + 阶段墙钟核（时间维，TDD）
- [x] 1.1 `retro_report.py`：change 发现（扫 `openspec/changes/*/` 活动 + `openspec/changes/archive/*/` 归档，剥日期前缀取 change 名）
- [x] 1.2 边界检测：`git log -- openspec/changes/<name>/`（pre-archive 路径，**禁 `--follow`**〔F-A/D1：--follow 只对单文件、且会搅入 rename〕）→ (sha, ts, subject)；归属靠路径不靠 tag
- [x] 1.3 边界守卫〔D9〕：**剔 seed-mass 提交**（一提交碰 ≥3 change dir，如创世 `db3c824`）；**pre-archive 路径 0 提交 → 兜底查 archive 路径**；**恰好 0/1 提交 → 显式守卫**（墙钟不可算、标"边界不可解析"计入 K，不崩）
- [x] 1.4 阶段映射〔D-C 词表〕：**最长前缀匹配** + `-fix/-gate/-autoplan/-rewrite` 归族；补 design-gate/writing-plans/final-review/model-baseline 词条；映射不出 → "unknown 阶段"桶
- [x] 1.5 **done 靠 path-rename**〔D8〕：检"提交把 change dir mv 进 archive/"（R 状态/删旧建新）映射 done，**不靠 subject 前缀**（实测 14/15 归档提交是 chore/feat）
- [x] 1.6 阶段墙钟：相邻 ts 差，标注"阶段级 elapsed（含人时间）"〔adr/0009〕；**Δ<0（ts 非单调）钳 0 + reorder-suspected**〔E〕
- [x] 1.7 git 硬化：`core.quotePath=false` + `errors="replace"`（承 trivial_shape 口径），畸形输出不崩

## 2. 镜价值维吸收 + join
- [x] 2.1 `git mv` `lens_metric_aggregate.py` + `tests/test_lens_metric_aggregate.py`：`sdflow-init/assets/workflow/tools/` → `sdflow-retro/scripts/`（含 tests/ 子目录，**校准 test 的 `parents[1]`** 使指向 scripts/〔G1〕）；SKILL 用**绝对 skill 路径** subprocess 调它〔F3：禁 cwd 相对〕
- [x] 2.2 per-change join〔D11〕：扫 **active `changes/*/` + archive 两源**的 **`spec-review-report.md` 与 `code-review-report.md` 两份**报告，按 layer 分归属挂采纳率/独立率；无锚 → 标"无度量锚"不阻塞
- [x] 2.3 hr-tg **双列**〔D10〕：读 spec-review + code-review 各自 `hr-tg` 锚 hit → `spec_hr_tg`/`code_hr_tg` 两列（不做语义分桶，只客观 flag；单列会 none 覆盖命中）

## 3. 报告合成（view-only 再生，原子写）
- [x] 3.1 `openspec/retro/report.md` 生成（**tracked 活文档**，含**进行中 change 标 in-progress**）：per-change 行（阶段Δ 含 done Δ + 镜价值 + hr-tg 双列）+ 聚合（阶段占比 / 双峰散点 / per-镜价值表）
- [x] 3.2 **原子写**〔D13〕：report.md 写盘沿用 buglist/todolist 原子写 helper（parent-dir 建 / 覆盖保权限 / 无残留 tmp / replace 失败原文件不变）
- [x] 3.3 顶部覆盖计数：覆盖 N / **有真锚 M（实测仅 2/17，显性防 N=2 当趋势）**/ 边界不可解析 K〔D-D/fail-safe〕
- [x] 3.4 N≥10 待复评镜 surfacing：**锚定机械契约**〔D12〕——报告顶部独立 `⚠️ 待复评` 区块 + 固定前缀标记（非"显著"形容词，可机验位置/标记）
- [x] 3.5 幂等：源无变化二次运行产出等价报告（无漂移）

## 4. SKILL.md 编排
- [x] 4.1 `sdflow-retro/SKILL.md`：frontmatter（description 锚定"openspec change / 评审工作流 / 成本×价值 / 镜价值 复盘"限定词〔轴3：与运行时同名 gstack `retro` 及 maintain 区隔，触发精度足〕）+ 编排（调脚本→再生报告→呈现待复评）
- [x] 4.2 数据类 skill 约定：机械活（边界/映射/join/原子写/不变量）交脚本，SKILL 只判断编排

## 5. 级联改动（maintain 瘦身 + 聚合器迁移善后）
- [x] 5.1 `sdflow-maintain/SKILL.md` 步骤 5：内联聚合 surfacing → 薄指针「跑 `/sdflow-retro` 看完整复盘（含 N≥10 待复评镜）」；不丢归档后自动提醒 cadence
- [x] 5.2 核对 maintain 回归纯 INDEX.md 本职（description 若提聚合则同步）
- [x] 5.3 `sdflow-init/scripts/init.py`：**仅移出源文件**；`copytree(tools/)` 与 `ignore_patterns("tests")` 通用排除 **MUST 保留**〔F5/G2：它还护 `trivial_shape.py` 部署 + `test_trivial_shape.py` 排除，删了重演 CF-6〕；init.py:116-120 注释同步改（别暗示 tests 排除只为聚合器）
- [x] 5.4 `sdflow-init/tests/test_init.py`：line 119 + **line 126（--dev 断言）** 的聚合器断言**改指 `trivial_shape.py`/`test_trivial_shape.py`**（保 tests-exclusion 覆盖，**非删**）；跑测试确认绿
- [x] 5.5 prose 指针**4 处**改指 retro：`sdflow-code-review/SKILL.md:132`、`sdflow-spec-review/SKILL.md:105`、**`:120`**、`sdflow-maintain/SKILL.md:78` + **`docs/workflow-skills/sdflow-code-review.md:57`**〔F2b/C5〕
- [x] 5.6 `openspec/INDEX.md`：**加 retro/ 策展条目**〔轴6〕 + workflow-metrics 条目聚合器路径更新（tools/ → sdflow-retro/scripts/）

## 6. 测试覆盖（TG-18，数据类必测）

```
  测试覆盖图（retro_report.py）
  [+] change 边界检测
    ├── [★★★] 活动/归档 change 各归属正确（路径不靠 tag）
    ├── [★★★] seed change pre-archive 0 提交 → archive 兜底 / 仍 0-1 标不可解析〔D9〕
    ├── [★★★] seed-mass 提交(碰≥3 dir)被剔除，不污染墙钟起点〔D9〕
    ├── [★★★] done 靠 path-rename（归档提交是 chore/feat 也命中 done）〔D8〕
    ├── [★★] 同名复用 → 两 archive 目录 → 标边界存疑降级
    ├── [★★] 前缀映射不出 → unknown 桶；最长前缀匹配（impl-review 不被 review 吞）〔D-C〕
    └── [★★] change 无提交历史/恰 1 提交 → 不崩
  [+] 阶段墙钟
    ├── [★★★] 相邻 Δ 正确 + 含人时间口径标注
    ├── [★★] Δ<0（ts 非单调）钳 0 + reorder-suspected〔E〕
    └── [★★] 单 checkpoint（无相邻对）不崩
  [+] 镜价值 join
    ├── [★★★] 一 change 两份报告(spec+code)锚正确合并、分 layer〔D11〕
    ├── [★★★] active change 已有锚 → 挂上（非误标无锚）〔D11〕
    ├── [★★★] 无锚 change 标"无度量锚"不阻塞
    └── [★★] hr-tg 双列 spec/code 各归位（单列 none 不覆盖命中）〔D10〕
  [+] 报告合成
    ├── [★★★] 覆盖计数正确（N/有真锚 M/K）
    ├── [★★] 双峰/占比聚合数值正确
    ├── [★★★] 原子写（无残留 tmp / replace 失败原文件不变）〔D13〕
    └── [★★★] 幂等：二次运行等价（无漂移）
```

- [x] 6.1 `sdflow-retro/scripts/tests/test_retro_report.py`：上图各分支（**用真实归档语料样本**做 fixture——seed change/feat 归档/多报告/无锚，冷镜实测证这些才是真 case）
- [x] 6.2 聚合器随迁 `test_lens_metric_aggregate.py`，`parents[1]` 校准后绿
- [x] 6.3 全量 `pytest` 零回归——**MUST 含 `test_init.py`（tests-exclusion 改断言后绿）+ ship_gate 测试（本 change 不改 tag，须仍绿）+ test_trivial_shape.py（部署未受影响）**

## 7. 部署 + 收尾
- [x] 7.1 `setup.sh` 装新 skill；README「Skills 列表」+ CLAUDE.md 同步新增 skill + `openspec/retro/` 目录角色
- [x] 7.2 dogfood：对本仓跑 `/sdflow-retro` 生成首份 `openspec/retro/report.md`，自洽核对（本 change 自身进复盘、标 in-progress）；**验证 seed change/feat 归档/2 真锚 等实测 case 输出正确**
- [x] 7.3 merge 后 push → 运行 checkout `/sdflow-upgrade` 激活；核消费仓 update 后孤儿聚合器副本被清（copy_bundle rmtree）
