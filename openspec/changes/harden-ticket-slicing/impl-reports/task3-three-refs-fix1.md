# Task 3 · Critical 修复报告（fix1）：SA-17 scope 内聚检查未接回执行路径

## 问题回顾

Task 3 把 SA-17 的 scope 内聚检查判据整条下沉到新建的
`sdflow-spec/references/scope-cohesion-check.md`，但没有把它接回执行路径：

1. `SKILL.md` 的「按需资料路由（默认不加载）」索引没有列出该文件。
2. B.7 item 3 只有一行「判据见 X」，无 MUST 强度；随后的 🔴 句「两者未经人确认 MUST NOT 自动写入」的
   「两者」只指 item 1/2（ADR + 术语），不覆盖 item 3。

## 修复内容（两处，均已落盘）

### 修复 1：B.7 item 3 补最小 MUST 强度

`sdflow-spec/SKILL.md:372`

- 改前：`3. scope 内聚检查——判据见 \`references/scope-cohesion-check.md\`。`
- 改后：`3. scope 内聚检查：MUST 读 \`references/scope-cohesion-check.md\` 判据；发现偏离 MUST 呈现给人拍板，MUST NOT 静默调整范围。`

item 3 现在自带 MUST 强度（读判据 + 呈现给人拍板 + MUST NOT 静默调整范围），不再依赖后面那句只覆盖
item 1/2 的 🔴 句，语义与 SA-17「发现偏离 SHALL 连同拆分/合并建议呈现给人拍板，MUST NOT 静默调整范围」对齐。

### 修复 2：路由索引补一行

`sdflow-spec/SKILL.md:182`（新增，紧跟在原 ADR/术语提议那条 bullet 之后）：

```
- B.7 item 3 做 scope 内聚检查时读取 [`references/scope-cohesion-check.md`](references/scope-cohesion-check.md)。
```

格式与其余五条「何时读」bullet 一致。

## 腾空间：逐处「改前 → 改后 + 为什么无损」

新增两处共 +147 字符（item3 行 +38，路由行 +109），文件原本 17,998/18,000，必须腾出至少 145 字符。
腾出的两处均为**字面重复文本**，删除/压缩后不损失任何 MUST/MUST NOT/判定条件/例外声明：

### 腾空间 A：删除文末与路由索引verbatim 重复的整段

`sdflow-spec/SKILL.md`（原第 528–532 行，出口序列之后）：

- 改前（整段删除）：
  ```
  ---

  历史取舍不进入默认运行；仅在审计历史依据或设计未来 T132 gate 时读取
  [`references/evolution-notes.md`](references/evolution-notes.md)。T132 未来 gate 尚未实现，保持 OPEN。
  ```
- 改后：（无，整段删除，文档在「🔴 MUST NOT 引用『主审裁决需冷视角』」后结束）
- 为什么无损：这段与「按需资料路由」索引里的 bullet（`SKILL.md:178-179`，未改动）**逐字重复**——
  `仅在审计历史依据或设计未来 T132 gate 时读取 [evolution-notes.md]。T132 未来 gate 尚未实现，保持 OPEN。`
  同一条「何时读 + 现状」在同一文件里出现两次，删除文末这份不改变任何指令内容——读者在文档任意位置
  都能从路由索引拿到同样的信息，且路由索引出现更早（第 178 行 vs 原第 531 行），是更合理的唯一落点。
  节省 137 字符（用 `python3 -c` 实测：删除前后 diff 差值 = 18141 → 18003，之后与其余修改叠加）。

### 腾空间 B：压缩 B.7 与 B.6 verbatim 重复的警示句

`sdflow-spec/SKILL.md:374`（原第 373–374 行）：

- 改前：
  ```
  🔴 **两者未经人确认 MUST NOT 自动写入。** 判据与模板见
  [`references/adr-and-glossary-templates.md`](./references/adr-and-glossary-templates.md)。
  ```
- 改后：
  ```
  🔴 同 B.6：item 1/2 两者未经人确认 MUST NOT 自动写入，判据与模板同引 B.6 所示文件。
  ```
