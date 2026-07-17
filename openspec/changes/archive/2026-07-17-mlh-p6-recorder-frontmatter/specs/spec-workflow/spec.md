## ADDED Requirements

<!-- REQ: SW-RI-1 -->
### Requirement: recorder frontmatter 索引与 legacy overlay dual-read

issues recorder（`buglist.py` / `todolist.py` / `issues.py`）SHALL 以 versioned `sdflow-issues` frontmatter namespace 作为新写机器索引的唯一真相源；索引 SHALL 保存 `module/summary/status/time/change/batch` 及 bug 专属 `priority` 或 todo 专属 `type`，并以 file-level `schema/pool/mode` 声明版本、池类型与 `canonical|overlay` 模式。frontmatter SHALL 使用文档化的 YAML-compatible 严格子集：`items` 下每个 canonical ID 对应一个单行 JSON object，使字符串中的 ASCII `|`、换行与 Unicode 由 JSON 无损转义；recorder MUST NOT 为这些索引字段继续写 Markdown 总览表 row，也 MUST NOT 因 `|`/换行拒绝合法值。

`[grill-amendment]` 所有索引 string SHALL 只含 Unicode scalar values，孤立 surrogate `U+D800..U+DFFF` 在任何写盘前按 ID+field 拒绝。renderer SHALL 使用 `ensure_ascii=False` 保留普通 Unicode，并把 U+0085/U+2028/U+2029 定向写成 JSON `\u0085`/`\u2028`/`\u2029`；CR/LF/tab/C0 由 stdlib JSON escaping。parser SHALL 拒绝 recorder 子树中的 raw NEL/LS/PS，接受其 escaped form 并还原原 code point。实现 MUST NOT 做 Unicode normalization，逐字段 round-trip SHALL 保持原 code points。

`[grill-amendment]` v1 renderer SHALL 产生唯一 canonical bytes：顶层键顺序 `schema,pool,mode,items`；item 按 `(ASCII prefix, decimal integer)` semantic key 排序；bug object 字段顺序 `module,summary,priority,status,time,change,batch`，todo 为 `module,summary,type,status,time,change,batch`，所有字段显式存在。`change/batch` 无值只允许 JSON `null`；writer SHALL 把输入 `""` 规范化为 null，reader SHALL 拒绝 frontmatter 中非 canonical 空字符串。`module/summary` SHALL 至少含一个非-whitespace scalar，但 MUST 保留原始前后空白/code points。空 map 只允许 `items: {}`，裸 `items:` 非法。reader MAY 接受 item 任意物理顺序，writer mutation SHALL 在自有 namespace 内 semantic-sort；render→render 必须 byte-identical。

`[grill-amendment]` 仅位于 byte 0 或紧随 UTF-8 BOM、且 opener/closer `---` 各自独占一行的 frontmatter block SHALL 是共享 envelope；正文中后续 `---` MUST NOT 被扫描或提升为 envelope。recorder SHALL 只拥有唯一的顶层 `sdflow-issues` 子树，内部键保持 `schema/pool/mode/items`，MUST NOT 展平为多个 `sdflow-issues-*` 顶层键，也 MUST NOT 接管共享 `sdflow` 父树或整个 envelope。reader SHALL 把 namespace 外内容视为其它 producer 所有的 opaque bytes；writer SHALL 以 byte-level splice 只插入/替换 recorder 子树，并逐字节保留其它顶层条目、注释、空行、顺序、标量样式、BOM、既有 EOL 及 frontmatter 外正文。重复 namespace、namespace 拼写/边界有歧义或窄 scanner 无法安全定位时 SHALL fail-closed，且原文件不得改变。

`[spec-review-amendment]` shared envelope v1 SHALL 只接受如下 lexical profile：每个顶层 entry 以 column 0 的无引号 ASCII key `[A-Za-z0-9][A-Za-z0-9_-]*:` 开始；同一物理行可带 value/comment，后续 value bytes 只能为空行、column-0 comment 或至少一个 ASCII space 缩进的 continuation，tab 禁止。column-0 空行/comment 是 producer-neutral separator，不属于 recorder span；recorder 自有子树内部则必须是无空行/comment 的 canonical form。entry span 在下一条合法 column-0 entry 或 closer 前结束。外部 entry 的 indented block/quoted scalar 与多行 flow value MAY 作为 opaque bytes 跳过；顶层 quoted/explicit/complex key、sequence、directive、`...`、未缩进 continuation、回到 column 0 的 flow continuation、tab或其它无法按该 profile 分段的构造 SHALL fail-closed。形似 quoted/explicit `sdflow-issues` 或 key/colon 变体 SHALL 作为 ownership ambiguity 拒绝，不得按 namespace absent 回退 legacy。

已有 envelope 的 recorder 子树 SHALL 沿用 opener 的 LF/CRLF；无 envelope 的 legacy 文件 SHALL 在 BOM 后或 byte 0 插入，并沿用正文首个 LF/CRLF，无 EOL 时使用 LF；新建 canonical 文件 SHALL 使用 UTF-8、无 BOM、LF。UTF-16 BOM、非法 UTF-8、lone CR、delimiter 缺失换行或无法安全判定 EOL SHALL fail-closed，MUST NOT 通过普通 text-mode round-trip 规范化整篇文件。

`[grill-amendment]` dated recorder 文件 SHALL 使用专用 bytes pipeline：一次 binary read 产生 raw bytes，document parser 从中返回 model、byte spans 与 EOL，namespace renderer 返回 bytes，最终由 `atomic_write_bytes` 同目录临时写 + mode bits 对齐 + `os.replace`。实现 MUST NOT 为保真先 text-read 再 binary reread，也 MUST NOT decode/encode namespace 外全文。完全生成的 INDEX/batches MAY 继续使用 text `atomic_write`。内容保真不承诺 inode、mtime、xattr 或 ACL 保留。

