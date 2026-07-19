<!-- sdflow:step1-broad-review v1 mode="native" -->

# 广审（autoplan）— harden-repo-root-fail-closed

**native 声明的侧信道佐证**：autoplan 的 preamble 在本 session 真实执行并回显
`BRANCH: feat/harden-repo-root-fail-closed` / `REPO_MODE: solo` / `SESSION_KIND: interactive`
/ `CHECKPOINT_MODE: continuous`；Phase 0 的 UI/DX scope 检测真实跑出 `UI=0` / `DX=57`；
Phase 0.5 的 codex preflight 真实探到 binary + `codex_reviews=enabled`，随后 `codex exec`
真实执行并返回 110,467 tokens 的评审输出。

**阶段执行**：Phase 1（CEO）✅ · Phase 2（Design）**跳过**——UI scope 检测 0 命中 ·
Phase 3（Eng）✅ · Phase 3.5（DX）✅（DX scope 57 命中）。

**双声编排偏离说明**：autoplan 规定「phase 内先 Claude subagent 后 codex，phase 间严格串行」。
本轮三个 Claude subagent（CEO/Eng/DX）**并行派出**——依据是 autoplan 自己对 subagent 的硬要求
「NO prior-phase context — subagent must be truly independent」：它们本就 MUST NOT 携带前序
phase 上下文，故并行不损独立性，只压墙钟。codex 侧仍按串行携带前序语境。

---

## 声音 1：CODEX SAYS（跨模型 · 战略 + 对抗架构）

<!-- sdflow:outside-voice v1 site="broad-review-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="11" truncated="false" -->

runner=codex · model=gpt-5.6-sol · 110,467 tokens · exit 0 · 直调 `codex exec -s read-only`
（autoplan 自带的 codex 编排，非经 `outside-voice.sh`；故 `truncated` 无 helper 的 `OV_TRUNCATED`
信号可取，此处 `false` 依据是收到的输出含完整 1–11 条编号、无中断痕迹）

| # | 严重度 | 置信 | 问题 | 证据 |
|---|---|---|---|---|
| X1 | **critical** | high | **`--root` 显式输入零校验**：argparse 默认普通字符串，坏 `--root` → `subprocess.run(cwd=start)` 抛异常 → 回落 `abspath(start)` → `recorder_lock` 照建目录。本 change 完成后最直接的坏根输入仍 fail-open | `issues.py:2265`、`buglist.py:1554`、`issues.py:1142`、`issues.py:188` |
| X2 | **critical** | high | **`isabs+isdir` 只证明「是既存绝对目录」，不证明「是 start 所属仓库的根」**：污染 producer 可输出 `/tmp`、home 或另一个仓库，全部通过，recorder 写进错误项目 | `design.md:75`、`spec.md:10`、`design.md:14` |
| X3 | high | high | **既有 `except Exception` 会吞掉新抛的 ValueError**：Task 1.1 未写死结构，按最自然的原位改法 raise 被自己 except 接住 → 重新回落 | `issues.py:1142`、`tasks.md:12` |
| X4 | high | high | **Task 1.5 的 CLI 测试触发不了目标分支**：只传坏 `--root` 会导致 git cwd 失败或 rc≠0 → 走正常回落，产生不了「rc=0 + 坏 stdout」。必须 PATH 注入 fake git | `tasks.md:31`、`spec.md:12` |
| X5 | high | high | **root 应只在进程边界解析一次**：main 解析后各 cmd_* 又各自解析（`issues.py:1535`），「try 外调用」应靠结构消除而非 docstring 纪律 | `design.md:113`、`issues.py:2324`/`1535` |
| X6 | high | high | **镜像永久化是症状根源**：guard 覆盖 37 个三向 + 24 个两向 helper，每次修复仍需手工三改。仓内已有 `sync_principles.py` 的「单一源 + 机械注入 + `--check`」先例 | `test_mirror_consistency.py:61`、`hack/sync_principles.py:8` |
| X7 | medium | high | 排除 `_git_root_or_dot()` 的理由是 scope-dodging——「不在 roster」与「是否处于不可信路径边界」无因果 | `proposal.md:55`、`init.py:543`/`882` |
| X8 | medium | high | Task 2.2 变异验证是一次性手工动作，无永久产物，不构成 Success Metric | `tasks.md:48`、`proposal.md:65` |
| X9 | medium | high | 根 conftest 只比顶层条目集，检测不到「修改/删除既存文件」「写入既存目录」；spec 却声称覆盖「一切落盘物」——契约强于实现 | `design.md:116`、`spec.md:70` |
| X10 | medium | high | 「截断 80 字节」不限制**读取量**：`capture_output=True` 先无界读入内存；且 Python 切片是字符非字节 | `issues.py:1143`、`design.md:151` |
| X11 | low | high | 「三份**逐字**一致」措辞强于实际 guard：实为「剥 docstring 后 executable AST 等价」，注释/docstring 可不同，但 **ValueError 消息文案必须一致** | `test_mirror_consistency.py:40`/`104` |

