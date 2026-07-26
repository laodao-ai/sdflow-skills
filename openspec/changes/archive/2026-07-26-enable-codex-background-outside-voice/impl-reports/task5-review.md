# Task 5 双轴审存档 — 两份评审 SKILL 的宿主自适应调度切换与安装快照

**票**：Task 5（R-ID: HAE-08, HAE-09, OVBG-01）
**轮次**：轮 1（`6084403`）**双 FAIL** → fix1（`fa378fb`）→ 轮 2 双 PASS

## 领域清单覆盖声明（Standards 轴，两轮均原样重述）

本 change 的 `proposal.md` 明确声明「不命中 backend、frontend、embedded 技术栈领域清单」，而
`code-checklists/domains/` 下只有 `backend*.md` / `embedded*.md` —— 故**领域清单未覆盖**，
Standards 轴以 `code-review-base.md` + 仓内 `CLAUDE.md` 基准 + Fowler code smell 为标准源。
**这是诚实降级，不是「全覆盖通过」。**

## 🔴 本票的主线发现：**宣称有锚，实则假绿**

本票判据重心与前四票不同——前四票是「代码行为对不对」，本票是「**SKILL 里写给模型看的调度指令，
与 helper 的实际契约是否一致**」。SKILL 是 prose 指令、**没有类型检查**，写错一个 `reason_code` 名、
少一个分支、把 `unknown_cost` 漏掉，机械门都不会红。

两轴各自用反向变异实测，证明 impl-report 里列为「机械锚」的多条**对其声称守护的不变量完全不敏感**：

| 宣称守护的不变量 | 实际锚 | 变异结果 |
|---|---|---|
| 外层 wait 回收后不重派 | `"MUST NOT 重" in seg`（**3 字前缀**，段内命中 2 次） | 删掉 `MUST NOT 重新 dispatch` 整句 → **35 passed** |
| manifest 记 4 列身份 | 只查 printf 行含 `attempt_nonce` 子串 | 格式串改回 3 个 `%s`（实参仍 4 个）→ **35 passed**；而 **POSIX printf 会复用格式串**，实际每次多落一行 `<nonce>\t\t` |
| dispatch 命令形态（**本票声明的最高风险面**） | 查四个词是否出现在段内**任意处**（散文里本就有） | 子命令 `dispatch`→`submit` + 丢 `--repo-root` + `--effort high`→`medium` → **全绿** |
| `unknown_cost` 禁自动 fallback（交接 3） | 四个子串被 ④ / ⑦ 别处满足 | 整条删掉 → **全绿** |
| 兼容分支已删除 | 只拦矩阵行 | 改写成**散文 MAY** 兼容分支 → **全绿** |

**若只看测试是否绿，这一票会当场通过。**

## 另一条 Critical（Spec 轴 F1）：锚形不合法 ⇒ 报告自检必红或必谎

`unknown_cost=true` 分支落 `exec-error`，但全段只在 exit 0 / exit 3 指定过 `runner=`。
实跑 `classify_combo('codex','none','exec-error',0)` → **illegal**（no-exec 仅许
`secret-hit|fallback-unavailable`）；唯一能过的 `runner==host` 等于**谎称同族 fallback 跑过**。
而 `declared-sites` 强制该站点必须有锚 ⇒ **报告自检必红，或者必须撒谎**。

## 两轴的独立裁断（编排层均采纳）

- **Concern 2「散文形态照不到」= 做窄了，非基准 1 合法残余**。基准 1 原文是「只有**机械真够不着的
  残余**（**无确定性信号者**）才退到语义规则」——而 ② 的字面串是**段内唯一**，一条 assert 即可守，
  与既有 8 条正向 golden **同级成本**。且「散文不构成可执行指令」这个理由被 SKILL 自身结构证伪：
  **②④⑤⑥⑦⑨ 全是散文 MUST，矩阵只是其中一处。** ⇒ 已补该字面串 golden。
- **降级项 ③（manifest 写失败只告警不中止安装）= 自洽**。OVBG-01「不一致时 fail-closed 为
  `preflight-error`」——**fail-closed 的对象是 background transport，不是 `setup.sh`**；
  再经 HAE-08「Codex-host background-exec 不可用时 SHALL 立即同族 fallback」，**正是 spec 规定路径**。
  中止 setup 反而把可选通道升格成 skills 安装前提。⇒ **不改**。

## 编排层裁决：F1 复用 `fallback-unavailable`

fix 上抛了语义差：spec 的 Scenario 描述「同族 fallback **起不来**」，而新用法是「同族 fallback
**被成本闸门禁止**」。**裁定复用是正解**——验收标准第 3 条字面要求「anchor 合法组合矩阵**保持不变**」，
新增枚举值要跨 `openspec/specs/` + `anchor_lint` + 全笛卡尔 golden，属矩阵变更、**超出本票范围**。
语义差记 **T221** 交冷层复看。

