### Task 4: workflow bundle 同步与安装链路生效

**Blocked-by:** 1, 2, 3
**R-ID:** R2

工作流规则 bundle 与本次讨论层重构对齐：`wayfinder-resolved:` 前缀规则保留但标为 legacy（消费仓
存量 footage 仍可能被溯源）、演进史留下一条移除记录、消费仓 config 生成模版中指向已不存在章节的
陈旧引用被订正；改动经安装链路生效到全局 canonical。

行为上可观察的结果：新下游仓由 `sdflow-init` 生成的 `config.yaml` 不再引用不存在的
「wayfinder→ff 衔接契约」章节；本机 `~/.sdflow/workflow/` 解析到的规则即改动后版本。

依据：`tasks.md` §4（4.1–4.5）。

🔴 **本票在主工作树串行执行**（`Blocked-by` 覆盖全部并行票 ⇒ `next_ready` 只返回它一个）——
`setup.sh` 建的是**绝对路径 symlink**，在临时 worktree 中执行会把全局 skill 链接指向随后即被删除的
路径。若发现自己不在主工作树，`BLOCKED` 上抛，MUST NOT 就地跑 `setup.sh`。
🔴 4.4 的**验收动作 = 单独跑 `python3 hack/sync_principles.py --check` 看 exit code**——`setup.sh`
里那一处是 `if ! …; then echo "⚠️…"; fi`，**不是 fail-closed 门**，警告会淹没在大段输出里。
🔴 4.5 是**合并后**才能执行的 hand-off 项（运行 checkout `~/.skills/sdflow-skills` 重跑 `setup.sh`
/ `/sdflow-upgrade`）——本票**不执行**它，只在实现记录中写明它待 hand-off 承接。

- [ ] `ff-generation-constraints.md` 的 `wayfinder-resolved:` 前缀规则保留且加 legacy 标注（4.1）
- [ ] `workflow-history.md` 追加一条 wayfinder 路径移除记录（4.2）
- [ ] `config.template.yaml` 的 `:41` / `:51` 两行陈旧章节引用已订正（4.3）
- [ ] dev checkout 跑过 `bash setup.sh`，且**单独**跑 `python3 hack/sync_principles.py --check` 退出码为 0（4.4）
- [ ] 4.5（合并后运行 checkout 还原）已在实现记录中写明为 hand-off 项，未在本票执行（4.5）

