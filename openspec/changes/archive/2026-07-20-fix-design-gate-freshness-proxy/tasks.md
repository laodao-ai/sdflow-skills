## 1. 勾选框翻转豁免（P0，`ship_gate.py`）〔spec-review-amendment：原「角色分流」经双 CEO 镜证伪，改为内容等值判据〕

- [x] 1.1 在 `is_stale()` 的 design 分支内：帧内**落在 design 域监视集内**的触及路径集 == `{tasks.md}` 时（🔴 **不是**整个 commit 的文件列表——checkpoint 走 `git add -A`，真实完成提交必然打包源码；按整 commit 求值会让豁免永不触发、P0 白做〔spec-review-amendment，Eng 镜 3.1〕），取该提交前后两版 `tasks.md` 内容做勾选框归一化行级等值比较；等值 ⇒ 不判失鲜，否则照判
- [x] 1.1a 实现形态：沿用现有**逐文件 return-True** 结构，仅对 `sub == "tasks.md"` 单独分支（等值则 `continue`），MUST NOT 重构成帧级两遍预扫描〔Eng 镜 1〕〔**done-amendment：本条字面约束已被 code-review F1 推翻**——冷层查出 `git log --name-only` 对 merge 提交不输出文件、且 rename 吞源路径（两条 fail-open），修法必须换成帧级 `diff-tree -m -r --raw --no-renames -z` 求路径集。目标（豁免只在纯勾选时成立）达成，机制与本条设想不同，如实留档不假勾〕
- [x] 1.1b 扩展 `git log` format 携带 commit sha（现为 `--format=%x00%s`，无 `%H` ⇒ 取不到 blob，是 P0 可实现的前提），分隔符 MUST 无歧义（subject 可含空格/冒号）〔Eng 镜 1〕〔**done-amendment：机制已变**——最终未走 `git log --format=%H`，而是 `git diff-tree -m -r --raw --no-renames -z --root`（分帧与取路径拆两跳，因 `-z` 的 NUL 与 `--format` 帧分隔符互相污染）。「取得到 blob」这个目的达成，路径不同〕
- [x] 1.1c 前后两版内容读取 MUST 用 `run_git_rc` 显式判 returncode；任一侧 rc≠0 ⇒ **直接保守判失鲜**，MUST NOT 依赖 `run_git` 的空串巧合不等（双侧失败会得 `"" == ""` ⇒ 判等值 ⇒ **放行真实设计改动**）〔Eng 镜 2.2〕
- [x] 1.1d 读取 MUST 保真：MUST NOT 复用会 `.strip()` / `text=True` 的路径（吞首尾空白、末尾换行、CRLF、非 UTF-8 字节，四者各自可造假等值）〔codex Eng 5 + Eng 镜 2.2〕
- [x] 1.2 归一化 MUST 仅替换 `[ ]` / `[x]` / `[X]` 标记本身，MUST NOT 触碰缩进 / 空白 / 其余字符
- [x] 1.3 前版取不到（该提交中新建 `tasks.md`）⇒ **保守判失鲜**
- [x] 1.4 确认 `proposal.md` / `design.md` / `specs/` 分支逐字未改；确认既有 `checkpoint(impl-review)` 精确式豁免逐字未改
- [x] 1.5 确认无语义 diff、无 markdown 结构解析、不依赖工作树状态（Compliance 硬条款）

## 2. 失鲜诊断指引（P1，`ship_gate.py`）

- [x] 2.1 design 失鲜的 `REFUSE_START` reason 携带触发提交（subject 或 sha）与触发文件路径
- [x] 2.2 reason 携带**分类原因**（混合路径 / 非勾选框变化 / 前后版缺失 / 状态不合格），机读与人读同源；**默认处置只推荐「重跑设计门」一条**，`checkpoint(impl-review)` **MUST NOT** 出现在默认处置指引中〔impl-review-fix：原文写「附两条分支处置提示…⇒ 走 checkpoint(impl-review) subject 通道」，与 spec-review 期改写后的 ADR-2 口径矛盾，系改写方案未扫残留引用所致（本 change 第 6 处同类接缝矛盾），此处对齐〕
- [x] 2.3 确认退出码与判定结果不受本项影响（纯诊断）

## 3. dispatch 信号权威表（P2，`sdflow-implement/SKILL.md`）

- [x] 3.1 implementer / fix dispatch prompt 必填槽补信号权威表（正面陈述，非禁令清单）
- [x] 3.2 表内容与 `ship_gate.py` 实际消费的完成判据一致（plan 分段复选框 + checkpoint 标签）
- [x] 3.3 SKILL 文本守（`test_skill_text.py` 同族）机械断言权威表在场

## 4. 测试