Spec 轴按要求核了两点：① `classify_combo` 实跑确认锚形**合法**（`no-exec`）；
② **仅部分可区分** —— 两种情形锚行**逐字节相同**，区分只在正文（成本闸门路径 MUST 写
`orphan_warning`/`detail`，另一路径无对应 MUST）⇒ 判别靠「orphan warning 缺席」这一**由缺席推断**
的弱信号。已并入 T221。

## 轮 2 复审（双 PASS）

**Spec 轴**跑了 11 条自创变异（**非复用 fix 的矩阵**）：`R2-MUT-B/C/E/F/G/H/I/J/K/L/M` 逐条红。
F3 的核验方式尤其值得记——它不只确认「条件加了 `∧ unknown_cost=false`」，而是追问
**RESERVED 那条路径现在走哪儿**：确认终点是确定的落锚动作（`runner="none" findings="0"
reason_code="fallback-unavailable"` + orphan warning + 提示 `cleanup --cancel`），
**既不卡死也不静默放行**；并验了「把 RESERVED 移出 `PENDING_STATES` 会不会红」——
**锚绑的是 helper 的实际状态集，不是措辞**。

**Standards 轴**抽验 7 条 + 自创 2 条，全红；并做了两件关键核查：
① 独立复核 `classify_combo` 两种组合；② **交叉断言非空自证** —— 验证 F4 那条
「子命令名 ⊆ helper `build_parser().choices`」的断言集合真的非空（实测必填集
`{--context-file,--repo-root,--run-dir,--site}`、子命令 10 个），**否则又是一个恒真锚**。
I3 确认是**真机械导入**（`importlib` 载 JOB 取 `MIN_CLAUDE_VERSION`，段内**无任何 `2.1.169` 字面**），
helper 提版到 `(2,1,170)` → 红。

### 新回归扫描

- **`(3, 6)` 第三处 bind：无。** fix 首轮全量跑红过一次，根因是该常量有**第二个** bind 在
  `test_setup_failsafe.py`、首轮 grep 漏了（**复现了「改共享字符串时 grep 范围不足、残留能活两轮」
  的既有教训**）。Standards 轴全仓 grep 确认仅存 `init.py` 一处「3.6+」且语义正确（那是 init.py
  **自身**的下限，同句已注明 setup.sh 按 3.7 卡）；归档目录保持原样（正确）。
- **`setup.sh` 既有不变量未再被触动**：diff 仅落在 manifest 归因块与版本闸门；
  `install_into` / `cleanup_orphans` / `is_our_marker_copy` **零改动**（所有权守卫、孤儿清理完好）。

实跑：`pytest sdflow-init/tests/ hack/tests/ -q` → **688~689 passed, 3~4 skipped**（环境敏感用例浮动）；
`check_async_branch_parity.py` → `✅ 2 处逐字节一致`；`sync_principles.py --check` → `✅ 18 个投放面一致`；
`bash -n setup.sh` → OK。全量 **2496 passed, 11 skipped, 3 xfailed**。

## 五条跨票交接**全部兑现**（前四票累积）

| # | 交接 | 兑现锚 |
|---|---|---|
| 1 | `setup.sh` 写 `capability-manifest.json`（Task 1 起交接、拖到本票） | 调 helper 的 `install-manifest` 子命令；`grep -in "sha\|shasum\|md5\|digest\|generation" setup.sh` **零命中** ⇒ shell 侧确无第二份 hash 口径。变异抽掉调用 → **5 failed** |
| 2 | SKILL 侧 config clamp 保留 | 段内保留「回落默认 900 / MUST NOT fail-closed 罢工」+ 新增下推禁令；变异删 clamp → 红 |
| 3 | SKILL 分支显式处理 `unknown_cost`（Task 3 C1） | **轮 1 锚是假绿**（整行删掉全绿），fix 后 MUT-E/F/I 三条全红 |
| 4 | T220 两处 docstring 知情未改 | 该测试文件 diff **零删除行** |
| 5 | `openspec/specs/` 主 spec 不动（归 archive） | `git diff --name-only -- openspec/specs/` **空** |

## Minor defer

**T221**（`fallback-unavailable` 语义复用 + 锚层不可区分）· **T222**（止损行「下一条」指代不准；
Standards 建议当场 fold，编排层维持 defer —— 冷层 code-review 紧接就跑且有自动修能力，
同类文档措辞项批量处理更划算）· **T223**（`_the_line_with` 的「恰好 1 行」是双向判据，
段内良性新增会假红；方向 fail-closed、报错点名 key，登记为已知刚性）。

## ⚠️ 仍未验（合并后 MUST 做）

**真实 HOME 跑 `bash setup.sh`** —— 破坏性动作（会把全局链指向 dev checkout），本轮按裁定
MUST NOT 跑。**合并后需在运行 checkout 重跑 setup.sh**，否则新 SKILL 调旧脚本。
