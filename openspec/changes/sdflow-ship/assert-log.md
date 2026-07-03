# assert-log — sdflow-ship

2026-07-04（Task 9：T20 串行句 + grep 断言留档）

以下每条命令均在仓库根 `/Users/cheneyzhao/Documents/04-sdflow-skills`（分支 `feat/sdflow-ship`）真实执行，实际输出原样粘贴。

---

## 1. `grep -c "有把握自动选" sdflow-init/assets/workflow/workflow.md`

**期望**：0

```bash
$ grep -c "有把握自动选" sdflow-init/assets/workflow/workflow.md
0
```

（`grep -c` 未命中时返回码为 1，`0` 为命中计数，符合预期）

**结果**：✅

---

## 2. `grep -l "model-tiers.md" sdflow-ship/SKILL.md sdflow-done/SKILL.md sdflow-spec-review/SKILL.md sdflow-code-review/SKILL.md`

**期望**：4 个文件全列出

```bash
$ grep -l "model-tiers.md" sdflow-ship/SKILL.md sdflow-done/SKILL.md sdflow-spec-review/SKILL.md sdflow-code-review/SKILL.md
sdflow-ship/SKILL.md
sdflow-code-review/SKILL.md
sdflow-spec-review/SKILL.md
sdflow-done/SKILL.md
```

4 个文件全部列出（顺序为 grep 内部匹配顺序，非入参顺序，但集合完整）。

**结果**：✅

---

## 3. `grep -c "MUST 待 Step1" sdflow-spec-review/SKILL.md`

**期望**：≥1

```bash
$ grep -c "MUST 待 Step1" sdflow-spec-review/SKILL.md
1
```

对应 Task 9 Step 3 在「## 第二步」标题行后插入的 T20 串行纪律句：

> **串行纪律〔T20〕**：**MUST 待 Step1 checkpoint 完成后才 fan-out，禁止与 Step1 并行**（多镜评审对象须含 autoplan amendment）；若历史运行已并行，Step3 裁决须 diff autoplan amendment 增量核对并在报告注明。

**结果**：✅

---

## 4. `grep -c "ship-gate: design-approved" sdflow-spec-review/SKILL.md`

**期望**：≥1

```bash
$ grep -c "ship-gate: design-approved" sdflow-spec-review/SKILL.md
1
```

**结果**：✅

---

## 5. `grep -c "ship-gate: verify" sdflow-done/SKILL.md`

**期望**：≥2（PASS/FAIL 两行）

**首次执行**（修改前，锚行写在同一行文字说明里：``` `<!-- ship-gate: verify=PASS -->` 或 `<!-- ship-gate: verify=FAIL -->` ```）：

```bash
$ grep -c "ship-gate: verify" sdflow-done/SKILL.md
1
```

❌ 与期望 ≥2 不符——根因：PASS/FAIL 两个锚行字面量被写在同一自然语言行内（用"或"连接），`grep -c` 按**匹配行数**计数，两个锚行落在同一行只算 1 行；而 `sdflow-ship/tests/test_anchor_contract.py::test_skill_templates_carry_same_literals` 本就要求 `sdflow-done/SKILL.md` 同时字面含有 `<!-- ship-gate: verify=PASS -->` 与 `<!-- ship-gate: verify=FAIL -->` 两个锚行——只是此前挤在一行文字说明里，未如 `sdflow-code-review/SKILL.md`（两行分列，即 CMD6 天然 =2 的原因）那样各自独立成行。

**修复**：把 `sdflow-done/SKILL.md` 第 78 行的说明改写为代码块形式，PASS/FAIL 两个锚行各占一行（保留原有"模板写死二选一、勿改写措辞、勿两行并存"的语义，仅调整排版使两个字面量各自独立成行）：

```markdown
   - **结论行下方紧跟机器锚行（ship-gate 契约，模板写死二选一，勿改写措辞、勿两行并存）**：

     ```
     <!-- ship-gate: verify=PASS -->
     <!-- ship-gate: verify=FAIL -->
     ```

     ——二选一，/sdflow-ship 以字面查找机判
```

**重跑（终态）**：

```bash
$ grep -c "ship-gate: verify" sdflow-done/SKILL.md
2
```

**结果**：✅（终态，已修复排版；`test_anchor_contract.py` 随 Step 4 一并验证通过）

---

## 6. `grep -c "ship-gate: code-review" sdflow-code-review/SKILL.md`

**期望**：≥2

```bash
$ grep -c "ship-gate: code-review" sdflow-code-review/SKILL.md
2
```

（该文件锚行本就分两行书写：`<!-- ship-gate: code-review=pass -->` 与 `<!-- ship-gate: code-review=blocked -->`，无需修改。）

**结果**：✅

---

## 7. `python3 -m pytest -q 2>&1 | tail -2`

**期望**：全绿无 warning

```bash
$ python3 -m pytest -q 2>&1 | tail -2
..........................................................               [100%]
274 passed in 14.36s
```

**结果**：✅（全仓 274 用例全绿，无 warning）

---

## 附加：sdflow-ship 子集 + 严格 warning 门（Step 4 完成判据）

```bash
$ python3 -m pytest sdflow-ship/tests/ -q -W error
.........................................                                [100%]
41 passed in 3.96s
```

40（既有）+ 1（本次新增 `test_serial_discipline.py`）= 41，`-W error` 下无任何 warning 被放大成失败，全绿。

**结果**：✅

---

## 汇总

| # | 断言 | 结果 |
|---|------|------|
| 1 | 无"有把握自动选"残留 | ✅ |
| 2 | 4 个 SKILL.md 均引用 model-tiers.md | ✅ |
| 3 | spec-review 含 T20 串行纪律句 | ✅ |
| 4 | spec-review 含 design-approved 锚 | ✅ |
| 5 | sdflow-done 含 verify PASS/FAIL 双锚（先失败后修复排版重跑通过） | ✅（修复后终态） |
| 6 | sdflow-code-review 含 code-review 双锚 | ✅ |
| 7 | 全仓 pytest 全绿无 warning（274 passed） | ✅ |
| 附加 | sdflow-ship 子集 -W error 全绿（41 passed） | ✅ |

7 条主断言 + 1 条附加断言，全部 ✅；其中第 5 条经历一次"实际不符期望 → 定位根因（锚行同行挤压）→ 修排版 → 重跑转绿"的真实闭环，非直接构造符合预期的文本。
