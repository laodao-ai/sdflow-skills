wrote openspec/changes/sweep-pool-debt-2026-08/impl-reports/task1-brief.md: 21 lines
k + 测试迁移 + 消费面收口）

**Blocked-by:** none
**R-ID:** SW1-SW6（spec-workflow delta 全部 Requirement：内容锚台账确定性 / 失鲜直接比较内容 / 评审锚 producer 记录 / 内容比较区分读失败与空 / gate git 调用失败退出码契约 / sdflow-code-review 复审边界；及 REMOVED 旧「阶段三编排台账确定性(ship_gate)」）

把 `ship_gate.py` 的失鲜判定从「以锚 commit SHA 作把手、ls-tree 映射等值 + tasks.md 逐提交豁免 walk」改为「监视域内容指纹（manifest + digest）单一源等值」，并交付权威写锚脚本，使 producer 写锚与 gate 验锚跑同一函数（物理同源）。对外可观察行为：设计门失鲜以内容 digest 判定（rebase/amend 不改内容即 CURRENT）、旧格式锚 fail-closed 判 UNKNOWN(6) 可恢复、归档 40-hex 报告仍可判 SHIPPED、`sdflow-code-review` 具备 impl-review 尾流修订的重锚协议。

- [ ] 指纹单一源函数落地：监视域枚举 → manifest 规范记录（字节保真编码，见 Global Constraints DT-2）→ sha256 digest；design 域监视集去 `tasks.md`（`DESIGN_WATCHED_NAMES` 调整），code/verify 域沿用顶层条目口径
- [ ] `is_stale`（design + code/verify 两分支）重写为「HEAD 侧重算 digest vs 锚 digest 等值」；`ship_gate.py:950` 现以锚 sha 作 git ref 取 `ls_tree_map` 的 code 分支一并改写为 HEAD 侧重算 digest 等值，锚值不再作 git ref 解析
- [ ] 删除勾框豁免层（`_normalize_checkbox_lines` / `_tasks_content_exempt` / `is_stale` 内联 tasks 豁免段，约 60–80 行 + 对应测试退役）；`grep -n "subject\|BR-7" ship_gate.py` 确认 subject 豁免 walk 已无残留（先期已删、无货可删，MUST NOT 在 report 报「删除了 walk」）
- [ ] 锚读取层 `read_reviewed_sha` 读 `reviewed_sha`(64-hex)+`reviewed_manifest` 并互证（manifest 字节 sha256 == digest）；缺失/非法/不互证 → UNKNOWN(6)；「锚指向对象不存在或非 commit」分类与诊断文案物理删除（六类→五类），五类 UNKNOWN 诊断 MUST 齐 problem/cause/fix 三段
- [ ] 校验分层落地（见 Global Constraints DT-1）：`FIELD_VALIDATORS["reviewed_sha"]` 放宽为 40|64 位小写 hex 语法校验 + `reviewed_manifest` 单行 base64 语法校验器（解析核不 fork）；`archived_verify_state` 仅消费 `verify` 结论，归档 34 份 40-hex 锚报告保持可判 SHIPPED
- [ ] HEAD 侧枚举失败 fail-closed：非零退出 MUST NOT 折叠为空 manifest（含变异证明用例）
- [ ] 新增 `sdflow-ship/scripts/anchor_writeback.py`（sibling，`import ship_gate` 复用指纹函数、4 行 reconfigure 前导、原子替换写 frontmatter、`--set` 同批写结论字段、空监视域/枚举失败 fail-loud 拒写、脏树守卫 fail-loud 拒写 + `--allow-dirty` 越权逃生口、头注释登记「手跑重锚=显式越权留痕」）
- [ ] 测试迁移：`sdflow-ship/tests/` 全部 `reviewed_sha` 相关 fixture 与断言迁到内容锚（实测 11 文件）；MUST 含 rebase 免疫（内容不变重写提交历史 → CURRENT）、manifest 字节保真 round-trip（Tab/换行/非 UTF-8 路径/CRLF）、code/verify 域 digest 等值（锚非 git 对象仍可判）、锚互证/缺失/非法 → UNKNOWN(6)、归档 40-hex + `verify: PASS` → SHIPPED 回归（变异证明：归档读点走 64-hex 校验 ⇒ 红）、anchor_writeback 写入/拒写单测
- [ ] 三个产出方 SKILL 回写步骤改调 `anchor_writeback.py`（`sdflow-spec-review` 拍板回写 / `sdflow-code-review` 报告落盘 / `sdflow-done` verify 模板与预检句 40→64-hex+manifest），并写明脚本调用失败（非零退出/空监视域）处置指引文案
- [ ] `sdflow-code-review` **新建** impl-review 重锚协议段（触发条件：对监视集文件打 `[impl-review-fix]` 补丁提交后；授权边界；调脚本刷新锚不动结论字段并随提交落盘）
- [ ] 新增独立 ADR 文件（为何 manifest+digest、tasks.md 移出、豁免通道改重锚协议）+ `adr/0026` 头部加 superseded-by 指针
- [ ] 全仓 `grep -rn reviewed_sha`（不加 --include）收口清零（归档区除外；实测消费面 21 文件，含 `openspec/specs/openspec-170-followup/spec.md` 与 `docs/workflow-skills/sdflow-spec-review.md` 的 40 位格式句）；全量 pytest 绿
- [ ] 票 1 收尾：用 `anchor_writeback.py` 重锚**本 change 自身** `spec-review-report.md`（40→64-hex+manifest，不动 `design_approved` 结论字段）并 checkpoint 落盘，随后实跑 `ship_gate` 确认 design 域 CURRENT（否则票 2/3/4 期间读本报告旧锚判 UNKNOWN(6) 自锁）

