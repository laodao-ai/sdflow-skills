# Task 1 — per-run 不可变 context 路径与 dispatch manifest（R1）

## 做了什么

改两个评审 SKILL 的「outside-voice helper 调用协议」节里的 context 构造说明（纯 Markdown 指令，无脚本改动）：

- `sdflow-spec-review/SKILL.md:272`
- `sdflow-code-review/SKILL.md:270`

两处替换为**逐字相同**的四行块（站点枚举行仍各自不同，留在块外）：

1. 本轮起手定一个 run-id（`date -u +%Y%m%dT%H%M%SZ`），本轮全站点共用、定后不变；
   context 写 `{change_dir}/.outside-voice/<run-id>/<site>-context.md`。
2. **per-run 不可变**：同 run-id 下每站点只写一次，写完不改不删；后续轮次换新 run-id，
   MUST NOT 复用或覆盖既有 run 目录（helper 的入境扫描与渲染是两次独立读 → 不可变路径令二者恒对同一快照，闭跨会话 TOCTOU）。
3. **父目录 MUST 仍在 `{change_dir}/.outside-voice/` 下**〔G5〕，附 `.gitignore` 递归覆盖的理由。
4. **dispatch manifest（F-I）**：每次实际发起 voice 追加一行到
   `{change_dir}/.outside-voice/<run-id>/dispatch-manifest.tsv`，格式 `<site>\t<task_id>\t<UTC ISO8601>`
   （后台派发记后台任务标识；同步 exec 记 `sync`）；「是否真派发过某站点」以本文件为准，MUST NOT 靠会话记忆。

按 DOC-1，正文只写最终态，未在指令里留「原先是固定命名」的考古层。

## 面治扫描（不止那两行）

全仓 grep `\.outside-voice`、`固定命名`、`下轮覆盖`（排除 `openspec/changes/`）：

- 旧口径「固定命名、下轮覆盖」在 skill / 脚本 / 文档中**已无残留**（唯一剩余命中是
  `openspec/issues/todolist/2026-07-todolist.md:563` 的 8 项合集里的第 ③ 条「同 change 并行评审 context
  文件互踩（固定命名无锁）→ 加运行 ID 后缀或 flock」——那是**待办描述**，其余 7 条未落地，故不标 DONE）。
- `outside_voice_guard.py` / `openspec/specs/outside-voice-reuse-guard/spec.md` 里的 `.outside-voice/`
  提法**无需改**：新鲜度用的是 **inclusion allowlist**（`SOURCE_FILES` = proposal/design/tasks + `specs/**`
  递归，见 `openspec/workflow/tools/outside_voice_guard.py:103-120`），per-run 子目录天然不在 allowlist 内，
  多一层目录不改变行为。
- `outside-voice.sh` 本体未动（Non-Goal）。

## 验收标准逐条证据

### ① 两层评审流程 context 构造均改为 per-run 不可变路径，父目录仍在 `.outside-voice/` 下

```
$ grep -n "run-id" sdflow-spec-review/SKILL.md sdflow-code-review/SKILL.md
sdflow-spec-review/SKILL.md:272:context 构造…{change_dir}/.outside-voice/<run-id>/<site>-context.md
sdflow-code-review/SKILL.md:270:context 构造…{change_dir}/.outside-voice/<run-id>/<site>-context.md
```
两处块文本逐字相同（站点行除外）。

### ② 旧口径无残留

```
$ grep -rn "固定命名\|下轮覆盖" --include="*.md" --include="*.py" --include="*.sh" . | grep -v openspec/changes/
openspec/issues/todolist/2026-07-todolist.md:563:…（待办条目本身，见上）
```
skill / bundle / 脚本零命中。

### ③ dispatch manifest 落盘

指令层已定死路径 `{change_dir}/.outside-voice/<run-id>/dispatch-manifest.tsv` 与三列格式，
并明确「追加」语义 + 「MUST NOT 靠会话记忆」。真实写入发生在后续 dispatch 票（本票是地基）。

### ④ gitignore 递归覆盖实测（让 git 自己回答，不靠推理）

```
$ RUN=20260718T000000Z; D=openspec/changes/async-outside-voice/.outside-voice/$RUN
$ mkdir -p "$D" && echo x > "$D/design-voice-context.md" && printf 'design-voice\tsync\t…\n' > "$D/dispatch-manifest.tsv"
$ git status --porcelain
 M sdflow-code-review/SKILL.md
 M sdflow-spec-review/SKILL.md          ← 新建的两个文件均未出现
$ git check-ignore -v "$D"/*
.gitignore:19:**/.outside-voice/	openspec/changes/async-outside-voice/.outside-voice/20260718T000000Z/design-voice-context.md
.gitignore:19:**/.outside-voice/	openspec/changes/async-outside-voice/.outside-voice/20260718T000000Z/dispatch-manifest.tsv
$ git add -A --dry-run
add 'sdflow-code-review/SKILL.md'
add 'sdflow-spec-review/SKILL.md'       ← checkpoint 的 add -A 不会卷入 per-run 目录
```
（测试目录事后已 `rm -rf` 清除。）

## 全套件

```
$ pytest -q
1619 passed, 2 skipped in 75.24s
$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致
```

## 遗留 concerns

1. **`proposal.md:27` 仍写旧路径形态** `.outside-voice/<site>-context.md`（TG-26 并发面描述段）。
   未改动——实现期改 change 四件套会触 `ship_gate` 设计门失鲜 `REFUSE_START`。建议由编排层在
   done/archive 阶段一并校正，或明确认定该行是「按站点分文件」的粗粒度表述、不构成旧口径残留。
2. **run-id 由模型现场生成**（`date -u` 取值），无机械门守「是否真的每轮换新」。这属于设计既有的
   指令层诚实边界（同外层 timeout 那类）；若后续想机械化，可在 anchor_lint 家族里加「manifest 存在性」核。
3. **两 SKILL 的协议节整体仍逐字重复**（todolist T:563 ①），本次改动又增 3 行重复面。
   下沉 bundle 单一源是既有待办，未在本票 scope 内；ADR-5 的 `check_async_branch_parity.py`
   （Task 后续票）会覆盖 async 段，但**不覆盖本次这段 context 构造块**——若希望它也被字节等值门守，
   需在后续票里决定是否把该块纳入 marker 范围（当前设计明确「context 构造留 marker 外」，故按设计不纳入）。