reader SHALL 只认文件起点成立的 frontmatter block：`sdflow-issues` namespace 缺失时读 legacy Markdown 表；namespace 存在时 MUST 严格校验 schema、pool、mode、缩进、重复键、ID、字段集合/类型与枚举。namespace 在场但任一校验失败 SHALL fail-closed 非零退出并点名文件/reason，MUST NOT 回退 legacy 表。`[grill-amendment]` mode 必须与 recorder legacy 状态总览区域互证：canonical 要求区域计数=0，overlay 要求=1；namespace 缺失的 legacy 也要求=1。区域缺失/重复或 mode mismatch 是 fatal，不得自动修 mode/删表/隐藏 items。验证通过后 `mode=canonical` SHALL 只以 frontmatter items 为索引；`mode=overlay` SHALL 按 semantic ID 合并同文件 legacy rows 与 frontmatter items，同 semantic ID 时 frontmatter 是唯一当前值，legacy row 仅作不可写 snapshot。`[spec-review-amendment]` relation validation SHALL 按 effective owner 分区：frontmatter-owned ID 只过 strict schema/canonical marker 规则，不进入 legacy 表↔块/status 检查；未 promotion legacy ID 继续旧规则；marker ownership 冲突、marker-only legacy、同 semantic key 多个 frontmatter key及跨文件/跨 pool 重复均 fatal。overlay 区域内 row arity 问题仍走既有 problems 分层。跨文件/跨 pool 重复 ID仍为错误。

新格式 prose 块 SHALL 只承载人读详情与 append-only 变更历史，MUST NOT 再复制 `status/batch` 等可变机器状态。历史表与历史属性表 MUST NOT 被任何新 writer 修改；对 legacy item 的 mutation SHALL 把完整当前索引提升进同文件 overlay，再更新 overlay。`[grill-amendment]` canonical/overlay 新 block SHALL 由独占行 `<!-- sdflow-issue-block:start id={canonical-id} -->` / `<!-- sdflow-issue-block:end id={canonical-id} -->` 成对定界；marker 必须同 ID、不可嵌套、每 ID 至多一块。新格式 reader MUST 只按 marker 定位 block，MUST NOT 回退 heading/`---` heuristic；后者只服务 legacy block。精确 marker 独占行是保留语法，renderer SHALL HTML-escape 用户 prose 中的同形行，其它 heading/separator/fence SHALL 作为普通 prose。`[spec-review-amendment]` promotion 在任何写盘前 SHALL 扫描待包裹 legacy block；内部已有任一精确 marker grammar 独占行时必须 fail-closed 并报告 block/line，MUST NOT 原样保留后再包外围 marker而制造嵌套/错配盘面。

`[spec-review-amendment]` producer `scan --json` 与 `issues.py` consumer 的 envelope 是稳定 fail-closed contract：bug 输出必须有 list `bugs` + list `problems`，todo 必须有 list `items` + list `problems`；item 必须包含对应 pool 全部 index fields 以及 string `id/file`，字段类型/枚举与本 schema 一致。坏 JSON、缺键、错误类型或缺 `file` SHALL non-zero，且既有 INDEX/batches 不变；consumer MUST NOT 以缺键默认 `[]`。

`[spec-review-amendment]` 本 change 新增的 fatal diagnostics SHALL 统一写 stderr，保持 JSON stdout 无污染，并采用可断言三段式 `ERROR: <problem>; cause: <cause>; fix: <action>`；涉及文件/ID/field/lock/rename stage 时必须带对应定位，fix 必须给可复制的重试/恢复动作。该文本格式不新增 machine error-code/diagnostic JSON API。

block heading SHALL 保持 `## {canonical-id}: {display-title}`，但不参与 identity；显式 `title` 必须通过拒绝 CR/LF/NUL 的窄 line-safety，缺省 display title 则由 `summary` 连续空白折叠成一个 ASCII space 后确定性派生。完整 summary SHALL 逐物理行加 `> ` 前缀作为新建 block 的 blockquote 人读投影，MUST NOT 从 prose 反解析成机器状态；promotion 包裹既有 block 时 MUST NOT 为补投影而改写其内部。bug 新 item SHALL 建 marker block；todo 轻量 item MAY 无 block，首次追加历史时 SHALL 建 marker-framed minimal block。写入其它 Markdown 单行结构位的 source/project/history note 仍 MUST 经窄 line-safety 校验或等价安全渲染；`batches.md` 的 batch key slug 契约（拒空白、首尾空白、`|`、换行、` — `）保持不变。

#### Scenario: 新 canonical 文件无损写入特殊字符
- **WHEN** 在不存在的目标 dated 文件中新增 item，且 `module` 或 `summary` 含 ASCII `|`、换行与 Unicode
- **THEN** recorder 创建 `mode=canonical` 的 v1 frontmatter，将 item 仅写入 `items`，随后 `scan --json` 逐字段返回原值；`[grill-amendment]` 若该 pool/payload 建立 prose block，则 heading 使用单行 display title、完整 summary 以逐行 blockquote 展示；todo 轻量项无 block 仍合法；文件中 MUST NOT 出现该 item 的 Markdown 总览表 row，也 MUST NOT 触发旧 table-cell reject

#### Scenario: YAML line-break code point 定向转义 `[grill-amendment]`
- **WHEN** 任一索引 string 含 U+0085、U+2028 或 U+2029
- **THEN** frontmatter item 物理上仍为单行，对应 code point 以 `\u0085`/`\u2028`/`\u2029` 出现；scan JSON 还原原字符且不做 normalization

#### Scenario: raw line separator 与孤立 surrogate fail-closed `[grill-amendment]`
- **WHEN** recorder 子树含 raw NEL/LS/PS，或 add/overlay promotion 的任一 string 经 JSON escape 输入后包含孤立 surrogate
- **THEN** parse/render 在业务写盘前非零失败，stderr 含文件或 ID+field+code point；MUST NOT 等到 UTF-8 encode 才抛无定位异常

