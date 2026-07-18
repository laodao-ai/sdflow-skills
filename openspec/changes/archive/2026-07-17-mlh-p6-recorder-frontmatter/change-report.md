# mlh-p6-recorder-frontmatter Change 总结报告

> 日期：2026-07-17  
> Change：`mlh-p6-recorder-frontmatter`  
> 当前状态：**主体实现与本地评审完成，最终 Verify 未通过，尚未归档、合并或 push**

## 一、执行摘要

本 Change 把 bug/todo recorder 的机器索引从脆弱的 Markdown 表格迁到 versioned frontmatter，同时保留历史文档可读、可更新，不批量重写旧文件。

它解决的不是单个 `|` 字符转义问题，而是整条 recorder 数据链的结构性风险：表格切列、表与正文双写、跨池 ID 冲突、并发 `max+1` 撞号、无锁写盘、`batch rename` 重复扫描与半途失败后误报成功。

落地后形成了以下目标态：

- 新 item 只把机器字段写入严格的 `sdflow-issues` frontmatter，不再写 Markdown 总览表 row。
- 历史文件继续 dual-read；首次 mutation 时建立 overlay，旧表与既有 prose bytes 保持不变。
- bug/todo 两池共享 semantic ID 唯一性和仓级 exclusive snapshot lock。
- `scan` 每个 dated 文件只读、解析一次；`batch rename` 复用一次内存 snapshot 完成 retag 与 reindex。
- registry provenance 和原命令重试使 rename 在多文件非事务边界下可恢复收敛，不再 warning-only 假成功。
- 三个 recorder 保持运行时自包含，由 mirror consistency tests 防止共享机械逻辑漂移。

## 二、原来存在什么问题

### 1. Markdown 表格承担了不适合它的数据职责

`ID/module/summary/priority|type/status/time/change/batch` 被存入 Markdown 表格 cell。解析依赖 `|` 切列，因此写侧只能拒绝管道符、换行等正常内容。随着字段变复杂，数据安全依赖越来越多的拒绝规则，而不是可靠的数据模型。

直接后果：

- summary、module 等字段无法自然承载 `|`、多行和复杂 Unicode。
- 表格列数异常会造成字段错位，reader 很难判断真实 batch/status。
- 格式限制不断扩散到 CLI 校验和错误分支。

### 2. 机器状态在表格和 prose 中双写

旧 writer 同时更新总览表和详情块。两处任何一次写入不一致，scan、reindex、status/triage 就可能看到冲突状态。

### 3. 历史兼容与新写格式互相牵制

仓内仍有大量未终态 legacy item，不能简单停止支持旧表，也不能为了迁移批量改写历史文档。原实现缺少一种“旧数据不动、新状态可继续演进”的中间形态。

### 4. ID 分配与写入存在跨池、跨进程竞态

旧 `max+1` 流程没有把扫描、查重、分配和写盘放在一个锁域中。bug `A1` 与 todo `A1` 也可能被当作不同池的合法 ID；`A007` 与 `A7` 这种语义同号异形缺乏统一约束。

### 5. `batch rename` 重复扫描且失败语义不可靠

旧流程先通过 recorder `scan --json` 聚合，再重新打开 dated 文件修改，最后 reindex 又读一次两池。多阶段写入失败时，部分路径会 warning-only 返回成功，调用者无法区分“完全收敛”和“只改了一半”。

## 三、本 Change 做了哪些事情

### 3.1 建立严格的 frontmatter v1 与 dual-reader

三个 recorder 使用同一逻辑合同读取以下三种盘面：

| 盘面 | 含义 | 读写策略 |
|---|---|---|
| `canonical` | 新格式文档，机器索引完全在 frontmatter | 只更新 frontmatter 与 marker prose |
| `overlay` | legacy 表仍在，但当前机器状态由 frontmatter 覆盖 | 冻结旧表，只更新 overlay |
| `pure-legacy` | 尚未触碰的历史文档 | 继续读取；首次 mutation 时 promotion |

关键实现：

- `render_recorder_namespace()` 产生固定字段顺序、semantic ID 排序、确定性 JSON object bytes。
- `parse_recorder_document()` 严格校验 schema、pool、mode、字段类型、枚举、ID、marker relation 和 lexical profile。
- 只有 namespace 不存在时才允许 fallback 到 legacy；namespace 在场但损坏时 fail-closed。
- reader 以 binary bytes 工作，保留 BOM、LF/CRLF、未知 sibling namespace 和 recorder span 外正文。
- shared envelope 只解释唯一顶层 `sdflow-issues` 子树，不引入 PyYAML，也不替其它工具验证未知顶层内容。

