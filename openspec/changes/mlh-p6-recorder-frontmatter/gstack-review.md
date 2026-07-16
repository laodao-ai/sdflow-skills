<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack-review — mlh-p6-recorder-frontmatter

> `[gstack-amendment]` 2026-07-16。autoplan 经主 session 原生执行：已加载 CEO / Eng / DX review 方法，按 CEO → Eng → DX 串行运行独立 fresh-context reviewer；Phase 2 Design 因无 UI scope 跳过。宿主解析为 `codex`，三档为 `gpt-5.6-sol / gpt-5.6-terra / gpt-5.6-luna`。本场景是 OpenSpec change，不改写独立 plan file；premise/final gate 按 G2 统一登记到最终 `spec-review-report.md`。
>
> 侧信道佐证：三个 cold reviewer agent id 分别为 `019f6b83-3026-7ed1-8bc7-a3120777d8d7`、`019f6b86-b566-71f3-9b13-39b13bbaf45c`、`019f6b8a-6212-7492-b703-9d4657b26646`；均返回带 file:line 的独立 findings。跨模型 outside voice 由 `sdflow-spec-review` guard 在本文件落盘后决定复用或补跑。

## 0. Intake 与目标态

- **对象**：`proposal.md`、`design.md`、两份 delta spec、`tasks.md`、ADR-0025，以及三 recorder / `sdflow-init` 的真实代码与测试。
- **产品类型**：本地 Python CLI + Git 中的 Markdown protocol；无 UI，DX scope 命中。
- **目标态**：机器索引不再受 Markdown 表列模型约束；历史 item 可闭环；CLI/JSON 稳定；并发写不撞号、不丢写；坏结构 fail-closed。
- **前提门**：用户已在 grill 明确批准 shared envelope、same-file overlay、semantic ID、exclusive snapshot lock 与 phase-recognizable rename；autoplan 不重开这些偏好门，只核是否存在新事实或不可实现承诺。

## 1. CEO / Strategy 广审

### 1.1 Premise challenge

结构化索引替代按 `|` 切列是真问题，不是代理指标；`proposal.md:9-19` 与现行 `_reject_cell_unsafe` / `parse_table_rows` 共同证明腐蚀根因。目标不是“减少几行 parser”，而是让未来 producer 可以合法产出 `|`、换行与 Unicode，同时不再制造表↔块双写。

### 1.2 实现路线

| 路线 | 完整度 | 收益 | 代价 | 裁决 |
|---|---:|---|---|---|
| A. 永久保留 table writer + reject/escape | 3/10 | diff 最小 | 根因保留、双写永久存在 | 淘汰 |
| B. dated-document 首次 mutation 整文件迁移 | 7/10 | 已触达文件快速单盘面 | 一次小变更会重写整篇历史，违反已批准的历史 bytes 边界 | 备选 |
| C. same-file item overlay + marker（现方案） | 10/10 | 历史表冻结、活 item 可闭环、逐项进入单一机器真相源 | dual-read 在历史寿命内存在，parser/marker 测试面大 | **推荐** |

推荐 C：它同时满足两个用户已拍板的硬边界；B 只有在允许整篇历史重写时更简单。这里不能用“现存文件还没有第二个 producer”否决 shared envelope；目标态本来就是多个 metadata producer 共用首块。

### 1.3 CEO findings（完整留痕）

| ID | Finding | 置信/严重度 | broad 裁决 |
|---|---|---|---|
| C-1 | 建议把 P6 拆成结构化写入与锁/rename 两期 | 中 / high | **待最终裁决**：拆分会让 ID/rename 在新格式上线后继续暴露竞态，需以依赖图而非文件数判断。 |
| C-2 | 建议由 item overlay 改为整文件懒迁 | 高 / high | **裁掉**：与“旧表/旧 prose 不批量改写”已批准边界冲突；技术备选仍保留在 ADR。 |
| C-3 | 建议普通 scan 不加锁 | 中 / high | **裁掉**：目标态成功 snapshot 不得跨 writer；只读锁域已收窄到 immutable snapshot materialize，输出前释放。stale-lock UX 另审。 |
| C-4 | 因当前未发现第二 producer，建议 recorder 独占 frontmatter | 高 / high | **裁掉**：违反通则③；以目标态 producer 组合性为基准，不能拿当前语料缺席否决。 |
| C-5 | breaking storage change 缺消费仓 smoke / 升级说明 | 高 / high | **采纳**：补 README/SKILL/help 与已知消费方 CLI/JSON contract smoke。 |
| C-6 | rename 恢复缺显式操作可见性 | 中 / high | **部分采纳**：错误须输出已识别阶段与原命令 retry；不新增 `--resume` 第二入口，保持原命令幂等。 |
| C-7 | `batches.md` 被排除却是恢复状态源 | 中 / medium | **采纳澄清**：不迁存储格式，但其既有 machine grammar/old-new key 是恢复输入，必须纳入盘面矩阵测试。 |

