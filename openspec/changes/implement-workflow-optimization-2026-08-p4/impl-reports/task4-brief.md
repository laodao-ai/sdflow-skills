### Task 4: render-review-prefix.sh 与部署链

**Blocked-by:** none
**R-ID:** SW-1

新建 `render-review-prefix.sh`（落 `sdflow-init/assets/hack/`，setup 装 `~/.sdflow/hack/`）：接受 `--layer code-review|spec-review` 参数；按固定序 cat 通则区块（`~/.sdflow/hack/skill-principles.md`）+ 内嵌通用契约段 heredoc（含 T103 输出封顶句「回传目标 ≤2k token，超出按严重度截优先」）+ base checklist（`$RULES_ROOT` 解析到的对应层 base checklist 全文）。任一源缺失 ⇒ fail-loud 非零退出 + stderr 含 problem+cause+fix。byte-stable 可测试（同规则集连续两跑逐字节同）。setup.sh 布署链验证：脚本随 hack 拷贝就位。

- [ ] `render-review-prefix.sh --layer code-review` 按固定序输出通则 + 通用契约段 + base checklist
- [ ] `render-review-prefix.sh --layer spec-review` 同构输出对应层
- [ ] 任一源缺失 ⇒ 非零退出 + stderr 含 problem+cause+fix（MUST NOT 输出半段前缀）
- [ ] byte-stable golden 测试：连续两跑逐字节同 + 源缺失非零退出
- [ ] setup.sh 部署链：脚本随 hack 拷贝到 `~/.sdflow/hack/`