- 为什么判定无损、以及编排层要求正面回答的三问：

  这句话在 B.6（`SKILL.md:362-364`，**本次未改动**）里逐字出现过一次——「🔴 两者未经人确认 MUST NOT
  自动写入。判据与模板见 [adr-and-glossary-templates.md]」，B.7 是对 B.6 的「收敛前逐条回扫」（B.7 结尾
  自己就写着「与 B.6 的区别」），紧接着把同一句警示原样再抄一遍。压缩把 MUST NOT 语义完整保留
  （「两者未经人确认 MUST NOT 自动写入」一字不改），只是把**直接文件链接**换成了**指向 B.6 的指针**。

  **① `adr-and-glossary-templates.md` 是否仍在执行路径上可达**：是，且是**双重可达**、完全未受本次改动
  影响——(a) B.6 原句（`SKILL.md:362-364`）持有的直接链接**我没有动它**，B.7 上面几行就是 B.6，物理
  距离是「同一屏内往上翻几行」；(b) 路由索引第 181 行「命中 ADR/术语提议条件时读取
  [adr-and-glossary-templates.md]」也未改动，是独立于 B.6/B.7 之外的第二条直接路径。两条路径都完好，
  我删的只是 B.7 里的**第三份**重复。

  **② 「两者」的指代是否更清楚还是更糊**：净效果是**更清楚**。原句「两者」在 B.7 的语境里本来就该指
  item 1/2（因为 item 3 是本次新加、且有自己独立的 MUST 语义，不受这句管），但原文没有显式说明，
  容易被误读成「item 1/2/3 三者」。改后显式写「item 1/2」消除了这个歧义，是澄清而非缩窄。

  **③ 净效果判定——不是完全无损，是一处已知的微小代价**：删链接确实把「B.7 单独一句话就能定位到文件」
  降级成「需要读者知道/回看 B.6」的一跳间接指路。对**连续通读**这个文件的 agent（本 skill 的唯一
  设计用法——SKILL.md 是一次性顺序读完，不是查表式随机跳转文档）而言，这一跳发生在同一屏内、
  上一个小节标题之下，代价接近零；但如果未来出现「只读 B.7 局部、不读 B.6」的消费方式（当前没有这种
  用法，B.7 本身依赖 B.6 的上下文才能理解「收敛前回扫」的含义，所以这种局部读取本就不成立），
  这一跳会造成一次额外查找。**我判定这不是完全对称的无损压缩，是一个成本极低、但确实存在的已知代价
  （已知代价 vs 语义损失的区别：MUST/MUST NOT 内容零丢失，只丢失了「零跳转直达」这一便利性）**，
  如实标注在此，是否需要恢复直接链接由编排层裁定。

## 核验命令与输出（均前台运行，非后台 Monitor）

```
$ python3 -c "print(len(open('sdflow-spec/SKILL.md',encoding='utf-8').read()))"
17934
EXIT_1=0
```

```
$ /usr/bin/python3 -m pytest hack/tests/test_sdflow_spec_resident_contract.py -q
..........                                                               [100%]
10 passed in 0.01s
EXIT_2=0
```

```
$ /usr/bin/python3 -m pytest -q
........................................................................ [  2%]
（省略中间进度行，全部为 . / s）
...................                                                      [100%]
2601 passed, 10 skipped in 370.01s (0:06:10)
EXIT_3=0
```

```
$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 27 个投放面全部与真相源一致（四条通则 + 广审镜定义）
EXIT_4=0
```

四条命令全部 exit 0。文件最终 17,934 字符，低于 18,000 阈值，余量 66 字符。

## Scope 确认

本次只改了 `sdflow-spec/SKILL.md` 里上述两处修复 + 两处腾空间（共四处 diff hunk，见上）。未触碰
`sdflow-roadmap/SKILL.md`、`sdflow-code-review/SKILL.md`、`references/scope-cohesion-check.md` 的实质内容，
未改动或放宽 `hack/tests/test_sdflow_spec_resident_contract.py` 的阈值。

## 完成信号

本报告不勾 `tickets.md` 复选框、不打 `checkpoint(...:task3-...)` 完成标签——这两项按信号权威表由双轴审通过后执行模式补打。