### 1.4 Dream state delta

```text
Markdown table 机器真相源
  + table/prose 双写
  + unlocked max+1
        |
        v
本 change：versioned namespace + marker prose + semantic ID + snapshot lock
        |
        v
12-month ideal：所有 recorder producer/consumer 只依赖稳定 CLI/JSON，
历史 legacy 只读自然衰减，任何新 metadata producer 可在共享 envelope 中独立演进。
```

## 2. Eng / Architecture 广审

### 2.1 Architecture

```text
buglist.py ─┐
todolist.py ├─ owner/participant lock ── immutable snapshot ── CLI/JSON
issues.py  ─┘             |
                parse once + byte spans
                         |
        legacy table / overlay / canonical namespace
                         |
        dated atomic bytes + generated text outputs
```

三份脚本自包含、以 CLI/JSON 解耦且用 AST/golden 守镜像，是与仓库安装模型一致的边界。真正的风险不在“文件多”，而在 scanner grammar、semantic identity、锁 release 承诺与 rename cut-point 是否可精确验收。

### 2.2 Eng findings（完整留痕）

| ID | Finding | 证据 | 置信/严重度 | broad 裁决 |
|---|---|---|---|---|
| E-1 | token check 后到 `unlink(path)` 仍有替代锁 TOCTOU，无法原子保证“绝不误删” | `design.md:246-250`; spec `SW-RI-2` owner release scenarios | 高 / high | **采纳**：把承诺收窄为 cooperative best-effort token/inode recheck；若路径在 recheck 后被外部绕协议替换，属于明确残余竞态，不伪称机械保证。 |
| E-2 | isolated legacy `A007` promotion 未定义 raw ID 与 canonical key/marker 的关系 | `design.md:86-97`; spec `SW-RI-2` | 高 / high | **采纳**：raw spelling 只作定位证据；semantic key 合并/shadow；promotion 写 canonical ID，marker identity 随 canonical ID。 |
| E-3 | rename 矩阵漏 `registry=old` 且 items 已全部 new 的真实 cut-point | `issues.py:990-996`; `design.md:278-284` | 高 / high | **采纳**：补 reachable state、动作与 fault injection。 |
| E-4 | shared envelope 外部 opaque YAML 的 span grammar 未定义 | `design.md:78,216-227`; `tasks.md:14` | 中 / high | **采纳**：明确 envelope lexical subset / rejection matrix；不实现完整 YAML parser。YAML 1.2 block scalar/flow/quoted styles证明仅按缩进找顶层键不够。 |
| E-5 | atomic replace 未区分 process-crash atomicity 与 power-loss durability | `atomic_write`; `design.md:157,274-286` | 高 / medium | **采纳**：本 change 只承诺进程级异常/replace 原子性；power-loss durability 显式 non-goal，不把两者统称。 |
| E-6 | POSIX mode bits、Windows sharing violation、network FS 支持边界未定义 | `design.md:252-257`; spec bytes-write scenario | 中 / medium | **采纳**：声明本地 POSIX 为验证平台，Windows 本地盘 best-effort/需兼容测试，网络挂载 unsupported；mode bits 仅 POSIX。 |

### 2.3 Test diagram

```text
parser/render unit
  ├─ schema/JSON duplicate/Unicode/NEL-LS-PS/canonical bytes
  ├─ envelope lexical subset + external opaque fixtures [E-4]
  └─ legacy raw ID -> semantic key -> canonical promotion [E-2]
          |
scan + mutation integration
  ├─ legacy / overlay / canonical + marker relations
  ├─ reader/writer barrier + owner/participant + blocked stdout
  └─ atomic bytes fault injection, process-crash boundary [E-1/E-5]
          |
rename recovery integration
  ├─ every dated/registry/INDEX/batches cut-point
  ├─ registry old + all items new [E-3]
  └─ idempotent rerun, no warning-only success
          |
platform/corpus regression
  ├─ full legacy baseline equality
  ├─ POSIX permissions
  └─ Windows local-disk compatibility / network FS explicit exclusion [E-6]
```

