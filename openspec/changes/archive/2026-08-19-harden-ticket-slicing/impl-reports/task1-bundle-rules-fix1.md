# Task 1 Fix 1 — 规则 3 与 BASE-18 去重复制

## 发现（Important，来自 Spec 轴）

`sdflow-init/assets/workflow/reference/change-decomposition-standard.md` 规则 3 把
`spec-checklists/spec-quality-base.md` BASE-18 的防吸积 AND 门判据近逐字抄了一遍
（同 capability ∧ 高耦合 ∧ 低增量成本 三元素 + 不满足时的 defer 兜底列举），
违反本票验收标准「标准文与 BASE-18 互为指针、不复制文本」与 Global Constraints Goals
「拆分标准单一源放 bundle 的 `reference/`，三处消费点指针引用不复制文本」。

## 改动

文件：`sdflow-init/assets/workflow/reference/change-decomposition-standard.md`

规则 3（原第 19-22 行）:

```
3. **相关发现优先 fold**：执行 / 评审过程中撞到与当前 change 相关的 bug / todo，默认**并入
   当前 change 做掉**，而非另开。是否真的该 defer，判定入口 = `BASE-18` 的防吸积 AND 门——
   **同 capability ∧ 高耦合 ∧ 低增量成本**三者皆满足才真 fold 进当前 change；任一不满足
   → defer 另开（真独立、扩容大、需自身设计审查、高 blast-radius 均天然落 defer）。
```

改为（现第 19-21 行）:

```
3. **相关发现优先 fold**：执行 / 评审过程中撞到与当前 change 相关的 bug / todo，默认**并入
   当前 change 做掉**，而非另开。是否真的该 defer，判定入口 = `BASE-18` 的防吸積 AND 门——
   具体判据（三元素与不满足时的 defer 兜底）见该行，本文不复述。
```

保留了规则 3 本身的规范语义（相关发现默认 fold、defer 判定入口指向 BASE-18），删除的是
AND 门三元素本体及其 defer 兜底枚举——这段具体判据现在只存在于 BASE-18 一处（单一源）。

**未改动**：规则 1/2/4、README、BASE-18 本身、Why 段第 36 行「判据落在『是否同
capability、是否高耦合、增量成本是否低』」——编排层已裁决该行是说理性提及（无「三者皆满足
才 fold / 任一不满足 → defer」的判定本体），保留不改，MUST NOT 再改。

## 核验

### grep 核验（AND 门判据本体只在 BASE-18 一处）

```
$ grep -rn "同 capability" /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-init/assets/workflow/
sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md:42:| BASE-18 | ... 「同 capability ∧ 高耦合 ∧ 低增量」三者皆满足才真 fold 进当前 change，任一不满足 → defer 另开（真独立 / 扩容大 / 需自身设计审查 / 高 blast-radius 天然落此）。... |
sdflow-init/assets/workflow/reference/change-decomposition-standard.md:36:的失衡都挡住：判据落在「是否同 capability、是否高耦合、增量成本是否低」，而不是「看起来像不像
```

判定本体（三元素 AND 门 + defer 兜底枚举）只出现在 `spec-quality-base.md:42`（BASE-18）；
`change-decomposition-standard.md:36` 是 Why 段的说理性提及，非规范判定句式，保留符合
编排层裁决。

### pytest 全绿（前台跑，`/usr/bin/python3 -m pytest -q`）

```
2601 passed, 10 skipped in 375.49s (0:06:15)
```

退出码 0，全绿，无失败/error。

## 状态

`DONE` — 规则 3 改为纯指针引用，AND 门判据单一源收敛到 BASE-18；grep 与 pytest 均核验通过。