结果：机器索引可以无损承载 `|`、换行和 Unicode，且坏数据不会被静默解释成合法 legacy 数据。

### 3.2 切换新 writer，并用 overlay 延续历史 item

新建 item 直接产生 canonical frontmatter。对 legacy item 执行 `set-status`、`triage` 或 rename 时：

1. 按 semantic ID 找到唯一可判的 legacy item 与 prose block。
2. 在 frontmatter 中建立 canonicalized overlay item。
3. 只在既有 prose block 外围添加成对 ID marker。
4. 冻结旧表、旧属性表和 marker 内部的历史 prose bytes。
5. 后续 mutation 只更新 frontmatter 与 marker 定界的历史记录。

writer 已停止：

- 写入或修改 dated 文件的 Markdown 总览表 row。
- 在 prose 中双写当前 status/batch。
- 使用 `_reject_cell_unsafe` 限制 frontmatter 可以安全承载的字段内容。

这使历史 item 仍能闭环，同时避免一次性迁移带来的大面积 Git churn 和审计噪音。

### 3.3 建立跨池 semantic ID 与仓级 snapshot lock

ID 规则升级为：

- 新写只接受 ASCII canonical spelling：单个大写字母 prefix + 非零开头十进制编号。
- bug/todo 两池按 `(prefix, decimal)` 统一查重，`A007` 与 `A7` 视为同一 semantic ID。
- 孤立 legacy alias 仍可读取；首次 promotion 后输出 canonical ID。
- `next-id`、自动 add、显式 ID 查重都在同一锁内读取两池全集。

所有权威读写统一进入仓级 `.recorder.lock`：

- owner 通过 `O_CREAT|O_EXCL` 独占建锁。
- `sweep → reindex → scan` 等复合命令通过受控 token 让 allowlist 子进程以 participant 身份加入，不自锁。
- token 不向非 allowlist 子进程泄露，伪造、过期、跨 repo 和越级委派在业务读取前拒绝。
- 写盘继续使用临时文件 + `os.replace`，并检查 ownership/token/identity 后释放。
- partial metadata 不按 TTL 自动偷锁，提供明确 break-glass 恢复步骤。

结果：并发 add 不再制造重复 ID 或 lost write，reader 与 writer 也不会成功返回跨 writer 的混合 snapshot。

### 3.4 重构 `batch rename` 为单次 snapshot 与可恢复流程

`issues.py` 现在直接构造两池 immutable bytes snapshot：

```text
bug/todo dated files
        │ 每文件 binary read + parse 各一次
        ▼
read_rename_snapshot
        │ registry-first provenance 判定
        ▼
retag_rename_snapshot（内存更新 canonical / overlay / legacy promotion）
        │
        ├── atomic write dated files
        └── _reindex_core(snapshot=updated_snapshot)
                 ├── INDEX.md
                 └── batches.md 派生状态
```

新行为包括：

- rename 整个命令每个 dated 文件 read/parse 各一次。
- 两池 recorder `scan --json` 调用数为零。
- reindex 复用 retag 后的同一 snapshot，不重新读取两池。
- registry 先写 new key 和 machine-owned `重命名自: old` provenance。
- 首次执行、全 old、old/new 混合、全 new retry 都有确定状态矩阵。
- orphan、old/new 双 key、unknown source、provenance 不匹配、影响 batch 真值的 malformed row 全部写前拒绝。
- registry、dated、INDEX、batches 四阶段失败均 non-zero，并输出 `stage=` 和可复制的原命令；解除故障后重跑同一命令可收敛。
- 与目标 retag 无关且 item 仍可判断的 legacy problem 保持默认可观测语义，`--strict` 仍负责升级为非零。

### 3.5 清理旧写半场并完成 dogfood

交付阶段完成了：