#### Scenario: item permutation 收敛为唯一 bytes `[grill-amendment]`
- **WHEN** 两个语义相同 model 以不同插入顺序包含 `A10/A2/B1`，或 reader 读到手工乱序 namespace 后执行合法 mutation
- **THEN** renderer 都按 `A2,A10,B1` 输出相同 bytes，object 字段按 pool 固定顺序；第二次 render 不再产生 diff

#### Scenario: optional null 与 empty map canonical form `[grill-amendment]`
- **WHEN** writer 输入 change/batch 空串或 model items 为空
- **THEN** 输出分别为 JSON `null` 与 `items: {}`；reader 遇到 frontmatter `change:""`、`batch:""` 或裸 `items:` 时 fail-closed 并点名字段

#### Scenario: required prose index string 不是空白壳 `[grill-amendment]`
- **WHEN** module 或 summary 只含 spaces/tabs/newlines，但类型仍为 string
- **THEN** writer/reader 以 required-nonblank 错误拒绝；若至少有一个非-whitespace scalar，则保留原始前后空白且 round-trip 不 trim

#### Scenario: 多行 summary 不能注入 prose block `[grill-amendment]`
- **WHEN** 未提供显式 `title`，且 summary 含换行、空白序列、`## B999: fake`、`---` 与 `|`
- **THEN** heading 中只出现空白折叠后的单行 display title；完整 summary 的每个物理行都带 blockquote 前缀，新格式 block parser 只认成对 marker 并仍只发现真实 item ID，`scan --json` 返回原始 summary

#### Scenario: 显式 title 仍受单行结构约束 `[grill-amendment]`
- **WHEN** payload 显式提供含 CR、LF 或 NUL 的 `title`
- **THEN** add 在任何文件创建或写入前非零拒绝；合法单行 title 可含 `|`，且只作为 display title、不进入 frontmatter 机器索引

#### Scenario: 向 legacy dated 文件新增 item
- **WHEN** 当前日/月 dated 文件只有 legacy Markdown 表，升级后的 recorder 新增一个 item
- **THEN** recorder 在同文件首部建立 `mode=overlay` 并把新 item 写入 frontmatter，同时追加其 prose 块；原表逐字节不变且无该新 item 行，dual-read 返回 legacy rows 与新 item 的并集

#### Scenario: legacy item mutation 提升为 overlay
- **WHEN** `set-status`、`triage` 或 `batch rename` 更新一个只存在于 legacy 表的未终态 item
- **THEN** writer 从 legacy row 构造完整 v1 item 写入同文件 overlay；`[grill-amendment]` 唯一可判的既有 block 只在外围插入同 ID marker，内部 bytes、legacy row 与属性表保持原样，再施加更新并把状态历史追加到 end marker 前；reader 对同 ID 只返回 overlay 当前值

#### Scenario: legacy block 预存 marker 时 promotion 拒绝 `[spec-review-amendment]`
- **WHEN** 唯一可判的 legacy block 内已含任一精确 `sdflow-issue-block:start/end` 独占行
- **THEN** promotion 在 frontmatter/外围 marker/历史任一写盘前 fail-closed，stderr 点名 file/legacy ID/line 与 marker collision；原文件逐字节不变，MUST NOT 通过再包一层制造嵌套或错配 marker

#### Scenario: promotion 后不再依赖 legacy block heuristic `[grill-amendment]`
- **WHEN** 某 legacy item 已成功 promotion 并原位套 marker，随后再次执行 status/triage mutation
- **THEN** writer 只用成对 marker 定位和追加，不再按 heading/`---` 搜索该 item；marker 内原 legacy prose 可自由含这些文本

#### Scenario: legacy block 无法安全包裹 `[grill-amendment]`
- **WHEN** 待 promotion 的 bug 缺 prose block、同 ID 有多个候选块或 legacy heuristic 无法唯一确定边界
- **THEN** mutation 在 frontmatter/marker/历史任一写盘前 fail-closed 并列出 evidence；MUST NOT 猜边界或另建同 ID continuation block

#### Scenario: 无 block legacy todo promotion `[grill-amendment]`
- **WHEN** 待 promotion 的 legacy todo 合法地没有详情块，且 mutation 需要追加历史
- **THEN** writer 写入 overlay item 并创建唯一 marker-framed minimal block；不得制造第二个无 marker 同 ID block

#### Scenario: namespace 在场但损坏不回退
- **WHEN** 文件首块含 `sdflow-issues`，但出现未知 schema、pool/path 不符、非法 mode、tab/缩进错误、重复 ID/JSON key、缺字段、类型或枚举越域任一情况
- **THEN** `scan` 与依赖它的 reindex/mutation MUST 非零失败并在 stderr 点名文件与 reason，MUST NOT 回退表格或挑最后一个重复值继续

#### Scenario: canonical 声明不能隐藏 legacy 表 `[grill-amendment]`
- **WHEN** namespace 声明 `mode=canonical`，但文档仍能定位 recorder legacy 状态总览区域
- **THEN** scan/mutation 以 mode-structure mismatch fatal，报告声明 mode 与区域计数；MUST NOT 忽略旧表后返回较少 items

#### Scenario: overlay 必须有唯一 legacy 总览区域 `[grill-amendment]`
- **WHEN** namespace 声明 `mode=overlay`，但 legacy 状态总览区域缺失或重复
- **THEN** scan/mutation fatal 且不自动改成 canonical或挑一个区域；若区域唯一但内部有坏 row，坏 row 仍按 legacy arity problem 处理

#### Scenario: 无 recorder namespace 的历史文件继续可读
- **WHEN** dated 文件无 frontmatter，或首块只有与 recorder 无关的其它 namespace，且含合法 legacy 总览表
- **THEN** reader 按 legacy parser 返回与升级前相同的 item 字段；不得把无关 frontmatter 当损坏的 recorder namespace

#### Scenario: 向共享 envelope 注入 recorder namespace `[grill-amendment]`
- **WHEN** legacy dated 文件的首个 frontmatter 已含其它工具的键、注释、空行或 block scalar，但不含 `sdflow-issues`
- **THEN** writer 在同一 envelope 插入唯一顶层 `sdflow-issues` overlay；namespace 外 frontmatter 与 Markdown 正文逐字节不变，随后 reader 合并 overlay 与 legacy rows

