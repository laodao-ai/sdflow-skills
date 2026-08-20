## Global Constraints

逐字摘自 `design.md` 的 MUST / MUST NOT / SHALL 硬约束与 Compliance 条款（implementer 与两轴审 reviewer 共享同一注意力透镜）：

- **DT-1 校验分层**〔spec-review-amendment R1，防 SHIPPED 大面积回归〕：解析层（`FIELD_VALIDATORS`）对 `reviewed_sha` 只做语法校验并放宽为「40 或 64 位小写 hex」、`reviewed_manifest` 注册单行 base64 语法校验器——解析核不 fork、无归档模式参数（承 A4 共核纪律，对存量行为零回归）；64-hex + manifest 互证的语义强制上移 `read_reviewed_sha`（live 读点），40-hex 判 ANCHOR_INVALID → UNKNOWN(6)，诊断指明「旧格式锚，重跑写锚脚本」；`archived_verify_state` 只消费 `verify` 结论，34 份 40-hex 归档报告自然通过解析（无 fail-open：新鲜度恒要求 digest 等值，40-hex 不可能等于重算 digest）。旧值(40-hex)进新 gate 判 ANCHOR_INVALID → UNKNOWN(6) 可恢复，天然 fail-closed。
- **DT-2 等值判定只走 digest**（重算 HEAD 侧 manifest → sha256 → 与锚值比对）；**诊断走 manifest**（digest 不等时对 HEAD 侧枚举求差集 → 点名路径，`git log -1 -- <路径>` 点名提交）。**监视域按报告分**：design 域 = change 目录内 `proposal.md`/`design.md`/`specs/`（tasks.md 移出，D2）；code/verify 域 = 顶层条目映射（非递归、排除 `openspec`，既有口径）——两域锚值均为 manifest digest，**gate MUST NOT 将锚值作 git ref 解析**（现 code 分支 `ship_gate.py:950` 以锚 sha 取 `ls_tree_map`，MUST 一并重写为 HEAD 侧重算 digest 等值）。
- **DT-2 manifest 规范编码 MUST 字节保真**：记录取 `ls-tree -z` 原始 path 字节（git 路径可含 Tab/换行/非 UTF-8），按原始 path 字节序排序；frontmatter 存储用单行字节保真编码（base64 该规范字节流），digest 对解码后原始字节计算；**MUST NOT 依赖 YAML 文本行清单的转义/归一化**（会致同内容不同 digest 或异路径折叠）；互证 = 解码字节流的 sha256 == `reviewed_sha`。比较端不取锚侧字节 ⇒ 无 dangling-blob 依赖。
- **DT-3 脚本 MUST 支持同批写入结论字段**（如 `--set design_approved=true` / `--set verify=PASS`），producer 一次调用同时落结论+锚（单次原子替换）；**MUST NOT 先手写结论再调脚本补锚**（中间态 = 结论在、锚缺 → UNKNOWN）。**脏树守卫**〔spec-review-amendment R2〕：监视集路径存在未提交改动（`git status --porcelain -- <监视集>` 非空）时 **MUST fail-loud 拒写**并提示「先提交修订再写锚」；逃生口（如 `--allow-dirty`）仅显式越权留痕场景。脚本带 4 行 `reconfigure` 前导（第五道机械门要求）。判官只读语义不破。
- **枚举失败 fail-closed**〔tasks 1.4〕：HEAD 侧枚举非零退出 **MUST NOT 折叠为空 manifest 参与比较**（空集 digest 假等值面）。
- **DT-7 impl-review 豁免通道改造**：gate 端 subject 豁免与勾框内容豁免在 spec 层一并退役（subject 豁免代码已于先前 impl-review-fix 物理删除、无货可删；勾框豁免代码仍在、真删），`is_stale` 缩为「重算指纹 → digest 等值」；`sdflow-code-review` **新建** impl-review 重锚协议段——修订提交后跑 `anchor_writeback.py` 刷新 spec-review-report 锚（不动结论字段）并随提交落盘。忘重锚 ⇒ REFUSE_START（fail-closed，补跑即恢复）。
- **Compliance**：遵守 `openspec/rules/doc-authoring.md`（DOC-1：正文即最终态，无演进史层）；遵守 `premise-verification`（断言带核验锚，引用前真打开）；**基准 5：不新增任何 Markdown/语法解析——指纹是零解析字节级 digest；fence 有界词法共用件保留原状**（`fence_delim`/`FenceTracker` 四处共用件不在删除面内）。