- 删除三个 recorder 新写路径中的 `_reject_cell_unsafe` 与 legacy row mutation。
- 保留 legacy table parser 只服务 dual-read 和 promotion。
- 更新 mirror helper roster、README、三个 `SKILL.md`、CLI help/error、`CONTEXT.md` 与 ADR-0025。
- 使用独立 test-side Markdown projection 对仓内 legacy corpus 逐 item 对账，不调用 production parser 自证。
- 通过真实 recorder 命令把 T85、T66、T67、T146、T2 写成 overlay/DONE 交付记录，确认旧表 bytes 不变、effective scan 值正确、`reindex --strict` 收敛。
- 更新 mechanical-layer-hardening roadmap、task-log、issues INDEX 与 batches。
- 新增持久、branch-agnostic 的 `windows-latest` workflow，准备执行 Windows local-disk smoke。

## 四、具体解决了什么问题

| 原问题 | 解决方式 | 用户/维护者得到的结果 |
|---|---|---|
| `|`、换行会破坏表格列 | 机器索引迁入 strict frontmatter | summary/module 可保存正常文本，不再靠拒绝输入保结构 |
| 表与 prose 双写会漂移 | frontmatter 成为当前机器状态单一来源 | status/batch 不再出现两处真相 |
| 历史 item 不能停止更新 | dual-reader + 按访问建立 overlay | 不批量迁移，也能继续 status/triage/rename/sweep |
| 坏 frontmatter 可能被当 legacy | namespace 在场即严格解析，失败不 fallback | 数据损坏尽早暴露，不静默吞错 |
| `A007`/`A7` 与跨池 ID 冲突 | semantic key + 两池锁内统一查重 | 自定义 ID 唯一，成功输出逐步 canonicalize |
| 并发 `max+1` 可能撞号、覆盖 | owner/participant snapshot lock + atomic replace | 20 进程压力测试下无重复成功 ID、无 lost write |
| scan 重复读取文件 | single-read binary document pipeline | 每 dated 文件只读/解析一次，结果更确定 |
| rename 多次扫描、半途失败假成功 | direct snapshot + provenance + fail-closed stage recovery | 只有完全收敛才成功；失败可用原命令重跑恢复 |
| 三份自包含代码容易漂移 | THREE_WAY/TWO_WAY mirror consistency roster | 保持无跨 skill runtime import，同时能机械发现差异 |
| runtime lock 可能进入 Git | canonical runtime `.gitignore` merge | init/update 幂等加入 lock ignore，并保留用户 bytes |

## 五、兼容性与迁移策略

### 保持兼容

- CLI command 和 scan JSON envelope 保持稳定。
- 历史 pure-legacy 文件继续可读、可操作。
- `issues/batches.md` 不迁移。
- 状态机、priority/type 枚举、DONE/FIXED 门禁和 sweep 非原子重跑语义不变。
- 三个 recorder 继续自包含，不建立跨 skill runtime import。

### 有意的 breaking change

- 新建 dated 文件不再生成 Markdown 总览表。
- legacy raw alias 如 `A007` 首次 mutation 后会以 canonical `A7` 出现在成功 JSON 和后续 scan 中。
- 直接解析 dated Markdown 表的非契约消费者必须改用 recorder CLI/JSON。

### 明确不做

- 不批量迁移全部历史文件。
- 不迁移 `batches.md`。
- 不新增数据库、远程 tracker backend、`doctor`、自动 lock recover 或 TTL 偷锁。
- 不承诺 NFS/SMB/FUSE 等 network/userspace FS 与本地文件系统相同的 lock/replace 语义。
- 不实现完整 file + directory fsync，因此不承诺 power-loss durability。
- cooperative lock 能防合规 participant 互相覆盖，但不伪造对绕锁外部 writer 的 CAS 保证。

## 六、验证与评审证据

### 已通过