#### Scenario: shared envelope lexical profile 接受与拒绝 `[spec-review-amendment]`
- **WHEN** 外部 namespace 使用合法 column-0 ASCII key，value 由 same-line bytes 或 space-indented block/quoted/flow continuation 组成
- **THEN** scanner 以 byte span 跳过并原样保留；若改为 quoted/explicit/complex top-level key、top-level sequence/directive、tab、未缩进 continuation或 column-0 multiline flow continuation，则 scan/mutation fail-closed 并点名 lexical category，原 bytes 不变

#### Scenario: BOM 与 CRLF 在 namespace splice 外保真 `[grill-amendment]`
- **WHEN** dated 文件以 UTF-8 BOM + CRLF frontmatter 开头，外部 namespace、正文及末尾换行含可识别的 byte fixture
- **THEN** recorder mutation 只改变 `sdflow-issues` byte range，新子树使用 CRLF；BOM 与所有 range 外 bytes 完全相同

#### Scenario: dated 文件单次 binary I/O `[grill-amendment]`
- **WHEN** scan 或 mutation 处理一个含共享 envelope 的 dated 文件
- **THEN** instrumentation 显示该文件只被 binary read 一次，parser/renderer 以 byte spans 复用该 buffer；不存在 text-mode read、二次保真 reread或 namespace 外全文 re-encode

#### Scenario: bytes atomic replace 保留 mode bits `[grill-amendment]`
- **WHEN** `atomic_write_bytes` 更新一个既有 0640 dated 文件，或首次创建新文件
- **THEN** replace 后既有文件仍为 0640、新文件为 0644；注入 write/chmod/replace 异常时旧 bytes/mode 不变且临时文件按既有清理契约处理

#### Scenario: 正文分隔线不是 frontmatter `[grill-amendment]`
- **WHEN** 文件 byte 0 不是 `---`，但正文稍后出现独占行 `---` 及形似 `sdflow-issues:` 的 prose
- **THEN** reader 不把该段识别为 envelope；若文件有合法 legacy table 则按 legacy 读取，writer 需要 overlay 时只在 byte 0 或 BOM 后新增真正 envelope

#### Scenario: 不支持的编码或 EOL fail-closed `[grill-amendment]`
- **WHEN** 文件含 UTF-16 BOM、非法 UTF-8、lone CR、frontmatter delimiter 无行终止或无法安全判定 EOL
- **THEN** scan/mutation 非零并报告 encoding/EOL reason；mutation 前后原始 bytes 完全一致

#### Scenario: 更新 recorder 子树不改写相邻 namespace `[grill-amendment]`
- **WHEN** canonical/overlay 文件的共享 envelope 同时含 `sdflow-issues` 与其它顶层 namespace，且 recorder mutation 成功
- **THEN** writer 只替换 `sdflow-issues` 子树；比较写前写后时，子树外 byte ranges 完全相同

#### Scenario: namespace 所有权或 splice 边界有歧义 `[grill-amendment]`
- **WHEN** 首个 envelope 含重复 `sdflow-issues`、非标准拼写造成同名歧义，或使用窄 scanner 无法无歧义界定的结构
- **THEN** reader/mutation 非零失败并报告文件与 reason；mutation MUST NOT 重写、规范化或截断该文件

#### Scenario: overlay shadow 不算重复 ID
- **WHEN** `mode=overlay` 文件的 frontmatter 与同文件 legacy 表都有 ID `T85`
- **THEN** reader 以 frontmatter `T85` 为当前值且不报告重复；若另一个 dated 文件也出现语义相同 ID，则仍 MUST 报跨文件重复

#### Scenario: overlay relation validation 按 owner 分区 `[spec-review-amendment]`
- **WHEN** overlay 含 frontmatter-only bug + canonical marker block，另有未 promotion legacy item + legacy block
- **THEN** 前者只做 frontmatter/marker relation，MUST NOT 因 legacy table 无该 literal ID 误报“块有 ID 但表无行”；后者继续 legacy 表↔块/status 检查；同一 marker 被两个 semantic owner 认领则 fatal

#### Scenario: 新 prose 不再复制可变状态
- **WHEN** 新格式 item 经 `set-status` 或 `triage` 更新
- **THEN** writer 只更新 frontmatter 索引并按需追加人读历史，不搜索/改写 prose 中的状态或批次副本；scan 的当前状态只来自索引

#### Scenario: 自由 prose 不制造新格式 block boundary `[grill-amendment]`
- **WHEN** phenomenon/rootcause/fix/impact/motivation/approach/note/optional 或人工 prose 含独占行 `---`、`## B12: fake` 与 fenced code
- **THEN** 新格式 parser 只按外围成对 marker 确定原 block，以上内容不截断或新增 block；若用户内容含精确 marker grammar 的独占行，renderer 将其 HTML-escape

#### Scenario: marker 损坏可观察且不回退 `[grill-amendment]`
- **WHEN** canonical/overlay prose 出现 marker 缺对、start/end ID 不同、嵌套或同 ID 重复 block
- **THEN** scan 产生带文件/ID/reason 的 problem，`reindex --strict` 非零；reader MUST NOT 用 heading heuristic 猜测修复边界

#### Scenario: todo 轻量项首次创建历史 block `[grill-amendment]`
- **WHEN** canonical todo item 起初没有 prose block，随后 `set-status` 需要追加历史
- **THEN** writer 创建成对 marker 的 minimal block 后追加历史；缺块在此前不算 problem，bug 新 item 缺 marker block 仍算 problem

#### Scenario: scan JSON consumer protocol 损坏 fail-closed `[spec-review-amendment]`
- **WHEN** recorder 子进程返回坏 JSON、缺 `bugs|items`/`problems`、任一键非 list，或 item 缺 `id/file`/pool 必需字段
- **THEN** `issues.py` 在生成/覆盖 INDEX/batches 前非零失败，stderr 点名 producer + key/type；MUST NOT 将缺键解释为空池或产生数据视图丢失

