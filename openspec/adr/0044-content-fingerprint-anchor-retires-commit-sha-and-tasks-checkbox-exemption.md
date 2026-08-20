# 内容指纹锚取代 commit-sha 把手；tasks.md 移出监视集，勾选框豁免层整体退役

`ship_gate.py` 的失鲜判定（`adr/0026`）录的锚是「被批准盘面的 commit sha」——一个**取物的把手**，
不是内容本身：`is_stale` 拿到锚后还要再对该 sha 跑一次 `git ls-tree`（design 域）或直接把它当
git ref 解析（`_read_anchor` 前身 `read_reviewed_sha` 的 `cat-file -e <sha>^{commit}` 语义级
校验）才谈得上"和 HEAD 比"。这个把手带来两条本可避免的复杂度：① `tasks.md` 仍需留在监视集内、
靠一层约 140 行的手搓 CommonMark 豁免层（`_normalize_checkbox_lines` + fence/缩进/HTML 注释
三道超集闸门）把「纯勾选框翻转」从「照判失鲜」里摘出来——该豁免层自身已登记基准 5 警号
（T189：黑名单式归一化，靠"数得完的形状"硬撑，本该反转为白名单）；② `checkpoint(impl-review)`
尾流合法修订虽已随 design 域换成 ls-tree 内容映射比较不再有 subject 豁免，但锚仍是把手、
gate 仍需在归档 34 份存量报告与新报告间做格式二态兼容（40-hex ⇔ 更长格式）没有干净路径。

**决策**：把锚从「commit-sha 把手」直接改为「监视域内容本身的密码学摘要」：

1. **D2 — `tasks.md` 移出 design 域监视集**：监视集收窄为 `proposal.md`/`design.md`/`specs/`。
   `tasks.md` 记录的是实现计划勾选状态，写入方是 agent 自由行为、非 SKILL 契约（`adr/0026`
   已论证按阶段切豁免会误伤正常勾选）；移出监视集后该文件的任何改动（含措辞、非勾选框差异）
   都不再影响 design 域新鲜度——**豁免不再需要"识别勾选框翻转"这个能力**，`_normalize_checkbox_lines`
   / `_tasks_content_exempt` / `HtmlCommentTracker` / `indent_columns` / `is_indented_code_line`
   / `CHECKBOX_BYTES_RE` / `read_blob_bytes` 整簇随之退役并物理删除（无 test-referenced 孤儿）。
2. **D3 — 锚 = manifest + digest 双字段互锁**：报告 frontmatter 落 `reviewed_sha`（监视域
   `path → (mode, type, oid)` 规范记录清单的 sha256，64 位 hex）+ `reviewed_manifest`（该
   manifest 规范字节流的单行 base64）。等值判定只走 digest 比较（HEAD 侧重算 vs 锚值）；
   诊断走 manifest（差集点名路径 + `git log -1` 点名提交）。manifest 编码字节保真（`ls-tree -z`
   原始 path 字节、按原始字节序排序），round-trip 对 Tab/换行/非 UTF-8 路径/CRLF 内容无损。
   **锚不再解析为任何 git 对象**——`read_reviewed_sha` 原有的 `cat-file -e <sha>^{commit}`
   语义级校验、以及六类诊断中的 `anchor-unresolvable` 分类整体删除（五类：git 不可用/超时/
   锚缺失/锚非法/读取失败）。
3. **DT-1 校验分层，防归档 SHIPPED 回归**：`FIELD_VALIDATORS["reviewed_sha"]` 放宽为纯语法
   校验「40 或 64 位小写 hex」（40-hex 兼容归档 34 份存量报告的历史锚值，解析核不为归档/live
   两态分叉）；64-hex 与 manifest 互证的语义强制上移至 live 读点 `_read_anchor`——40-hex 在
   live 侧判 `ANCHOR_INVALID`（需重跑写锚脚本），归档读点 `archived_verify_state` 只消费
   `verify` 结论，不touch `reviewed_sha`，故 34 份存量报告不受影响。
4. **D9 — `checkpoint(impl-review)` 豁免通道改 producer 侧重锚协议**：gate 端不保留任何
   基于 commit subject 的豁免（该通道已在更早的 `impl-review-fix` change 里随 design 域整体
   换成内容映射比较而删除，本 change 只是补上 spec 文本的死文字清理）；`sdflow-code-review`
   **新建**（非"补"，现无既有协议）尾流修订重锚段——touch 到 design 域监视集的
   `checkpoint(impl-review)` 提交落盘后，跑写锚脚本刷新锚（不动 `design_approved` 结论字段）。
5. **DT-3 — 新增权威写锚脚本 `sdflow-ship/scripts/anchor_writeback.py`**：`import ship_gate`
   复用同一份 `fingerprint_entries` 实现（物理同源，杜绝读写两端口径漂移），支持
   `--set field=value` 同批写入结论字段（producer MUST NOT 先写结论再补锚），对空监视域 /
   枚举失败 / 监视集存在未提交改动一律 fail-loud 拒写（脏树守卫，逃生口 `--allow-dirty` 仅供
   显式越权）。三个产出方 SKILL 的回写步骤改调此脚本，**MUST NOT 手写/手抄锚值**。

## Considered Options

- **内容 manifest+digest 双字段互锁（选中）**：锚即内容摘要本身，`is_stale` 退化为一次 digest
  相等性判断（design/code 两域同构），不再需要把锚当 git ref 二次解析；`tasks.md` 的豁免需求
  随监视集收窄一并消失，无需再维护一层手搓 CommonMark 归一化器（基准 5 直接命中：黑名单式
  归一化本就不该长期存在）。校验分层保证对存量归档报告零回归。
- **继续用 commit-sha 锚 + 收窄 `tasks.md` 监视集（未选）**：能消掉 `_tasks_content_exempt`
  这一层，但锚仍是把手——`read_reviewed_sha` 的语义级 git 对象解析、`ls_tree_map(root, sha, …)`
  这类"把锚值喂给 git 命令当 ref"的调用点原样保留，物理同源的写锚脚本也做不出来（写锚脚本
  没有能力"制造"一个可解析的 commit——它只能在事后指认某个已存在的 commit，与"脚本权威计算
  锚值"的设计意图相悖）。
- **锚保持 commit-sha、`tasks.md` 豁免层继续维护、只砍 subject 豁免的 spec 死文字（未选）**：
  最小改动，但把 T189 登记的基准 5 违规继续背下去，且归档兼容与内容锚的诊断精度两头都没改善；
  不满足本 change 的目标态（消灭手搓归一化器 + 消灭把手语义）。