- recorder 定向 `-W error`：`445 passed, 2 skipped`；两个 skip 都是 actual-Windows-only case。
- mirror consistency：`7 passed`。
- Task 4 snapshot/rename/mirror 定向复审：`98 passed`。
- 普通全仓 pytest：`1619 passed, 2 skipped`。
- known-consumer smoke：升级安装后对 legacy/canonical/overlay fixture 执行两 recorder `scan --json`、`issues reindex --strict` 与 `sweep`，验证 JSON/INDEX/batches contract。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive`：valid。
- `git diff --check`：通过。
- Task 1–4 均经过独立 Standards + Spec 双轴评审并在修复后 PASS。
- Task 5 首轮发现的 Windows delegation fixture、corpus 自证、公开 SKILL 旧合同均已修复；复审确认只剩 actual Windows 执行证据。

### 收尾门（两项均已达成）

1. **Actual Windows local-disk smoke——已通过（曾为 release blocker，现已解决）。**
   - `windows-latest` runner（真本地盘 `C:\Users\runneradmin\...`）→ `2 passed in 20.73s` 无 skip：run [29568476168](https://github.com/laodao-ai/sdflow-skills/actions/runs/29568476168)、commit `ba004e1`。
   - recorder lock acquire/conflict/participant/replace/cleanup 与 setup copy 均在真 Windows 通过。
   - 收尾途中真 Windows 暴露两处**测试层**问题（`bash` 解析到 System32 的 WSL launcher 无 distro；subprocess text 模式未指定 utf-8 致读线程解码 setup.sh 的 UTF-8 输出崩），已一并修复——非 recorder/setup.sh 代码 bug。

2. **全仓 warnings-as-errors 门——已 fold 清零（曾为缺口，现已解决）。**
   - 结果：修 4 个 pre-existing 未关闭文件站点后，全仓 `pytest -W error` → `1619 passed, 2 skipped`（2 skip = Windows-only）。
   - 站点枚举、引入 commit 与归属决策见下「成因溯源与 fold 清零」子节；执行见 tasks 7.5。
   - 决策 = 修站点 fold 进本 Change、全仓机械守卫另开 hardening change（todolist T155）。

[verify-report.md](verify-report.md) 现判定 **PASS**（warning 门 fold 清零 + Windows 门取得真 runner `2 passed` 锚），逐需求核对全 ✅，可执行 hand-off → archive → spec 主线同步 → 默认分支 merge。

### 全仓 `-W error` 门：成因溯源与 fold 清零（pre-existing，非本 Change 引入）

三个待修站点全部是存量缺陷，由更早的 Change 引入，早于本 Change 分支点
（merge-base 7fd59e6，2026-07-16 14:08）：

| 站点 | 引入 commit | 时间 | 引入的 Change |
|---|---|---|---|
| `maintain_scan.py:244` 裸 `open().read()` | a32e91e7 | 2026-07-09 | mlh-p4-maintain-scan |
| `maintain_scan.py:184` 裸 `open().read()` | 10254c16 | 2026-07-09 | mlh-p4-maintain-scan |
| `test_maintain_scan.py:224` 裸 `open(...,"w").write()` | 56c77d1 | 2026-07-09 | mlh-p4-maintain-scan |
| `test_sad_scaffold.py:525` Popen 不 drain | ce9b037c | 2026-07-12 | add-sdflow-architecture |

（verify-report 原记「37 全在 :244」不准：不仅 `maintain_scan.py` 读侧 :184/:244 两处，
`test_maintain_scan.py:224` 还有一处测试侧 `open(...,"w")` 裸写——**同一「未关闭文件」面既有读也有写**。
该第 4 站点是 fold 修完前 3 处后跑全仓 `-W error` 才由工具自己暴露的：解析 Python 表达式是无界语法面，
正则手搓会漏（实测漏掉嵌套括号的 :224），故站点一律以 `-W error` 权威枚举，非正则清点。）

为什么之前没发现——从没有任何门照过它：

- 历史所有 Change 的 `-W error` 只挂各自 scope 的定向套件，全仓一律普通 pytest；
  引入缺陷的两个 Change 自己 verify 也没跑 `-W error`。7-09 至今无任何 Change
  对 sdflow-maintain 跑过 `-W error`。
- 本 Change tasks 7.3 是本仓第一次把 `-W error` 挂到全仓 1600+ 级别，
  因而是第一个「看见」这些潜伏 7 天存量债的 Change。
- 次要放大（非主因）：python 3.14.6 + pytest 9.1.1 对 unclosed file 捕获更严。

成因时间线：

```text
7-08 done-roadmap-writeback  全仓 -W error → 762 passed 0 warning ✅（缺陷尚未引入）
7-09 mlh-p4-maintain-scan    引入 maintain_scan.py:184/:244 裸 open().read()  ← 缺陷诞生
7-12 add-sdflow-architecture 引入 test_sad_scaffold.py:525 Popen 不 drain    ← 缺陷诞生
7-14 add-sdflow-devenv       全仓普通 pytest 1260 ✅（不加 -W error，照不到）
7-16 add-codex-host-support  全仓普通 pytest 1426 ✅（不加 -W error，照不到）
7-16+ 本 Change mlh-p6       tasks 7.3 首次全仓 -W error → 38 failed          ← 债第一次被照出
```

定性：pre-existing 是事实，但不构成「绕过」理由——本 Change 是第一个立全仓 -W error
门、因而第一个看见此债的 Change。按目标态（warning 清零）应面治根治。

**归属决策（已定）**：拆两半——

- **修 4 站点 → fold 进本 Change**：它们是本 Change tasks 7.3 亲手立的门的完成条件（门下的债，
  不清不绿）；4 处均纯机械低风险（`with` / `communicate()`），另开一次完整 workflow 循环的固定
  成本远大于修复本身。已于 tasks 7.5 完成，全仓 `-W error` → `1619 passed, 2 skipped`。
- **全仓机械守卫（把全仓 `-W error` 常态化为持久 CI 门）→ 另开 hardening change**：本仓
  `.github/workflows/` 现仅有 Windows smoke、无任何全仓 pytest CI，「常态化 `-W error`」是从零
  新增 CI 基础设施 + 一致性面治理，够一个独立完整阶段结果，且需设计（触发 / matrix / 覆盖范围）——
  fold 进本 Change 会把 recorder 迁移膨胀成两个不相干功能。已登记 todolist `T155` 作为其起点。

## 七、交付状态

| 阶段 | 状态 | 说明 |
|---|---|---|
| 设计与 delta specs | ✅ 完成 | proposal、design、spec-review 已收敛 |
| Task 1：strict dual-reader | ✅ 完成 | 双轴 PASS |
| Task 2：semantic ID + snapshot lock | ✅ 完成 | 双轴 PASS |
| Task 3：frontmatter writer + overlay promotion | ✅ 完成 | 双轴 PASS |
| Task 4：snapshot rename + provenance recovery | ✅ 完成 | 双轴 PASS |
| Task 5：cleanup/dogfood/docs | ✅ 完成 | 本地 review gap 已修；Windows actual smoke 已在真 runner 通过 |
| `sdflow-done` Verify | ✅ PASS | 两门均达成：warning 门 `1619 passed, 2 skipped`；Windows 门 run 29568476168 `2 passed`（见 verify-report） |
| Archive / merge / push | ⏸ 待执行 | Verify 已 PASS，可跑 `sdflow-done` 走 hand-off → archive → ff merge |

## 八、下一步

1. ~~修复 `sdflow-maintain`/`sdflow-architecture` 未关闭文件 warning~~ **已完成**（tasks 7.5 fold 修 4 站点，全仓 `pytest -W error` → `1619 passed, 2 skipped`）。全仓机械守卫另开 hardening change（todolist T155）。
2. ~~在 `windows-latest` 执行 Windows smoke 并保存 run 锚~~ **已完成**：run [29568476168](https://github.com/laodao-ai/sdflow-skills/actions/runs/29568476168)、commit `ba004e1` → `2 passed` 无 skip（收尾途中修 `bash`→WSL、subprocess utf-8 两处测试层问题）。
3. **待执行**：跑 `$sdflow-done mlh-p6-recorder-frontmatter` 走正式 Verify（strong model 冷启动复核）→ hand-off（issues sweep；T153/T154 已标 DONE + reindex 已刷新，sweep 处理其余 OPEN）→ archive（delta spec 同步进 `openspec/specs`）→ ff merge 到默认分支。
4. **后续**：另开 hardening change 落 T155（全仓 `-W error` 常态化 CI 守卫）。

## 九、关键资料

- [proposal.md](proposal.md)：为什么做、影响面与 success metrics。
- [design.md](design.md)：frontmatter、overlay、lock、snapshot rename 的完整设计。
- [tasks.md](tasks.md)：逐项实施与当前完成状态。
- [spec-workflow delta](specs/spec-workflow/spec.md)：recorder 行为合同。
- [determinism-guards delta](specs/determinism-guards/spec.md)：镜像与确定性守卫。
- [ADR-0025](../../adr/0025-recorder-versioned-frontmatter-overlay-and-snapshot-lock.md)：落地后的稳定架构决策。
- [verify-report.md](verify-report.md)：最终门禁证据与未闭环项。
- [impl-reports/](impl-reports/)：每个 Task 的实现、双轴评审与修复证据。