## 3. DX 广审

### 3.1 Persona 与 journey

**Persona**：维护或自动调用 sdflow recorder 的 skill 作者；只应依赖 CLI/JSON，不应理解 frontmatter 内部。

> “我升级是为了继续调用同一组 CLI，不是为了学习 frontmatter。成功时我要实际 ID；失败时我要马上分清输入错误、可重试锁冲突、stale lock 与仓内数据损坏。若必须自己推断 overlay/token/rename 阶段，内部实现就泄漏成了操作负担。”

| Stage | 动作 | 目标 | broad 发现 |
|---|---|---|---|
| Discover | 阅读 release/README | 知存储变但 CLI 不变 | README 仍讲表↔块双写 |
| Install | `bash setup.sh` | 三 recorder 同版 | Windows copy 更新非原子 |
| First write | `add` | 不学 frontmatter | 成功 JSON 兼容目标明确 |
| Consume | `scan --json` | shape 稳定 | 需 contract fixture |
| Allocate | `next-id` / `add` | 知 advisory | help 未说明不预留 |
| Concurrent | 多 agent/CI | 明确 retry | lock 诊断格式未钉死 |
| Diagnose | bad namespace/marker | problem/cause/fix | path/reason 有要求，缺统一文案模板 |
| Recover | stale lock / partial rename | 按提示重跑 | 需输出阶段与恢复命令 |
| Verify | 全仓/消费仓 | 证明升级可用 | 缺 README/known-consumer smoke |

### 3.2 DX findings（完整留痕）

| ID | Finding | 置信/严重度 | broad 裁决 |
|---|---|---|---|
| D-1 | 自动化错误没有稳定 code/JSON diagnostic | 高 / high | **部分采纳**：所有新增失败必须统一 `ERROR: problem; cause; fix` 且 stdout 纯净；新增 `--diagnostic-format=json` 超出稳定 API 目标，作为后续候选。 |
| D-2 | README/SKILL/help 未纳入 breaking storage 升级交付 | 高 / high | **采纳**。 |
| D-3 | `next-id` help 易被误当 reservation | 高 / high | **采纳**：help/SKILL 明写 advisory，示例以 `add` 返回 ID 为准；不新增 `next-id --json`。 |
| D-4 | stale lock 只有手工核验/删除，无 `lock recover` | 高 / high | **待最终裁决**：自动 recovery 与“不偷锁”冲突；优先可读诊断/runbook，是否新增保守子命令交多镜审。 |
| D-5 | 缺 `doctor --json` | 中 / high | **待最终裁决**：scan/reindex 已能报告 problems；先核是否能扩充现有只读命令而非新增重叠入口。 |
| D-6 | Windows 顺序 copy 可能混合三 recorder 版本 | 高 / high | **部分采纳**：实现/安装测试必须覆盖同一 checkout setup 后三脚本协议一致；重做整个 Windows installer 非本 change 默认 scope。 |
| D-7 | 无 Windows CI | 高 / high | **待最终裁决**：不能以“当前无 CI”否决目标支持；要么建立 runner，要么公开未验证边界。 |
| D-8 | 无 DX outcome measurement | 高 / medium | **采纳轻量验收**：verify 记录升级 smoke 与典型恢复路径可操作性，不加遥测。 |

### 3.3 DX scorecard（门前）

| Dimension | Score / 10 |
|---|---:|
| Getting started | 6 |
| CLI/API continuity | 8 |
| Error messages | 5 |
| Documentation | 4 |
| Upgrade path | 4 |
| Dev environment / platform | 5 |
| Community / ecosystem | 7 |
| Feedback loop | 5 |

目标：升级后首次 `scan --json` + `reindex --strict` 在 5 分钟内完成；lock conflict <1 分钟理解并重试；stale-lock / rename recovery 指引在 5 分钟内可执行。

## 4. Failure / rescue registry

| Codepath | Failure | Handling target | User sees | Test |
|---|---|---|---|---|
| parse document | malformed envelope/namespace/JSON | fatal, no fallback/no write | path + line/ID + cause + fix | negative matrix |
| semantic ID | invalid spelling / cross-pool conflict | fatal before write | both locations + canonical key | ID matrix |
| acquire lock | active/initializing owner | fail-fast before business read | owner metadata + retry/recovery | process barrier |
| release lock | ownership changed | preserve observed replacement; report lost ownership | explicit residual-boundary diagnostic | controlled replacement test |
| atomic replace | write/chmod/replace exception | old bytes preserved, temp cleanup | target + operation | fault injection |
| marker promotion | missing/ambiguous bug block | no mutation | ID + ambiguity + fix | promotion matrix |
| rename | partial dated/registry/derived outputs | non-zero, stage + rerun command | exact failed phase | cut-point matrix |
| setup/update | recorder protocol mix | fail-loud or install validation | rerun setup + mismatch | install smoke |