- [x] 4.1 正例：提交只触及 `tasks.md`、只翻勾选框 ⇒ 不失鲜
- [x] 4.2 负例：勾选框 + 同行措辞改动 ⇒ 失鲜
- [x] 4.3 负例：勾选框 + 新增一个 `### Task N+1:` 段（范围扩大）⇒ 失鲜
- [x] 4.4 负例：同一提交同时触及 `tasks.md`（纯勾选）与 `design.md` ⇒ 失鲜
- [x] 4.4a 负例：只改缩进 / 空白（无勾选框变化）⇒ 失鲜（归一化未过宽）
- [x] 4.4b 负例：`tasks.md` 在该提交中新建（无前版）⇒ 保守判失鲜
- [x] 4.4c 负例：删除一个 `### Task N:` 段 ⇒ 失鲜
- [x] 4.4d 正例：勾选框由 `[x]` 翻回 `[ ]`（反向）⇒ 不失鲜（归一化对称）
- [x] 4.4e 🔴 **正例（最贴近真实故障）**：同一提交既纯勾选 `tasks.md`、又改仓库别处源码（`git add -A` 打包形态）⇒ **不失鲜**。**缺此例则「按整 commit 文件列表求值」的错误实现全绿通过、而豁免在真实世界永不触发**〔Eng 镜 3.1 + design-voice〕
- [x] 4.4f 负例：fenced code block 内的 `[ ]`↔`[x]` 翻转 ⇒ 失鲜（fence-aware）
- [x] 4.4g 负例：表格 / 行内反引号 / 散文字面量中的 `[ ]`↔`[x]` ⇒ 失鲜（锚定到 task-list 行首）
- [x] 4.4h 负例：同一行含多个标记，task marker 与文档字面量反向翻转 ⇒ 失鲜
- [x] 4.4i 负例：纯行重排（零字符改动）⇒ 失鲜（位置对齐，非 LCS）
- [x] 4.4j 负例：CRLF↔LF、末尾换行增删、首尾空白 ⇒ 失鲜（保真读取）
- [x] 4.4k 负例：`tasks.md` 被删除 / `git mv` 迁走（后版取不到）⇒ 失鲜
- [x] 4.4l 负例：仅 `chmod` / regular↔symlink（blob 内容完全相同）⇒ 失鲜（状态位资格）
- [x] 4.4m 负例：merge 提交内触及 `tasks.md` ⇒ 与**每个** parent 归一化等值才豁免，否则失鲜
- [x] 4.4n 真值表：`精确 / 变体 / 空 / 普通 subject` × `纯勾选 / 语义改动` 共 8 格，逐格锁定优先级（subject 精确匹配 MUST 在读 blob 前短路）
- [x] 4.4o 负例：非 UTF-8 字节 ⇒ 不得被解码替换吞掉差异
- [x] 4.4p 回归锁定：code 域 JSON 的 `freshness` 取值不因 P1 结构化返回而变
- [x] 4.5 回归：既有豁免用例全绿（`test_impl_review_exempt_bare_and_colon` / `test_impl_review_evil_suffix_stale` / `test_impl_review_fix_variant_stale` / `test_interleaved_impl_review_and_normal_stale`）
- [x] 4.6 新增：失鲜 reason 含触发文件路径与处置提示的断言
- [x] 4.7 **变异验证**（PV 规则 5，每道新守护须证「删掉会红」）：删 1.1 内容判据 ⇒ 4.1 红；删 1.1 的监视集限定（改按整 commit 求值）⇒ **4.4e 红**；删归一化锚定（改无锚定子串替换）⇒ 4.4f/4.4g 红；删 fence 感知 ⇒ 4.4f 红；改位置对齐为 LCS ⇒ 4.4i 红；删 1.1c 的 rc 检查（回落 `run_git` 空串）⇒ 需构造双侧失败用例转红；删状态位资格 ⇒ 4.4l 红；删 2.1 reason 增强 ⇒ 4.6 红
- [x] 4.8 跑全套件确认无新增 failure / warning

### 测试覆盖图〔TG-18〕

```
                      is_stale(scope="design")
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   subject 豁免面          路径成员面            reason 输出面
        │                      │                      │
   4.5 回归 ×4        ┌────────┼────────┐         4.6 断言
  （既有锚不动）       │        │        │              │
                    4.1     4.2      4.3/4.4          │
                 plan 在   plan 无   邻近路径          │
                 tasks.md  tasks.md  未误伤            │
                 不失鲜     失鲜       失鲜             │
                    └────────┴────────┴───────────────┘
                               │
                        4.7 变异验证（删守护 ⇒ 转红）
```

## 5. 收尾

- [x] 5.1 面治扫描：`DESIGN_WATCHED_NAMES` 上是否还有其他「零设计信息量」的成员形态未被审视（一次扫全，不只补 `tasks.md` 一点）
- [x] 5.2 hand-off 声明生效条件：消费仓需 `/sdflow-upgrade` 后才拿到修复
