---
ship-gate:
  code_review: pass
---

## code-review 报告 — harden-repo-root-fail-closed

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-08" declared="TG-08,TG-18,TG-19,TG-22,TG-23" evidence="repo_root 消费 git rev-parse 的 stdout 并把结果当可写仓根交给 makedirs——本 change 全部内容即重新定义对该外部依赖的信任边界" -->
<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="8" 采纳="5" 裁掉="0" defer="3" 独立="4" sev="致0/高4/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高0/中0/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致0/高1/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="3" sev="致1/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="1" sev="致0/高2/中0/低0" -->

## 结论（先说）

**建议进 `/sdflow-done`。** 但这轮代码审的结论不是「基本没问题」——它**推翻了本 change 已通过设计门的核心判据**。

冷层抓到一条 **Critical**：祖先校验只证明「`top` 是 `start` 的祖先」，**没证明「`top` 是 `start` 的最近仓根」**。
`core.worktree` 指向**外层祖先仓库**时，四项判据全部放行，recorder 写进外层仓。
**我已亲自复现**。判据因此从 6 步扩到 **9 步**，两轮 fix 后所有 Critical/High 已闭合。

## 命中范围

| 项 | 值 |
|---|---|
| 栈 | Python 脚本 + pytest |
| 清单 | base **CR-01~09**；🔴 **领域 delta 未覆盖**——`domains/` 只有 backend-go / backend / embedded-*，本仓栈无对应清单（已知缺口，非本轮遗漏） |
| diff base | `24811c2b`（`merge-base origin/main HEAD`） |
| trivial_shape | `NOT_EXEMPT`（`non-doc-markdown:CLAUDE.md`）⇒ 照常 fan-out |
| HR-TG ∩ | `{TG-08}` 非空 ⇒ 单开领域专属 cross-model |
| 全套件 | **1910 passed / 9 skipped / 3 xfailed / 0 failed** |

### Step1 广审：`mode="simulated"`（如实标注，非原生）

**未经 Skill 机制原生执行 gstack `/review`**，改由子代理做同口径的 scope-drift + 完成度审计。
**这是降级，不是等价**——按 skill 的 sanctioned 降级路径处置并显著标注，MUST NOT 读作原生。

### 镜编排

| 镜 | 数 | 结论 |
|---|---|---|
| 领域镜 | 1 | 4 条（1 高 / 1 中 / 2 低） |
| 对抗镜 A（并发与资源） | 1 | **refuted=true 维持**——四条攻击线全实测证伪；另据实登记 2 条存量 |
| 对抗镜 B（错误路径） | 1 | 2 条真复现（1 高 / 1 中） |
| 对抗镜 C（守护自身可靠性） | 1 | **3 条「退化了但全绿」**，全部真跑复现 |
| 历史镜 | 1 | 无 Critical/High；3 条正面确认 |
| outside-voice ×2 | 2 站点 | code-voice 4 条（含 2 Critical）· hr-tg 3 条 |

**能力探针**：`host=claude` ⇒ 免探，`subagents="available"`。
**后台能力**：探针 `PROBE_OK` + 主 session 已确证 ⇒ voice 走 **async 分支**，内层 `--timeout 900`（config 键被注释 ⇒ 回落默认）。
**voice 首次 dispatch 失败**（run-id `20260719T152512Z-wheZcF`）：`.rc=1`，诱因为**调用方错误**——`SDFLOW_VOICE_RUNNER` 未 export（harness 每次 Bash 调用是独立 shell）。按 run-id 不可变纪律保留失败证据，新建 `20260719T152647Z-VdyEHo` 重试，两站点均 `.rc=0`。**该协议坑本 session 内第二次踩中（阶段二同款）⇒ 已登记 T184。**