## 声音 2：CLAUDE SUBAGENT（CEO · 战略独立）

| # | 严重度 | 置信 | 问题 |
|---|---|---|---|
| E1 | — | high | **正面确认**：缺陷真实、4 棵垃圾树现场复现、`git status` 确实隐形、假绿诊断坐实。价值定位准确，不是「缝合 4 个目录」 |
| E2 | medium-high | high | **面没扫全**：`sdflow-ship/scripts/ship_gate.py:837` 是同款反模式第 4 个消费点，四件套全篇未提。（实测其有 `--git-dir` 前置兜底 + 全文件无 makedirs ⇒ 后果轻，但「已扫过全仓」这句隐含承诺目前为假，正撞 CLAUDE.md 基准 3「面治优先于点补」） |
| E3 | medium | high | init.py 排除写的是**程序性理由**（不属 roster）而非**安全论证**。实测其消费点只读、包在 `except (OSError, UnicodeDecodeError)`、无 makedirs ⇒ 结论对、论证缺 |
| E4 | — | high | **正面确认**：四条 ADR 的备选否决理由全部带可复现实测；`.github/workflows/mechanical-gates.yml` 确实跑仓根 pytest ⇒ 新 conftest fixture 会被 CI 真实执行 |
| E5 | medium | 中 | 仓根 `conftest.py` 终结了「无根级 pytest 配置」这条既定架构性质。文档已同步（Task 4.4），但**代码侧缺自我边界声明** ⇒ 半年后会被逐步塞满共享 fixture |
| E6 | low | 中 | exit 2 语义复用（坏 root / 坏 scan id）：已扫 4 份 SKILL.md，无脚本按 exit code 分流 ⇒ 当前无外部消费方受影响，记为观察项 |

## 声音 3：CLAUDE SUBAGENT（Eng · 架构独立）

| # | 严重度 | 置信 | 问题 |
|---|---|---|---|
| G1 | **critical** | high | **80 字节截断按字面实现会抛 `UnicodeDecodeError`**——实测复现：`("a"*78+"雪茄").encode()[:80].decode()` 抛错。这会**击穿 spec 自己的「MUST NOT 含 Traceback」**（fail-closed 路径自身先崩）。三份脚本现有诊断从无「截断任意外部输出」先例，无可抄。tasks 1.2 的负例全是 ASCII ⇒ 现有计划抓不到 |
| G2 | medium | high | **「14 个调用点」计数错**：`ast.walk` 精确统计为 **19 处**（issues 7 / buglist 6 / todolist 6），排除 3 处 main 入口后 16。结论不受影响（16 处二次解析均在已验证 root 上，不会新抛），但**一份把 PV 当卖点的提案，自己的验证计数是错的** |
| G3 | medium | high | AST 镜像要求 **raise 消息逐字相同**——实现者出于「让诊断更有用」的自然冲动往消息里塞脚本名/`__file__`，当场变红。tasks 1.1 只写原则未点破这个具体错误 |
| G4 | medium | high | **新诊断把外部进程输出打到 stderr，`secret_scan` 完全不覆盖这条路径**（其 scope 限定在 outside-voice 出境）。修复前是完全静默 ⇒ 这是**新增**的信息暴露面，design 零讨论零缓解。而威胁模型举的例子（企业 git 包装脚本）恰恰最可能把 token / 内网路径混进 stdout |
| G5 | low | high | conftest 性能实测：1756 测试 × `listdir` 共 0.068s，可忽略。`__pycache__` 不误报的**真实原因是 collection 早于 per-test 快照**，不是「这些工具不写 cwd」——design 归因不准；`pytest-xdist` 未安装 |
| G6 | low | high | **正面确认**：`_scan_pool` 子进程链不会双重失败；且扩大搜索确认其余 6 处全局 mock 均为安全写法，**「只有这一处假绿」的范围认定准确** |
| G7 | low | high | `_ACTIVE_RECORDER_TOKEN` 复位在 `args.func(args)` 之后 ⇒ 异常跳过复位。**既有问题**，非本变更引入，CLI 一次性进程下生产影响为零 |