## 5. Cross-phase themes

1. **恢复承诺必须等于可实现的原语**：E-1、E-3、C-6、D-4。
2. **机器身份与人读 spelling 分离**：E-2 与 canonical renderer。
3. **opaque preservation 仍需要显式 lexical 边界**：E-4；YAML 不是简单缩进表。
4. **breaking storage change 的稳定面是 CLI/JSON + upgrade docs**：C-5、D-1/2/3/8。
5. **原子性/跨平台必须声明保证层级**：E-5/6、D-6/7。

## 6. Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale |
|---|---|---|---|---|---|
| AD-1 | Intake | 接受已 grill 的问题/目标前提，最终门统一确认 | premise gate deferred | G2 | 不在 broad review 重开已批准偏好；新事实另列 finding |
| AD-2 | CEO | 继续 same-file overlay，不改整文件懒迁 | automatic | P1 completeness | 同时满足历史 bytes 与活 item mutation |
| AD-3 | CEO | shared envelope 以目标态 producer 组合性评判 | automatic | 通则③ | 当前语料缺席不能否决目标 |
| AD-4 | Eng | 接受 E-1..E-6 进入 amendment 候选 | automatic | explicit over clever | 都有可核代码/标准证据 |
| AD-5 | DX | 接受升级文档、advisory help、fix-directed diagnostics | automatic | fight uncertainty | 不改变成功 API，降低恢复成本 |
| AD-6 | DX | diagnostic JSON/doctor/lock recover/Windows CI 暂不自动扩 scope | taste/defer | G2 | 交最终多镜裁决，报告给推荐与三面后果 |

## 7. Outside voice（design-voice fallback）

跨模型 Claude runner 按 helper 契约运行到真实 300 秒超时，未返回 findings；随后用 helper 的同一 prompt 回落 fresh Codex 子代理，收到 3 条 finding。该段是**同族降级**，不是跨模型第二意见。

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="codex" runner="codex" reason_code="timeout" findings="3" truncated="false" -->

| ID | Finding | 严重度 | broad 裁决 |
|---|---|---|---|
| OV-1 | overlay 中 frontmatter/marker-owned item 与未 promotion legacy item 的 relation 检查未明确分区；marker-only 新 bug 会被旧“块有 ID 但表无行”误报 | high | **采纳**：effective owner=frontmatter 的 ID 不参与旧表↔块/status 双写检查；未 promotion legacy ID 继续旧规则；marker ownership 冲突 fatal。 |
| OV-2 | 锁起点若只写“第一次业务文件读取”，可能把 `list_files/exists/stat/glob` 留在锁外，产生枚举后插入窗口 | high | **采纳**：除 `repo_root` 外，一切影响 snapshot 的 discovery/stat/open 均在 owner acquire 或 participant 校验后。 |
| OV-3 | dated writer 仍可能走 text I/O，破坏 EOL/BOM bytes | high | **裁掉（已覆盖）**：`design.md:135-157` 与 tasks 2.1/5.3 已明确 single binary read + `atomic_write_bytes`，INDEX/batches 才保留 text helper；后续接地镜验证引用是否完整。 |

## 8. Broad-review completion

- CEO：7 findings（2 采纳、2 部分、3 裁掉/待裁决）。
- Design：skipped，无 UI scope。
- Eng：6 findings，全部进入最终多镜裁决。
- DX：8 findings，3 采纳、2 部分、3 待最终裁决。
- `NOT in scope`：full YAML/PyYAML、批量迁移、remote tracker、power-loss durability、network filesystem 保证、遥测。
- `What already exists`：现有 `atomic_write`、legacy parser/problem 分层、CLI/JSON contract、reindex strict、mirror AST guard 均复用，不重建平行入口。
- outside voice：跨模型 timeout；同族 fallback 3 findings（2 采纳，1 已覆盖裁掉）。
- broad review 结论：**有实质 amendment 候选，不能直接放行；进入 sdflow 多镜前先 checkpoint 本报告。**