**code-voice context 裁剪声明**：全量 diff 466KB，排除 `openspec/changes/*/impl-reports/`（实现期过程报告，占比 90%+）后 328KB。**全部代码、测试、四件套、`CLAUDE.md`、`conftest.py`、`pytest.ini` 均在内。** 仍 `truncated=true`（丢弃 123506 字节）。裁剪目的是不让过程产物挤占截断预算把真代码挤掉。

---

## Findings（置信 ≥80）

### 🔴 核心：判据不足（4 个独立来源收敛，已修）

| # | 问题 | CR | 证据 | 严重度 | 处置 |
|---|---|---|---|---|---|
| **C1** | 祖先校验未证明**最近**仓根 ⇒ `core.worktree` 指向外层祖先仓库时静默放行，写进外层仓 | CR-02 | code-voice；**编排层亲自复现** | **致命** | 已修 `[impl-review-fix]` |
| **C2** | 同形变体：PATH 注入 fake git 返回外层仓 ⇒ 四项判据全过 | CR-02 | hr-tg | 高 | 同 C1 一并修 |
| **C3** | git 非 0 退出**一律回落** ⇒ 仓内静默写错地方。**高频触发面是 `detected dubious ownership`（safe.directory）**——容器/CI 里 git 常态性 rc=128 而进程确实在仓内 | CR-02 | hr-tg + 对抗B + 领域镜（**3 源**）；领域镜实测 rc=128 → 返回**子目录** | 高 | 已修 |
| **C4** | 回落值 → `recorder_lock` → `makedirs` 抛 `OSError`（非 `ValueError`）⇒ `main()` 接不住 ⇒ **裸 Traceback + exit 1**；可写目录下**静默建树**（`cd ~ && buglist add` → `~/openspec/issues/`） | CR-01 | 对抗B，三份全复现 | 高 | **在仓内的一半已修**；非仓库+不可写的一半 → **B17** |

**修法**：判据 6 步 → **9 步**。新增 ④ 从 `start_real` 做**不依赖 git** 的最近 `.git` 上溯（`os.path.exists`，故 linked worktree / submodule 的**文件**形态 marker 也算）；⑤ 裁决 git 失败（**有 marker ⇒ raise；无 marker ⇒ 才回落**）；⑨ 要求 `marker_dir == top_real`。

**一处有意的行为变更**：起点在 `.git/` 内部时现在 fail-closed——旧行为返回 `.git/hooks` 当可写根，**会建出 `.git/openspec/issues/`**。

**合法场景零误伤**（接缝复审逐个真跑）：linked worktree / submodule / 仓子目录 / symlink / **嵌套仓正常情形（从 inner 起返回 inner，未被外层劫持）** / 非 git 回落 / bare / `--separate-git-dir` / `start=/` / `$HOME` 无仓。

### 🔴 守护自身部分是假的（对抗镜 C，全部真跑复现，已修）

| # | 问题 | CR | 严重度 | 处置 |
|---|---|---|---|---|
| **C5** | 门 A 只认接收器名字面量 `monkeypatch` ⇒ 对 `mp = monkeypatch` / `MonkeyPatch()` / `MonkeyPatch.context()` **完全失明**。退化站点写成 `mp.setattr(...)` 后两道门 `7 passed`、文件 `91 passed` 全绿 | CR-09 | 高 | 已修：判据放宽为「任意 `<expr>.setattr` + 实参指向 `subprocess.run`」+ 三种别名钉成自检语料 |
| **C6** | 任一 skill 目录出现带 pytest 段的 `pyproject.toml`/`tox.ini` ⇒ **rootdir 被抢** ⇒ confcutdir 同塌 ⇒ 仓根 `pytest.ini` + `conftest.py` **双双出局**，泄漏探针 `1 passed`（静默失效） | CR-09 | 高 | 已修：加守护存活自检 |
| **C7** | xfail 锚的**前提断言在 xfail 体内** ⇒ 前提烂掉也计入 xfail、照样绿，且摘要仍打印 R2 说明误导读者 | CR-09 | 中 | 已修：前提核验外提为独立非 xfail 用例 |

