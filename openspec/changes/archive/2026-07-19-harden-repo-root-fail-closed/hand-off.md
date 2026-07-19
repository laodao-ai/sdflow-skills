# hand-off — harden-repo-root-fail-closed

> 异步人类再入口 + 下个 change 种子。verify 判 **PASS** 之后、archive 之前产出。
> 「完成」项**不直接搬运 verify 的 ✅**——每条已复核锚点存在性。

---

## ✅ 完成了什么

**一句话**：三份 recorder 的 `repo_root()` 从「零校验采信 `git rev-parse` 的 stdout」变成**九步身份校验的 fail-closed 解析器**，
并连带堵掉了它下游「任意字符串被静默具现成目录树」的整条链。

| 交付 | 锚点（已复核存在） |
|---|---|
| **九步身份判据**（起点 → 环境净化 → **最近 marker 上溯** → git 失败裁决 → 调 git → 形状 → 祖先 → marker → **最近根一致**） | 三份 `scripts/*.py` 的 `repo_root`；`test_repo_root_identity_{issues,buglist,todolist}.py` 各 41+ 例 |
| **主防线可证伪** | 变异确认：祖先校验改 `if False` → `test_core_worktree_redirect_is_rejected` 等 2 例变红（verify 独立重做过） |
| **单点解析** | `ast.walk` 实测 Call 节点 **19 → 3**（三份 `main()` 各一） |
| **假绿消除** | 对照实验：同一变异下旧形态 `8 passed`（瞎的）、新形态 `4 failed`；`test_task4_rename_snapshot.py` |
| **16 站点 argv 分派面级收敛 + 双门 AST 机械守** | `sdflow-issues/tests/conftest.py` + `test_patch_discipline.py`（11 例，含三种 `MonkeyPatch` 别名自检语料） |
| **cwd 泄漏回归断言（全仓）** | 仓根 `conftest.py` + `pytest.ini`（**两文件缺一即失效**）；11 个套件各自干净临时目录跑，残留全 `[]` |
| **垃圾树清除且不再生** | `find . -maxdepth 1 -name '{*'` 无输出；再生链已由加固切断（Task 1 定位、Task 2 切断） |
| **全套件** | `1910 passed / 9 skipped / 3 xfailed / **0 failed**` |

**7 条 Success Metrics 全达成**（广审独立验过 5 条，verify 独立验过 3 条）。

---

## ⏳ 未完成 / 延后

### 批次 `harden-repo-root-fail-closed`（10 项，见 `openspec/issues/batches.md` + `INDEX.md`）

| ID | 一句话 | 为什么没在本 change 做 |
|---|---|---|
| **B15** | **P1**·跨进程根分裂时 `recorder_lock` 静默写错根 —— **spec R2 的一条 MUST 当前不成立** | 修法（下传 `SDFLOW_RECORDER_LOCK_ROOT`）**触 lock spec** ⇒ 设计门议题。已落 `xfail(strict=True)` 机械锚，**堵上即 XPASS 判红** |
| **B18** | **P1**·`maintain_scan.py::find_repo_root` 是同面**第四份**实现，三条判据全缺 | 面治扫描口径盲区（见下方教训）；修法 = 第四份内联 + 四向镜像，或等 T170 抽 canonical 源 |
| **B17** | P2·非仓库 + **不可写**目录仍裸 Traceback | 缺陷在下游 `makedirs`，非 `repo_root`。**诱人的修法是错的**——加可写性闸门会打断 `next-id`/`scan` 在只读目录的合法使用。**`repo_root` 负责解析，不负责授权** |
| **B16** | `test_exec_claude_reverse_path_three_flags_golden` 时红时绿 | **触发条件未定位**（原记「全量跑必红」已被多轮实测证伪）。⚠️ 排查时须显式排除仓根 conftest 的三钩子（本 change 新增的全局 per-test 副作用面） |
| **T181** | 回落用词法 `abspath`，symlink+`..` 下 ≠ git 实际探测目录 | spec 明文 MUST 返回 `abspath`。⚠️ **defer 理由是流程约束（改 spec 令设计门失鲜），不是安全论证** —— 设计门须显式确认。缓解：`recorder_lock` 入口即 `realpath`，锁侧已兜住 |
| **T185** | `capture_output` 对 **stderr** 同样无界（design Non-Goals 只列了 stdout） | 与 tasks 4.8 同族，合并处置 |
| **T182/T183** | tasks 4.8 / CF-7 登记的 DoS 面与 TOCTOU 窗口 | 边角，spec 未要求处置 |
| **T180** | recorder 缺「给已存在项追加/改字段」的命令 | 结构性，与 T170 同批 |
| **T184** | outside-voice 的 `$SDFLOW_VOICE_RUNNER` 协议坑（**本 session 踩中两次**） | ⚠️ **挂错 change**——它是跑评审时踩到的 workflow 缺陷、与本 change 功能无关，**会污染本批次的 sweep 圈选**。建议改挂 `main`（受 T180 阻塞，需手工编辑） |