<!-- REQ: SW-RI-2 -->
### Requirement: recorder ID 语义唯一与仓级并发写安全

`[grill-amendment]` `[spec-review-amendment]` bug/todo 新写 ID SHALL 统一符合 ASCII `[A-Z][1-9][0-9]*`，默认 prefix 分别为 `B`/`T`，公开的自定义 `--prefix` 保持兼容且只接受一个 ASCII 大写字母。matcher MUST 使用 ASCII 字符类/`re.ASCII`，不得让 `\d` 接受 Arabic-Indic、fullwidth 或其它 Unicode decimal digit。ID 的语义身份由 ASCII 大写 prefix + 十进制数字值决定，不包含 pool；reader MUST 把 `A007`/`A7` 等同号异形视作冲突并 fail-closed，writer MUST 只接受 canonical spelling。ID SHALL 在 bug+todo 两池仓级全局唯一；显式 ID 查重、自动 max+1 分配与 `next-id --prefix X` 的计算 MUST 在同一个 snapshot lock 内读取两池全集，MUST NOT 只扫当前 pool。`next-id` 命令只提供 advisory 值，不构成 reservation。

`[spec-review-amendment]` legacy reader MAY 保留孤立 ASCII raw spelling `A007` 作为定位 alias；mutation 仅在同文件确有该 raw legacy row 且 semantic key 唯一时接受该 alias。promotion SHALL 写 canonical frontmatter key/marker `A7`，overlay shadow 按 semantic key，成功 mutation 与后续 scan 返回 canonical ID；未触碰 pure-legacy scan 仍返回 raw ID。无 raw legacy alias 的非 canonical 用户输入必须拒绝。

所有会形成权威仓级 snapshot 或修改 dated 文件、`issues/INDEX.md`、`issues/batches.md` 的 recorder 命令 MUST 以 `O_CREAT|O_EXCL` 获取仓级 exclusive snapshot lock `openspec/issues/.recorder.lock`。`[spec-review-amendment]` 除 pure argument validation 与 `repo_root` 解析外，owner 必须在任何影响结果的 discovery/glob/list/exists/stat/open 前 acquire，participant 必须先校验 token；只读命令 SHALL 持有到全部输入已发现、读取、解析、校验并固化成不再访问文件的内存 snapshot，随后先释放再格式化/输出；mutation SHALL 持有到最后一次原子替换完成。两类命令均在正常/异常退出的 `finally` 路径释放。至少包含 bug/todo `scan`、`next-id`、add/set-status/triage，以及 issues reindex/sweep、`batch lint/add/set-status/rename`。锁内容 SHALL 记录 repo、PID、命令、开始时间与高熵 capability token。锁冲突 MUST 在任何业务 snapshot/写盘前立即非零失败并显示 owner，但 MUST NOT 显示 token；实现 MUST NOT 等待、自动按 TTL 偷锁或忽略冲突。目标文件落盘 MUST 继续使用同目录唯一临时文件 + `os.replace`，写前异常不得改变旧文件。

`[grill-amendment]` lock 只提供 cooperative isolation，MUST NOT 声称可阻止不遵守协议的编辑器/脚本/Git 修改。`sdflow-init` SHALL 以 `sdflow-init/assets/snippets/runtime-gitignore.txt` 为 canonical source，并由 `init.py::run()` 的 init/update 两路调用 planned `merge_runtime_gitignore()`，向消费仓根 `.gitignore` 幂等合并 `/openspec/issues/.recorder.lock`；已有一条时 byte-noop，缺项时仅追加完整行，重复条目时 fail-closed 不擅删用户内容，其它 ignore bytes 必须保留。本仓 `.gitignore` SHALL 同步 dogfood。当前不存在的 canonical ignore 资产与 merge path 必须由本 change 新增。

`[spec-review-amendment]` guarantee matrix SHALL 明示：macOS/Linux 本地 filesystem 是自动 release gate，mode bits 只在 POSIX 保证；Windows 本地 filesystem 是必须执行 smoke 的兼容目标，sharing violation 等失败须 non-zero 且旧文件不变；NFS/SMB/FUSE 等 network/userspace filesystem unsupported。`os.replace` 只承诺本地文件系统上的 process exception/crash 边界；未执行完整 file+directory fsync protocol，power-loss durability 非本 change 承诺。

`[grill-amendment]` 顶层 snapshot/mutating CLI SHALL 是唯一 lock owner；它启动的 recorder 子进程 SHALL 通过专用环境变量接收 token，只有在 token 与当前锁文件匹配时才作为 participant 进入同一锁域。participant MUST NOT 再次 acquire 或 release；`[spec-review-amendment]` 已验证 participant 仅可向 allowlist 内、同 repo、当前复合调用图需要的 recorder 子进程原样转发该 token，其它 subprocess env 必须剥离 token；缺失/不匹配、跨 repo、非 allowlist 或越级委派均不得进入 participant core。非 owner 直接调用仍须正常竞争锁或 fail-closed，MUST NOT 绕过互斥。owner 释放前 MUST 对当前路径 identity 与 token 作 best-effort 终检，只能删除仍观察为自己的锁；普通 path API 无 compare-and-unlink，终检后的外部替换 race 明确不在 cooperative 保证内。`O_EXCL` 创建成功后即视为 occupied；竞争者读到空白/部分 metadata 时仍须失败，不得据此偷锁。独立 reader MUST 真正 acquire；仅在读取前后检查 lock 是否存在不满足 snapshot 隔离。

`[spec-review-amendment]` 共享 envelope 的所有**合规** producer 若会 mutation 同一 dated document，MUST 加入同一 `.recorder.lock` document lock protocol，即使它不拥有 `sdflow-issues`；所有权按 namespace 分离，mutation 协调按整文件 replace 共享。非合规外部 writer 绕锁后，recorder 不承诺以额外 reread/CAS 检出其变化；这种 lost-update race 明确属于 cooperative residual boundary，MUST NOT 用“byte splice”夸大为跨任意 producer 安全。