> 对抗镜 C 给的判断值得当设计原则：**「守护必须能回答『我现在活着吗』，否则它的失效永远无声。」**

### 其他已修

| # | 问题 | CR | 严重度 |
|---|---|---|---|
| **C8** | `text=True` 无 `encoding` ⇒ Windows cp1252 下 stdout 可为 `None` ⇒ `.rstrip` 抛 `AttributeError`（非 `ValueError`）⇒ 裸 Traceback。**仓内自己的 Windows 测试文件里就记着这个坑的证据** | CR-01 | 高 |
| **C9** | 仓根 `conftest.py` 用 `@pytest.hookimpl(wrapper=True)`（**pytest 8+ 才有**），而 `pytest.ini` 无 `minversion`、两 CI 都是裸 `pip install pytest` ⇒ **pytest 7 下全仓收集直接崩**（影响全部用例，不止本 change） | CR-09 | 中 |
| **C10** | 诊断把「显式指定 `--root`」当修复手段，而显式 `--root` **仍走同一次 git 探测** ⇒ 用户照做仍得到相同错误 | CR-01 | 中 |
| **C11** | Windows 跨盘符时 `commonpath` 自抛的 `ValueError` 不带 `ERROR/cause/fix` 三元组 | CR-01 | 低 |
| **C12** | `timeout=30` 裸魔法数 → 函数体内局部常量（保持在 AST 镜像覆盖内） | CR-08 | 低 |

---

## 已裁掉 / defer（反静默压制：原始发现 + 理由，可审计）

| # | 原始发现 | 去向与理由 |
|---|---|---|
| **X1** | 对抗镜 A：锁文件在持锁进程被 SIGKILL 后**永久残留**，后续调用永久拒绝（实测 `PERMANENTLY BLOCKED`） | **存量，不在本 diff 内**——对抗镜自己判定并据实登记。**未计入本轮 finding**（判断正确） |
| **X2** | 对抗镜 A：`_ACTIVE_RECORDER_TOKEN` 复位在 `args.func(args)` 之后、异常路径跳过 | **存量**；但本轮给出了比阶段二更硬的证据：**测试进程内实测残留**（跑完两文件后 token 仍为 `42468581...`），后续 `recorder_child_env()` 会把它注入子进程 env ⇒ **影响面比阶段二「CLI 单发进程无害」的判断大**，是 order-dependent 幽灵故障的材料 |
| **X3** | code-voice：回落用词法 `abspath`，symlink+`..` 起点下 ≠ git 实际探测目录 | **defer → T181**。⚠️ 对抗镜 A 实测补充：`recorder_lock` 入口即 `realpath` ⇒ **锁这一侧被兜住，方向安全**。但**广审提请注意**：T181 的 defer 理由是「改 spec 会令设计门失鲜」——**这是流程约束、不是安全论证**，设计门须显式确认 |
| **X4** | 对抗镜 B：`sdflow-maintain/scripts/maintain_scan.py:19 find_repo_root` 是同一片面上的**第四份实现**，三条判据全缺（实测：cwd 删除 → 裸 Traceback；linked worktree 下静默爬到外层仓） | **defer → buglist**。⚠️ **Task 6 的面治扫描漏了它，因为扫描关键词是 `show-toplevel`，而这一份靠向上找 `.git` 实现** ⇒ **扫描口径本身太窄**，这是比漏一处更值得记的教训 |
| **X5** | hr-tg：`capture_output=True` 对 **stderr** 同样无界，design Non-Goals 只把 stdout 列为 DoS 面 | **defer → todolist**（与 tasks 4.8 同族，合并登记） |
| **X6** | C4 的另一半：非仓库 + **不可写**目录 → 裸 Traceback | **defer → B17**。此处 `repo_root` 回落**是对的**（上方确无 marker），缺陷在下游 `makedirs`。**诱人的修法是错的**——给 `repo_root` 加可写性闸门会打断 `next-id`/`scan` 在只读目录的合法使用。**`repo_root` 负责解析，不负责授权** |