### 被延后的 ≥2 方案决策

- **B15 的修法**：Spec 轴给了完整方案（新增 `SDFLOW_RECORDER_LOCK_ROOT`，`recorder_child_env` 下传父进程 realpath，`recorder_lock` 判「变量存在且 ≠ 本进程解析根 ⇒ 响亮失败」；变量缺失仍走既有回落 ⇒ 契约测试原样绿）。**代价**：三份同步 + AST 镜像 + 触 lock spec。**当时没自动选，因为它越过了已拍板的设计门**。
- **T181 的修法**：回落改 `realpath` —— 同样要改 spec。

### verify 的 Minor 缺口

- **4.6 Windows**：用例已写并挂进泳道，**但从未在真 Windows 跑过**（本机 macOS 全 skip）。达成的是「覆盖已就位」，不是「已验证」。
- **3.2**：实为 **11** 个套件（票面「12」沿用 ADR-3 的失准基线）。
- **4.7**：shell 脚本的排除论证仍在 impl-report、未回写 Non-Goals（四件套冻结所致）。
- **CF-8**：`timeout=30` 的**数值本身**无自动化锚（真等满 30s 不可接受）。**不宣称「超时面已全覆盖」。**

---

## ▶ 下一阶段建议

**Roadmap 回填**：— 无关联（`roadmap_writeback_draft.py` exit=3，本 change 非 roadmap 驱动）。

### 🔴 优先级 1：spec 回写（**归档时就要做，不能留到下个 change**）

`impl-reports/carry-forward.md` 的 **CF-9 共 11 项 + verify 新增 2 项**。⚠️ **两类，MUST NOT 混为一谈**：

- **a–g：实现对、措辞旧** —— 收窄口径没落 spec 正文、`autouse fixture` vs hook wrapper、ADR-3 漏了 `confcutdir` 前置条件、「12 个 skill」实为 11 等。
- **h–k + verify 新增 2 条：原判据本身不足、被代码审证伪后收紧** —— 回落判据、步骤⑨最近根一致、`.git/` 内 fail-closed、六步→九步、捕 `OSError` 而非 `FileNotFoundError`、`os.fsdecode` 而非 `text=True`。
  **这是对已批准设计的实质修订，MUST NOT 在设计门被折叠进「措辞订正」桶。**

🔴 **归档硬条件（verify 提出）**：R2 的「子进程解析出不同根时响亮失败」这条 Scenario **MUST NOT 原样落进 `openspec/specs/`**，须就地标注 B15 或移出 ADDED——**否则主 spec 会宣称一个代码里不成立的保证**。

### 优先级 2：开一个 `harden-recorder-lock-root-binding` change

吃掉 **B15**（含 lock spec 修订）+ 顺带 **B17**、**T181**——三者同属「解析与授权的边界」这一片面，一起做比分开做省一整轮 workflow 循环。

### 优先级 3：**T170**（三份物理复制 → canonical 源）

本 change 已按「抽取友好」硬约束写（`repo_root` 内零脚本专属分支、raise 消息通用文案），落地时是**纯搬运**。
⚠️ 现在多了一个理由：**B18 的 `maintain_scan.py` 是同面第四份** —— T170 该把它一起收编，否则永远是三向镜像 + 一个野生实现。

---

## 📌 三条值得留档的教训

1. **面治扫描的口径要按「所解决的问题」定，不能按「实现手段」定。**
   Task 6 的扫描关键词是 `show-toplevel`，于是漏了 `maintain_scan.py`（它靠向上找 `.git` 实现同一件事）。**漏的不是一处，是一整类。**

2. **守护必须能回答「我现在活着吗」。**（对抗镜 C 原话）
   本 change 建的 4 道守护里有 3 道被实测出「退化了但全绿」——门 A 对 `MonkeyPatch` 别名全盲、rootdir 被抢时仓根守护静默出局、xfail 前提烂掉也计入 xfail。**失效无声的守护，等于没有。**

3. **冷层是承重墙，不是边际残差。**
   主防线的 Critical（`core.worktree` 指向外层祖先仓）躲过了 3 轮设计返修 + 6 票双轴审 + 3 轮接缝复审，被两个**冷跨模型 voice** 各自独立抓到、并各自独立提出同一修法。
   原因：内部各轮的判据基准是**这个 change 自己写下的那份设计**——大家都在问「祖先校验做对了吗」，**没人退一步问「祖先校验本身够不够」**。