## 声音 4：CLAUDE SUBAGENT（DX · 开发者体验独立）

| # | 严重度 | 置信 | 问题 |
|---|---|---|---|
| D1 | medium | high | **`premise-verification.md` 没有编号**：其标题无 `PV-` 前缀（对照 `doc-authoring.md:1` 自带 `# DOC-1：`），全仓 grep `PV-` 除本 change 外零命中 ⇒ Task 4.3「登记编号 + 路径」**按字面无法执行**；design 里用的「PV 规则 2/5」是本 change 现造的 |
| D2 | medium-high | high | **Windows CI 盲区**：`windows-recorder-smoke.yml` 的 `paths` 精确匹配本 change 改的三个目录，但只跑 `test_task2_windows_local_fs_smoke.py`——该文件直传 `tmp_path` 给 `recorder_lock`，**绕开 `repo_root`**；主矩阵 `mechanical-gates.yml` 只有 ubuntu/macos ⇒ 新校验从未在 Windows 真跑过。四件套全文 grep "Windows" 零命中 |
| D3 | low | 中 | 「截断至 80 字节」措辞与 Python 字符串语义不对齐（同 G1/X10，DX 侧独立命中） |
| D4 | — | high | **正面确认**：既有诊断格式 `ERROR: <问题含值>; cause: ...; fix: ...` 约 60 处一致，新消息格式吻合；「非 git 仓库不变」claim 属实；4 棵垃圾树与 CLAUDE.md 锚点字符串均现场核实；全仓仅 `test_init.py:593` 一处 `monkeypatch.chdir`，与新 fixture 无误报冲突 |

---

## 跨声音主题（2+ 独立声音命中 ⇒ 高置信信号）

| 主题 | 命中来源 | 说明 |
|---|---|---|
| **80 字节截断有坑** | codex X10 · Eng G1 · DX D3 | 三声独立命中；Eng 侧**实测复现异常**，从「措辞不准」升级为 critical |
| **`isabs+isdir` 判据不足 / 信任边界画错位置** | codex X2（critical）· codex X1（`--root` 面） | 同一根因的两个面：只盯 git stdout，漏了「根的身份」与「显式输入」 |
| **Task 2.2 变异验证不是真 metric** | codex X8 · （Eng F6 侧面印证测试面认定） | 一次性手工动作无永久产物 |
| **面没扫全** | CEO E2（ship_gate.py）· codex X7 / CEO E3（init.py 论证） | 「已扫过全仓同款反模式」目前是未坐实的隐含承诺 |
| **根 conftest 的边界与契约** | codex X9（契约强于实现）· CEO E5（缺防蔓延声明）· Eng G5（归因不准） | 三声从三个角度指向同一处 |

## autoplan 自动决策（G2：不弹窗，登记进 spec-review-report 决策区）

| # | 决策 | 分类 | 原则 | 理由 |
|---|---|---|---|---|
| A1 | Phase 2（Design）跳过 | Mechanical | — | UI scope 检测 0 命中，无 UI 面 |
| A2 | 三个 Claude subagent 并行而非串行 | Mechanical | P3 务实 | autoplan 自身要求 subagent 无前序上下文 ⇒ 并行不损独立性 |
| A3 | 前提门（premise gate）不弹窗 | — | sdflow G2 | 按 sdflow-spec-review 的 G2 适配，改为登记进设计门一次拍板 |
| A4 | codex 只调一次（CEO 位）而非每 phase 一次 | Taste | P3 务实 | 单次调用已覆盖战略 + 对抗架构 + 实现可行性三层，产出 11 条含 2 critical；每 phase 重调的边际收益低于其墙钟成本。**登记备查** |

## 反向核验（PV 规则 5）

- 正向：四个声音各自产出 ≥6 条 findings，均带 `file:line` 证据。
- 反向：**无任何一个声音回复「未发现问题」而不给检查范围**——四份都列出了「已检查、判定无问题的项」。
