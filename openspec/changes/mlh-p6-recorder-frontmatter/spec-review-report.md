<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="codex" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-06,TG-16,TG-26" declared="TG-05,TG-06,TG-10,TG-11,TG-13,TG-14,TG-15,TG-16,TG-18,TG-19,TG-20,TG-21,TG-23,TG-26" evidence="proposal 触发判定命中三脚本共享契约、单次解析性能与并发写入时序" -->

# Spec Review Report — mlh-p6-recorder-frontmatter

> `[spec-review-amendment]` 2026-07-16。阶段二连续评审：autoplan 广审 → 对抗镜×3 + 接地镜×1 → HR-TG outside voice → 主 session 合并裁决。对象为 `proposal.md`、`design.md`、两份 delta spec、`tasks.md`、ADR-0025、CONTEXT 术语与真实 recorder/init 代码。

## 结论

**建议进入设计 HARD-GATE，但不能把 grill 版本原样批准。** 多镜发现 15 组有效缺口，其中 11 组是无需偏好判断的技术闭合，已直接回灌；4 组涉及新架构/支持边界，已按调研后的推荐方案预写入文档，须在本报告设计门一次确认。

没有待用户代查的事实问题。当前仍是设计文档修订，未实施 recorder 代码。

## 执行与独立性

- Step1：原生执行 autoplan 方法，fresh CEO / Eng / DX 三审；无 UI，Design phase 跳过。广审产物已 checkpoint 为 `2b595b7`。
- Step2：Codex capability probe 真派出并收到 `PROBE_OK`；随后同轮并行对抗镜 3 个、接地镜 1 个，均为 fresh context，prompt 原文携带三条通则。
- 领域镜：proposal 明确 Python CLI + Markdown/YAML，无 backend/embedded/frontend 命中，故未伪造 domain 镜。
- HR-TG：确定性交集为 `TG-06/TG-16/TG-26`。
- 两个 Claude outside voice 都真实运行至 300 秒 timeout；均按 helper 同 prompt 回落 fresh Codex，因此本轮**没有跨模型第二意见**，只有可审计的同族 fallback。

## 决策登记区

### 自动决策

| ID | 决策 | 理由 | 落档 |
|---|---|---|---|
| D1 | 共享 envelope 定义整个 v1 lexical profile，不再只说“opaque/歧义拒绝” | 不定义顶层 key/span grammar，三份 scanner 无共同可验收边界 | design D1a、SW-RI-1、tasks 1.2/1.3、ADR-0025、CONTEXT |
| D2 | promotion 前扫描 legacy block 内精确 marker；命中即写前拒绝 | “内部 bytes 不变”与“marker 不嵌套”否则可由一次成功 mutation 自造坏盘面 | SW-RI-1、tasks 1.4/2.4 |
| D3 | ID grammar 改 ASCII `[A-Z][1-9][0-9]*`；孤立 `A007` 只作 legacy alias，promotion 输出 `A7` | Python `\d` 接受 Unicode digits；raw/canonical 身份原未定义 | design/ADR/CONTEXT、SW-RI-2、tasks 3.1/5.4 |
| D4 | overlay relation 按 semantic effective owner 分区；scan JSON consumer 严格验 envelope/item | 避免 frontmatter-only item 被旧双写检查误报，也避免 partial install 被 `.get(..., [])` 静默吞成空池 | SW-RI-1/3、DG-RI-1、tasks 2.2/5.5 |
| D5 | lock 在所有 result-affecting discovery 前获取；participant 仅向 allowlist recorder child 受控转发 | `sweep→reindex→scan` 有两层 subprocess；“首次业务 read”留下枚举窗口 | D3、SW-RI-2、tasks 3.3/3.5 |
| D6 | release 承诺收窄为 cooperative identity+token best-effort；终检后外部替换 race 明示残余 | 普通 path API 没有 compare-and-unlink，不能声称绝不误删替代路径 | D3、SW-RI-2、ADR-0025 |
| D7 | 同 dated document 的合规 sibling producer 共享 `.recorder.lock`，replace 前做 snapshot fingerprint 终检 | namespace 所有权分离不等于整文件 replace 可各用各锁，否则后写覆盖先写 | D1a/D3、SW-RI-2、tasks 3.5 |
| D8 | runtime ignore 真相源固定 `assets/snippets/runtime-gitignore.txt`，由 `init.py::run()` init/update 两路合并 | 仓内没有现成 merge path，笼统“新增 canonical asset”不可实施 | design、SW-RI-2、tasks 3.6 |
| D9 | 新 fatal error 使用 stderr `ERROR: problem; cause: cause; fix: action`，JSON stdout 纯净 | 已有 path/reason 不足以完成 stale lock/rename 恢复；不需新增 API | SW-RI-1、tasks 1.3/5.4 |
| D10 | 删除不存在的 `batch query` 假接口，锁清单写实际 `batch lint/add/set-status/rename` | `issues.py --help` 与 parser 只有这四个入口 | design、SW-RI-2、tasks 3.3 |
| D11 | rename 中与 retag 无关的 legacy nonfatal problems 回显但不阻断；任何判定/写/派生失败非零 | 与默认 reindex 语义对齐，同时删除真正的 warning-only 假成功 | D4、SW-RI-3、tasks 4.4 |