#### Scenario: 显式前导零 ID 被拒
- **WHEN** `add` 收到显式 `A007`，无论池中是否已存在 `A7`
- **THEN** writer 在写盘前以 canonical ID 错误拒绝；若 legacy corpus 已同时存在两种 spelling，scan MUST 报语义重复并拒绝 reindex

#### Scenario: Unicode decimal digit 不是 canonical ID `[spec-review-amendment]`
- **WHEN** reader/writer/marker 遇到 Arabic-Indic、fullwidth 或与 ASCII 混合的数字 spelling，例如 `A1٢`、`A1２`
- **THEN** 在 semantic key/int conversion 前以 non-ASCII-ID 错误拒绝，不 normalization、不与 `A12` 静默归并

#### Scenario: 孤立 legacy 前导零 ID promotion `[spec-review-amendment]`
- **WHEN** pure-legacy 文件仅有 raw `A007` 且仓内无 semantic `A7` 冲突，调用 `set-status A007`
- **THEN** raw row/旧 block bytes 保留，overlay key 与 marker 写 `A7`，成功 JSON 及后续 scan 返回 `A7`；同文件 shadow 以 semantic key 合并且不产生两个 item

#### Scenario: 自定义 prefix 保持兼容 `[grill-amendment]`
- **WHEN** bug 或 todo 调用 `next-id/add --prefix A`，且仓级两池不存在对应冲突
- **THEN** writer 分配 canonical `A<n>`，CLI/JSON shape 与默认 B/T 相同；小写、多字母或空 prefix 在业务读取/写盘前非零拒绝

#### Scenario: 自定义 ID 跨 pool 冲突 `[grill-amendment]`
- **WHEN** bug 池已存在语义 ID `A7`，todo add 尝试显式 `A7`、自动 `--prefix A` 或 legacy 中出现 `A007`
- **THEN** 显式/legacy 路径 fail-closed 并列出两池位置；自动分配在锁内跳过该 semantic key 选择下一可用 canonical ID，MUST NOT 因 pool 不同放行重复

#### Scenario: 并发 add 不产生重复或丢写
- **WHEN** 20 个进程并发向同一仓库 recorder 执行自动 ID 的 `add`
- **THEN** 同一时刻至多一个 writer 持锁；成功写入的 ID 全部唯一，冲突进程均显式非零且可重试，最终文件无 lost update、半写或重复 ID

#### Scenario: 锁冲突在读改写前失败
- **WHEN** `.recorder.lock` 已由另一写命令持有
- **THEN** 当前 mutation 在读取可变 snapshot/分配 ID/创建文件之前失败，stderr 含 lock path 与 owner PID/command/time，任何目标文件逐字节不变

#### Scenario: sweep 子进程加入父命令锁域 `[grill-amendment]`
- **WHEN** `issues.py sweep` 已持有 owner lock，并依次启动 bug/todo triage、batch add 与 reindex 子进程
- **THEN** 每个 mutating 子进程校验继承 token 后以 participant 身份执行，不发生嵌套抢锁；从 sweep 首次 scan 到最终 reindex 之间，任何外部 writer 均 fail-fast

#### Scenario: participant 受控嵌套委派 `[spec-review-amendment]`
- **WHEN** `sweep → issues reindex → bug/todo scan` 形成两层 recorder subprocess，或 participant 启动非 allowlist 外部命令
- **THEN** 内层 allowlist scan 原样校验同一 token 后加入且不自锁；外部命令环境无 token；跨 repo/伪造/越级委派在业务读取前失败

#### Scenario: 伪造或过期 participant token 被拒 `[grill-amendment]`
- **WHEN** 子进程收到缺失、过期或与当前 lock file 不一致的 participant token
- **THEN** 子进程 MUST NOT 进入锁内 mutation core；它按顶层调用正常 acquire，若锁已存在则在业务读写前失败

#### Scenario: owner 不误删替代锁 `[grill-amendment]`
- **WHEN** owner 持锁期间 lock file 被人工删除，且另一 writer 随后建立了不同 token 的新锁
- **THEN** 若替换在 release identity/token 终检前可观察，旧 owner保留新锁并显式报告 ownership lost；诊断同时声明终检与 unlink 之间的非 cooperative 替换不具备原子 compare-and-unlink 保证

#### Scenario: 竞争者撞上 metadata 初始化窗口 `[grill-amendment]`
- **WHEN** owner 已通过 `O_EXCL` 创建 lock file，但 metadata 尚为空或只写入一部分时另一 writer 竞争
- **THEN** 竞争者仍立即非零失败，可报告 metadata unavailable/initializing；MUST NOT 删除、覆盖或绕过该锁

#### Scenario: 写入异常保持旧文件
- **WHEN** render、临时文件写入或 `os.replace` 前注入异常
- **THEN** 命令非零退出，原目标文件逐字节不变，正常异常路径清理临时文件并释放本进程持有的 lock

#### Scenario: crash stale lock fail-loud
- **WHEN** writer 被不可捕获终止而遗留 `.recorder.lock`
- **THEN** 后续权威读写 MUST fail-loud，按 `ERROR: problem; cause; fix` 显示 repo/path/PID/command/start/metadata state 与可复制恢复步骤；MUST NOT 自动删除可能仍属活进程的 lock

#### Scenario: metadata 前 crash 的 break-glass `[spec-review-amendment]`
- **WHEN** owner 在 `O_EXCL` 成功后、完整 metadata 写入前 crash，留下空白或部分 lock
- **THEN** 后续命令保守拒绝并明确无法核验单一 owner；fix 要求先停止该 repo 全部 recorder owner/participants、再删除精确 lock path并重跑，MUST NOT 只凭空 metadata 猜 stale

