### Task 1: Validator 机械脚本

**Blocked-by:** none
**R-ID:** R-裁决

新建 findings 引用核验机械脚本（落 bundle `tools/` 同类脚本旁），实现三查 + 三态输出 + 崩溃降级。

**行为**：
- 输入：结构化 JSON，每条 finding 带 `{file, line, quote}` 或 `evidence_pack` 机读字段
- 三查：① 引用路径存在 ② `file:line` 落在文件行数内 ③ 单行引文命中所报行或显式行范围（MUST NOT 只检查整文件子串）
- 三态输出：`pass`（三查全过）/ `fail`（结构化字段在、任一不过）/ `uncheckable`（引用为证据包/设计层引用，非干净 `path:N` 形态 ⇒ 不裁，原样直进强档裁决）
- 「无引文且无证据包」（结构化字段确认皆缺）→ 机械裁掉
- 脚本级不可恢复错误（crash / 输入 JSON 畸形）→ 显式降级：整批标 `[ref-check-unavailable]` 直进裁决 + 报告显著标注机械门未生效，MUST NOT 静默呈现全部 pass
- 输出遵循消费型信号校验器输出诚实（不 emit 裸通过码）

- [ ] 正例（路径存在+行号合法+引文命中该行）返回 pass
- [ ] 三种失败态（路径不存在/行号越界/引文不在所报行）各返回 fail
- [ ] 无引文且无证据包态返回机械裁掉信号
- [ ] uncheckable 态（证据包/设计层引用/行范围外形态）返回 uncheckable
- [ ] 脚本级崩溃（输入 JSON 畸形/意外异常）→ 显式降级标 `[ref-check-unavailable]`
- [ ] 输出码形态符合信号内诚实
- [ ] pytest 覆盖上述 6 个场景