### 需拍板（推荐已写入文档，未批准前仍为 Proposed）

#### Q1 — batch rename 的一次读取实现协议

**推荐 A：`issues.py::read_rename_snapshot()` 直接一次 binary read/parse 两池 dated files。** 它保留 raw bytes/spans/model，retag 和 reindex 复用同一 snapshot；整个 rename 每 dated file read/parse=1、per-pool `scan --json`=0。

- 系统后果：真正满足 T66 与 bytes splice；代价是 issues.py 也要具备 legacy/overlay parser 行为。
- 用户后果：CLI 不变，rename 更确定；不会因 text 二读规范化 BOM/EOL/sibling bytes。
- 开发循环后果：三向行为 golden/roster 变大，但仍无跨 skill runtime import。
- 备选 B：长生命周期 per-pool participant RPC 保留 snapshot——少复制 parser，但引入私有进程协议、生命周期与失败恢复，复杂度高于收益。
- 主次判定：系统正确性和可验证单读优先，推荐 A。

#### Q2 — rename retry provenance

**推荐 A：registry-first，并在 target `batches.md` entry 写 machine-owned `重命名自: old`。** 首次先严格预检，再原子改 registry + provenance，随后 retag/reindex；只有 provenance 精确匹配时允许 source 缺失的 retry。

- 系统后果：所有 crash cut 可区分；未知 source、预存 orphan 不会被误吸收。代价是 batches grammar 多一条 generated field。
- 用户后果：仍重跑原命令，无 `--resume`；Git 中多一条可读审计来源。
- 开发循环后果：状态矩阵改成 registry/provenance × items，测试更多但无需 stale sidecar cleanup。
- 备选 B：sidecar journal——证明力强，但多一个忽略文件/跨机器恢复真相源；备选 C：裸盘面——简单但无法区分误输与 retry，已证伪。
- 主次判定：fail-closed 与同命令恢复优先，推荐 A。

#### Q3 — stale/partial lock 恢复

**推荐 A：不新增自动 `lock recover`，使用 fix-directed manual break-glass。** metadata 完整时显示 repo/PID/command/start；空白/部分 metadata 时明确要求先停止该 repo 全部 recorder owner/participants，再删精确 lock path并重跑。

- 系统后果：不把 PID/file existence 伪装成 liveness lease；代价是 crash 后权威读写会阻塞到人工处理。
- 用户后果：恢复步骤更长但不误杀活锁；错误文案可直接复制。
- 开发循环后果：无需第二套 recovery command/API，需覆盖 stale/partial/PID reuse 风险的诊断测试。
- 备选 B：自动 recover/TTL——体验短，但跨平台无法可靠证明 owner 已死；备选 C：引入 OS file lock——自动释放，但破坏已选跨平台 `O_EXCL` 协议并扩大 scope。
- 主次判定：不制造假安全优先，推荐 A。

#### Q4 — 平台与 durability 支持矩阵

**推荐 A：macOS/Linux 本地 filesystem 为自动 release gate；Windows 本地盘为必须 smoke 的兼容目标；network FS 与 power-loss durability 明确 unsupported/non-goal。**