**<80 置信滤除项（一行带过，不静默丢）**：`premise-verification.md` 的 proposal 叙述失真（读起来像既存文件，实为 grill 期落盘，Info）；报告单文件基线数字 `44 vs 45` 的笔误（Info，结论不受影响）。

---

## 修复 / defer 台账

- **自动修 12 项** `[impl-review-fix]`：C1–C12，分两轮（`ce133cc` 核心判据 + `260c9c2` 剩余 High/Medium）。
- **两轮各做变异确认**（PV 规则 5）：接缝复审**独立重做 2 处**，红的用例集与报告逐字一致。
- **defer 6 项**：T181 · T184 · B15 · B17 · maintain_scan → **B18** · stderr DoS → **T185**。
- **T10 复核**：本轮无「无客观判据的 ≥2 方案」——C1 的修法由两个跨模型 voice **各自独立**提出同一形状，且接缝复审逐场景实测验证无误伤，属客观判据可判（T10 ①）。

### ⚠️ 归档前必须处理

1. **spec 回写批次已扩到 11 项**（CF-9 a–k）。⚠️ **a–g 与 h–k 不是同一类**：a–g 是「实现对、措辞旧」；**h–k 是「原判据本身不足、被评审证伪后收紧」**——是对已批准设计的**实质修订**，MUST NOT 在设计门被折叠进「措辞订正」桶。
2. **T184 挂错 change**（实为跑评审时踩到的 workflow 缺陷，与本 change 功能无关）⇒ 会污染本 change 的 sweep 圈选，建议改挂 `main`。受 **T180**（recorder 缺「改已存在项字段」的命令）阻塞，需手工编辑。
3. **CF-9 的数字锚已订正**：原写 `passed+skipped == 1879` 为恒定量，实为会随新增用例变化的量（现 1919）。**恒定量只有 `failed == 0` 与 `xfailed == 3`。**

---

## 元观察

**这轮代码审的价值全部来自「冷」。**

C1 是本 change 的**主防线被绕过**，而它躲过了：3 轮设计返修 + 6 张 ticket 的每票双轴审 + 3 轮接缝复审。
抓到它的是两个**冷跨模型 voice**——它们各自独立地指到同一处，并各自独立地提出了同一个修法。

原因不难看：内部各轮的判据基准，是**这个 change 自己写下的那份设计**。
`core.worktree` 被 ADR-2 立为「祖先校验要防的那个攻击」，于是后续每一轮都在问「祖先校验做对了吗」，
**没有人退一步问「祖先校验本身够不够」**。

同理，对抗镜 C 那三条也不是「代码写错了」，而是**守护的覆盖面比它自己声称的窄**——
门 A 的 docstring 明写覆盖 `monkeypatch.setattr`，而 `MonkeyPatch.context()` **本身就是它**，却全盲。

⇒ **本轮实证：`sdflow-code-review` 不是「高风险才跑的边际残差」（旧 quality-layering §五 已否决），它是承重墙。**

另一条值得留档的观察：本 change 实现期共发生 **5 次**「修复引入新缺陷」，其中 4 次由**返修后的接缝复审**抓到，
1 次（`normpath` 词法归一）由**「被要求补一条测试锚」这个动作**抓到——
**强制走一遍具体路径，比抽象审视更容易撞见问题。**

---

## 结论

- ☑ **建议进 `/sdflow-done`**
- ☑ defer 残差已入 buglist / todolist（B15 · B17 · B18 · T181 · T184 · T185，hand-off 会引用）
- ⚠️ **归档时 MUST 处理上方「归档前必须处理」三条**，尤其 CF-9 的 h–k 属实质设计修订