#### Scenario: next-id 不承诺预留
- **WHEN** 调用者先执行 `next-id`，随后另一进程抢先成功 add 同一建议号码
- **THEN** `next-id` 的计算 snapshot 在持锁期间一致，但释放即失效；前一调用者的后续 add 在新锁内查重时重新自动分配或对显式冲突非零失败，MUST NOT 覆盖既有 item

#### Scenario: 独立 scan 不读取跨文件写中间态 `[grill-amendment]`
- **WHEN** batch rename owner 已改写部分 dated files 但尚未完成 registry/reindex，此时另一个独立 `scan --json` 启动
- **THEN** scan 在读取任一业务文件前因 snapshot lock 冲突非零失败；MUST NOT 返回一半 old、一半 new 的成功 JSON

#### Scenario: reader 先持锁时 writer 不穿越 `[grill-amendment]`
- **WHEN** 独立 scan 已 acquire snapshot lock 并正在读取多文件，另一 writer 启动
- **THEN** writer 在任何业务读取/写盘前 fail-fast；scan 返回的成功 snapshot 对应无 writer 穿越的锁内时点

#### Scenario: 慢输出不延长只读锁 `[grill-amendment]`
- **WHEN** scan 已完成全部读取/解析/校验并固化内存 snapshot，但 stdout consumer 阻塞其 JSON 格式化或写出
- **THEN** scan 在输出前已 token-safe release；另一命令可 acquire，且 scan 最终输出仍只来自已固化 snapshot、不再访问业务文件

#### Scenario: runtime lock ignore 幂等注入 `[grill-amendment]`
- **WHEN** `sdflow-init` 对缺少、已有或已含 recorder lock 条目的消费仓 `.gitignore` 连续执行 init/update
- **THEN** `/openspec/issues/.recorder.lock` 恰好存在一次，其它用户规则逐字节保留；持锁期间 `git status --short` 不显示该 runtime lock

#### Scenario: 平台与 durability 边界可验证 `[spec-review-amendment]`
- **WHEN** 在 POSIX local FS 跑全套、Windows local FS 跑 acquire/conflict/replace/cleanup smoke，或用户查阅 network FS/power-loss 支持说明
- **THEN** POSIX mode/atomic tests 与 Windows smoke 通过；Windows sharing failure 保留旧文件；文档明确 network FS unsupported、power-loss durability 未承诺，MUST NOT 用“跨平台原子”笼统覆盖这些层级

#### Scenario: cooperative lock 不夸大保证 `[grill-amendment]`
- **WHEN** 外部编辑器或未采用 recorder lock 的脚本在 owner 持锁时直接改写 issue 文件
- **THEN** recorder 不承诺拦截该写入；文档/诊断明确保证仅覆盖遵守协议的 CLI，并在后续 parse/validation 尽可能 fail-loud

#### Scenario: 两个 namespace producer 不互相覆盖 `[spec-review-amendment]`
- **WHEN** recorder 与另一个合规 producer 并发更新同一 dated document 的不同顶层 namespace
- **THEN** 二者竞争同一 document lock，至多一个先写、后者 acquire 后从最新 bytes 读取并保留前者更新；测试与文档同时声明绕锁 producer 的并发 replace 不在保证内

<!-- REQ: SW-RI-3 -->
### Requirement: recorder 单次解析与 batch rename snapshot 复用

`scan` SHALL 对每个 dated 文件至多执行一次文件读取与一次 document parse，并从同一 parse result 完成 frontmatter/legacy merge、ID/字段校验、block relation 与 JSON 输出；MUST NOT 为 arity、重复 ID、rows、blocks 分别重复切分同一文件。`[spec-review-amendment]` `issues.py batch rename` SHALL 由自包含 `read_rename_snapshot()` 直接对两池每个 dated 文件执行一次 binary read/parse，snapshot 携带 raw bytes/spans/model/effective items/problems；MUST NOT 先经 `scan --json` 读取后再为 retag 二次打开同一文件。retag SHALL 更新内存 model并以原 raw buffer splice，再把 updated items 传给 reindex 核心生成 INDEX/batches；整个 rename 每 dated 文件 read=1/parse=1，per-pool `scan --json`=0，reindex 不再读取两池。该约束不把多文件 rename 宣称为事务；`[grill-amendment]` rename 只有在 dated files、batch key、INDEX 与 batches 派生状态全部收敛后才可 exit 0，任一步失败均非零并允许原命令按有 provenance 的当前盘面识别阶段后重试。

`[spec-review-amendment]` recorder `scan --json` 是跨脚本 fail-closed contract：bug envelope 必须含 list `bugs` + list `problems`，todo 必须含 list `items` + list `problems`；每个 item 必须含 `id,module,summary,status,time,change,batch,file` 及 pool-specific `priority|type`，类型和值域与 schema 一致。`issues.py` 消费者遇坏 JSON、缺键、错误类型或缺 `file` 必须在写 INDEX/batches 前 non-zero，MUST NOT 以默认空 list 掩盖 partial install/protocol drift。

`[spec-review-amendment]` rename 首次执行 SHALL 先验证 old registry 存在、new 不存在且无 item 已引用未注册 new；随后原子把 registry header 改成 new，并在 target entry 写/替换 machine-owned `重命名自: old`，再 retag dated files、reindex。重试只有在 new entry 的 provenance 精确匹配 old 时才允许 old registry 缺失；该状态下全 old、old/new 混合或全 new items 都继续收敛。无匹配 provenance 的 `old missing/new exists` 必须保持未知 source 非零，MUST NOT 把误输或 orphan items 吸收成成功 rename。

#### Scenario: scan 每文件一次解析
- **WHEN** 一个 dated 文件同时包含 overlay、legacy table 与 prose blocks，运行 `scan --json`
- **THEN** instrumentation 显示该文件 open/read=1、document parse=1，输出仍完成 shadow merge、legacy arity、ID 与 block 检查