- 系统后果：保证层级与实际原语一致；POSIX mode bits 不误投射到 Windows。
- 用户后果：Windows 有明确 smoke 证据；NFS/SMB/FUSE 用户不会被“跨平台原子”误导。
- 开发循环后果：新增 Windows runner smoke，但不需要在本 change 建完整多平台 CI 产品线。
- 备选 B：只支持 POSIX——最省测试但收窄现有跨平台安装预期；备选 C：宣称所有 filesystem——无法由 `O_EXCL/os.replace` 普遍证明。
- 主次判定：诚实保证 + 现实兼容优先，推荐 A。

### 已裁掉（保留原始意见与理由）

| ID | 原始意见 | 裁掉理由 |
|---|---|---|
| X1 | 把 frontmatter 与 lock/rename 拆成两期 | 新 writer 上线后继续保留 ID/lost-update 竞态，不是按依赖切分；范围大不能单独作为目标缩水依据 |
| X2 | 普通 scan 不加锁 | 目标态成功 snapshot 必须对应无 cooperative writer 穿越的时点；锁已收窄到 materialize，stdout 前释放 |
| X3 | 当前没第二 producer，所以 recorder 独占 envelope | 违反目标态基准；多 producer 是设计目标，不以当前语料缺席否决 |
| X4 | 加 `doctor --json`、diagnostic JSON、自动 lock recover | 现有 scan/reindex + fix-directed stderr 已覆盖本 change 诊断；新增平行 API/恢复协议未证明必要 |
| X5 | 全面重做 Windows installer 原子发布 | 本 change 需要 protocol/install smoke，不需要重构整个 installer；后者范围独立 |
| X6 | dated writer 可能回退 text I/O | 已由 design bytes boundary、tasks 2.1/5.3 与 call-graph test 完整覆盖；重复 finding 不再加第二套 amendment |

## 采纳 findings 合并表

| Finding | 来源镜 | 严重度/置信 | 裁决与 amendment |
|---|---|---|---|
| shared envelope span grammar 未定义 | broad Eng + 对抗1 + 接地 | HIGH / 高 | D1：全-envelope lexical profile + 接受/拒绝 byte fixtures |
| legacy block 预存 marker 会被包成嵌套坏盘面 | 对抗1独立 | HIGH / 高 | D2：promotion 写前 marker collision scan |
| `\d` 接受 Unicode digits | 对抗1独立 | HIGH / 高 | D3：ASCII grammar/`re.ASCII` |
| isolated `A007` promotion 身份不明 | broad Eng + 对抗3 | HIGH / 高 | D3：raw alias→canonical key/marker/result |
| overlay relation 未按 effective owner 分流 | design-voice fallback 独立 | HIGH / 高 | D4：frontmatter-owned/legacy-owned validation partition |
| scan JSON 缺键可被当空池 | 对抗3独立 | HIGH / 高 | D4：producer-consumer strict contract |
| lock acquisition 晚于 discovery | design-voice fallback 独立 | HIGH / 高 | D5：root/纯参数后立即 acquire |
| nested participant token 委派未定义 | 对抗3独立 | HIGH / 高 | D5：同 repo allowlist 原样转发、其它 env 剥离 |
| release token check→unlink 仍有 TOCTOU | broad Eng独立 | HIGH / 高 | D6：identity+token best-effort + residual boundary |
| sibling producer 可被 stale whole-file replace 覆盖 | hr-tg fallback 独立 | HIGH / 高 | D7：shared document lock + fingerprint conflict |
| metadata 前 crash 无 owner 可核验 | 对抗2 + 对抗3 | HIGH / 高 | Q3 推荐 manual break-glass |
| rename scan JSON 后再 retag，无法 whole-command read=1 | 接地 + hr-tg fallback | HIGH / 高 | Q1：issues direct raw snapshot |
| rename 无 provenance，误输盘面与 retry 同构 | 对抗2 + broad Eng | HIGH / 高 | Q2：registry-first `重命名自:` |
| rename 与默认 reindex nonfatal 语义未分层 | 接地独立 | MEDIUM / 高 | D11：unrelated nonfatal 回显；任何收敛失败非零 |
| runtime ignore 无 init/update integration path | 接地独立 | HIGH / 高 | D8：canonical asset + exact merge function/path |
| `batch query` 不存在 | 接地独立 | MEDIUM / 高 | D10：改成真实四入口 |
| breaking docs/consumer smoke/next-id advisory 缺验收 | broad CEO+DX + 接地 | HIGH / 高 | README/SKILL/help + known consumer/Windows smoke |
| atomicity、platform、durability 保证层级混用 | broad Eng+DX + 接地 | MEDIUM / 中高 | Q4 支持矩阵 |
| errors 不够 fix-directed | broad DX + hr-tg fallback | MEDIUM / 高 | D9 三段式 stderr；不新增 API |