#### Scenario: batch rename 每池只扫描一次
- **WHEN** `batch rename old new` 同时命中 bug 与 todo 多个 dated 文件并成功触发 reindex
- **THEN** `issues.py` 对每个 dated 文件 binary read/parse 各一次，bug/todo `scan --json` 调用均为 0；reindex 使用 retag 后 snapshot 生成输出且 namespace 外 bytes 保真

#### Scenario: rename 中途失败可重跑收敛
- **WHEN** batch rename 在若干 dated 文件成功后、后续文件或 batches/INDEX 写入失败
- **THEN** 命令非零并点名失败位置；重跑从 dual-read 当前 snapshot 继续，把剩余 item、batch key、INDEX 与成员状态收敛一致，MUST NOT 因复用 snapshot 掩盖部分完成态，MUST NOT 在 reindex 失败时只 warning 后 exit 0

#### Scenario: batch key 已改名但派生输出未收敛 `[grill-amendment]`
- **WHEN** 重试 `batch rename old new` 时 registry 已无 `old`、已有 `new` 且 target entry 精确记录 `重命名自: old`，items 为全 old、old/new 混合或全 new
- **THEN** 命令把盘面识别为已开始的同一次 rename，retag 仍为 old 的 items 并补跑 reindex；完全收敛后 exit 0，失败仍非零

#### Scenario: retry 不静默合并冲突 batch `[grill-amendment]`
- **WHEN** `old` 与 `new` registry entry 同时存在，或 registry 仅有 `new` 但 provenance 缺失/不匹配，或首次执行前已有 item 引用未注册 new
- **THEN** 命令 fail-closed，列出 registry/provenance/item 证据，不 retag、不 merge、不写派生输出

#### Scenario: rename 的非致命 problems 不冒充写失败 `[spec-review-amendment]`
- **WHEN** rename snapshot 含与 batch retag 无关、仍可判 item 的 legacy 非致命 block/arity problem，且全部 target outputs 成功收敛
- **THEN** problem 回显 stderr但沿用默认 reindex 语义可 exit 0；任何影响 item/batch 判定的 fatal problem、dated/registry/INDEX/batches 写失败均 non-zero，MUST NOT warning-only success

## MODIFIED Requirements

<!-- REQ: SW-RI-4 -->
### Requirement: reindex 一致性问题可观测且不阻断重建

`issues.py reindex` SHALL 把子进程 `scan` 报出的 index↔block 一致性 problems **回显到 stderr**（逐条带 pool / 文件定位），使独立跑 reindex 时的不一致对用户可见。**默认**：非致命 problems（如 legacy 表 arity、孤儿/缺失 prose block）非空 MUST NOT 使 reindex 失败——INDEX SHALL 照常从所有可判 item 确定性重建、退出码为 0。reindex SHALL 提供 **`--strict`** 选项：problems 非空时以非 0 退出，供非交互调用/收尾门 enforcement。**致命错误**（文件不可读、`sdflow-issues` namespace 在场但 schema/JSON/枚举/ID 损坏、跨文件语义重复 ID）无论是否 `--strict` 均 MUST 非零退出且不得写新 INDEX/batches snapshot。

读侧盘面完整性 SHALL 按格式分流：legacy table 继续校验 8/7 列 arity；canonical/overlay 校验严格 frontmatter schema。overlay 内 frontmatter shadow 同文件 legacy ID 是合法迁移语义，不得误报重复；同一 canonical ID 出现在不同文件仍为致命冲突。reindex 的 INDEX 与 batches 同步 MUST 使用同一份已校验 snapshot，MUST NOT 在两份输出间重新读取形成不一致时点。

#### Scenario: problems 回显 stderr 但不阻断 INDEX 重建
- **WHEN** 池中某 dated 文件存在非致命 index↔block 不一致，运行默认 `issues.py reindex`
- **THEN** 每条 problem 逐条出现在 stderr（含 pool/文件定位），INDEX 仍从可判 snapshot 完整重建，退出码为 0

#### Scenario: 独立跑 reindex 时不一致不再静默
- **WHEN** 不经独立 `scan`、直接运行 reindex，且池中存在非致命一致性问题
- **THEN** 用户从 stderr 看到具体问题，而不是静默重建或吞掉 problems

#### Scenario: --strict 下 problems 非空即非零
- **WHEN** 以 `reindex --strict` 运行且池中存在非致命 problems
- **THEN** problems 回显后以非 0 退出；同一数据下默认 reindex 仍 exit 0 并生成 INDEX

#### Scenario: malformed recorder namespace 始终致命
- **WHEN** 任一 dated 文件的首块含 `sdflow-issues` 但 schema、JSON、字段或枚举损坏
- **THEN** reindex 无论是否 `--strict` 都非零退出并保持既有 INDEX/batches 逐字节不变，MUST NOT 以 legacy table 或部分 item 重建

#### Scenario: legacy arity 检查永久保留在历史读半场
- **WHEN** legacy table 某行不是 7/8 列且文件无有效 recorder namespace
- **THEN** scan 把该行作为带定位的 problem 回显；默认/strict 语义分别保持非阻断/阻断，MUST NOT 因新写已迁 frontmatter 而删除历史 arity 检查

#### Scenario: overlay shadow 不制造假重复 problem
- **WHEN** 同一 overlay 文件中 frontmatter item 与 frozen legacy row ID 相同
- **THEN** reindex 使用 frontmatter 当前值且不产生 duplicate problem；若相同 canonical ID 位于另一文件，则致命失败

## REMOVED Requirements

### Requirement: 总览表 row 字段 table-cell-safe（写时 reject 守盘面完整性）

**Reason**：新写索引不再使用 `|` 分隔 Markdown 表，拒绝合法 `|`/换行已无必要；继续保留该 requirement 会把临时止血守卫误当目标态并阻止 frontmatter 无损承载。

**Migration**：索引字段改由 SW-RI-1 的严格 frontmatter/JSON 转义承载；legacy table 只读并由 arity 校验守护。`batches.md` batch slug 与 Markdown 单行结构位的 line-safety 约束迁入 SW-RI-1，不能随 table-cell guard 一并删除。