## HR-TG outside voice

Claude runner 在 `hr-tg` site 真实超时，helper 同 prompt fallback 返回 3 条：direct rename snapshot、sibling producer lost update、可操作诊断。三条均采纳并回灌。

<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="codex" runner="codex" reason_code="timeout" findings="3" truncated="false" -->

Autoplan design-voice 同样为 Claude timeout → Codex fallback，返回 validation partition、lock discovery、bytes pipeline 三条；前两条采纳，第三条因已完整覆盖裁掉。

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="codex" runner="codex" reason_code="timeout" findings="3" truncated="false" -->

## Amendment inventory

- `proposal.md`：storage/ID compatibility、direct rename snapshot、shared producer lock、platform/non-goals。
- `design.md`：D1a lexical/write coordination、D2 owner partition/raw promotion、D3 lock/recovery/platform、D4 direct snapshot + registry provenance、NFR/failure modes。
- `specs/spec-workflow/spec.md`：binding scenarios for grammar、marker collision、ASCII ID、JSON contract、delegation/shared producer、break-glass、provenance rename。
- `specs/determinism-guards/spec.md`：issues direct snapshot 的三向行为 golden 与 consumer validator。
- `tasks.md`：可执行 parser/lock/rename/docs/platform/consumer tests，所有新增项标 `[spec-review-amendment]`。
- `openspec/adr/0025-...md` 与 `openspec/CONTEXT.md`：稳定决策/术语回灌；ADR 仍 Proposed。

## 不利影响与残余后果

- strict lexical profile 会拒绝一部分合法 full YAML；这是零依赖窄 scanner 与 byte-preserving splice 的明确兼容代价。
- `issues.py` 为 whole-command single-read 复制更多 legacy/overlay 行为；维护面由三向 golden/AST guard 承担。
- shared `.recorder.lock` 使不同 namespace 的合规 writer 也串行；换来不丢 sibling update。
- crash 尤其 metadata 前 crash 会把全部权威读写阻塞到人工 break-glass；这是拒绝不可靠自动偷锁的代价。
- `batches.md` 新增 machine-owned `重命名自:` 行；registry diff 变大一行，但 retry 不再靠猜。
- pure legacy `A007` 首次 mutation 后对外变为 `A7`；旧表 bytes 保留，升级说明必须提示这一可见 canonicalization。
- Windows 只以 local-disk smoke 承诺；network FS 与断电 durability 明确不支持，避免把未验证层级包装成跨平台保证。

## Lens metrics（pre-gate 草稿）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="codex" runner="codex" site="—" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="5" sev="致0/高8/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="codex" runner="codex" site="—" findings="14" 采纳="8" 裁掉="4" defer="2" 独立="4" sev="致0/高5/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="codex" runner="codex" site="—" findings="6" 采纳="5" 裁掉="0" defer="1" 独立="3" sev="致0/高3/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="codex" runner="codex" site="design-voice" findings="3" 采纳="2" 裁掉="1" defer="0" 独立="2" sev="致0/高2/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="codex" runner="codex" site="hr-tg" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致0/高2/中1/低0" -->

计数归约由 emitter 完成；finding 分类、roster 完备与誊写仍是主 session 信任边界。本 skill 只落锚，不聚合/复评；跨 change 反馈由 `sdflow-retro` 负责。设计门若翻改 Q1–Q4，拍板回写时须同步重算这些 pre-gate 草稿锚。

## HARD-GATE 建议

**建议按 Q1=A、Q2=A、Q3=A、Q4=A 批准。** 批准后主 session 才会在本报告首部写 `ship-gate.design_approved: true`，补人读拍板记录并最终化 lens metrics；随后下一步才是 writing-plans / 实现计划。
