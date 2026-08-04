# Open Issues 分批清理路线图

> 版本：v8（2026-08-04，B1-B10 完成，新排期 B11-B16 + WONTDO 9 条）
> 总量：95 条 open todo（0 条 open bug）

## 原则

- **按改动区域合批**——同一脚本/skill 的 issue 一个 change 做完，省多次评审
- **按影响排序**——安全/假绿/数据丢失 > 功能缺口/一致性 > 优化/文档
- **大块延后**——设计级重构（评审编排层重做、implement 大改）不塞进清理批次
- **已过时的先关**——与已删代码/已归档 change 相关的 WONTDO 掉

## 总览

| 批次 | 主题 | Issue 数 | 影响 | 难度 | 就绪度 |
|---|---|---|---|---|---|
| ~~B1~~ | ~~outside-voice 协议修复（环境变量必炸）~~ | ~~7~~ | -- | -- | ✅ 全部已关（5 DONE + 2 WONTDO） |
| ~~B2~~ | ~~机械门补缺（verify/gate/anchor 假绿面）~~ | ~~5~~ | -- | -- | ✅ 全部已关（5 DONE） |
| ~~B3~~ | ~~setup.sh 安全加固（所有权/覆盖/告警）~~ | ~~5~~ | -- | -- | ✅ 全部 DONE |
| ~~B4~~ | ~~sdflow-init 读写路径~~ | ~~4~~ | -- | -- | ✅ 全部 DONE |
| ~~B5~~ | ~~recorder repo_root 四合一~~ | ~~4~~ | -- | -- | ✅ 全部 WONTDO |
| ~~B6~~ | ~~outside-voice-job 零碎硬化~~ | ~~8~~ | -- | -- | ✅ 全部已关（3 已修 DONE + 5 直接修 DONE） |
| ~~B7~~ | ~~hack/ 测试守卫补全~~ | ~~7~~ | -- | -- | ✅ 全部已关（4 直接修 DONE + 3 WONTDO） |
| ~~B8~~ | ~~ship_gate 小修集~~ | ~~4~~ | -- | -- | ✅ 全部已关（1 直接修 DONE + 3 WONTDO） |
| ~~B9~~ | ~~sdflow-issues 脚本改造~~ | ~~4~~ | -- | -- | ✅ 全部 WONTDO（v2 架构已消除前提） |
| ~~B10~~ | ~~lens-metric 体系补全~~ | ~~4~~ | -- | -- | ✅ 全部 WONTDO |
| **BW** | **过时关闭（v8 新增 WONTDO）** | **9** | -- | -- | ✅ 全部 WONTDO |
| **B11** | **outside-voice 脚本修复** | **6** | 中-高 | 中 | 就绪 |
| **B12** | **workflow/tools 工具修复** | **5** | 中 | 中 | 就绪 |
| **B13** | **sdflow-maintain 扫描器硬化** | **4** | 中 | 小 | 就绪 |
| **B14** | **sdflow-implement 小修** | **3** | 中 | 小 | 就绪 |
| **B15** | **文档 + 术语 + spec 订正** | **6** | 低 | 小 | 就绪 |
| **B16** | **sdflow-init 小修集** | **5** | 低-中 | 小-中 | 就绪 |
| **延后池** | 评审编排大改 / implement 重构 / bundle 增强 / 度量 / Codex… | ~66 | 低-中 | 中-大 | 条件触发 |

---

## 已完成批次详情

### ~~B1~~ · outside-voice 协议修复 — ✅ 全部已关

核验后发现 T175/T255/T168 是同一根因的三次独立发现、T159 早已实质修好、T184(b) 被 ADR-9 机械锁禁止。
T150 经五问分诊 WONTDO：失效方向安全（fail-loud 不假绿）、真探针需 API 调用成本过高、review SKILL 已显式记录 preflight 是必要不充分条件。

| ID | 摘要 | 判定 |
|---|---|---|
| T175 | dispatch 模板改占位符 + claude-host exec 加内联环境变量前缀 | ✅ DONE |
| T255 | 与 T175 同一缺口 | ✅ DONE |
| T168 | 与 T175 同一根因（ADR-9 矛盾面） | ✅ DONE |
| T222 | 止损行改直接指名条款 | ✅ DONE |
| T159 | HELPER 变量——后续调用已全改字面路径 + MUST NOT 禁令 | ✅ DONE（核验时已修） |
| T184 | (a) 被 T175 修法覆盖；(b) 被 ADR-9 机械锁禁止 | ✅ WONTDO |
| T150 | preflight 只 command-v + timeout 检查，无真认证/模型探针 | ✅ WONTDO（fail-loud 兜底安全） |

---

### ~~B2~~ · 机械门补缺 — ✅ 全部已关

**痛点**：verify/gate/anchor 路径有假绿面——该拦的没拦住。

| ID | 摘要 | 判定 |
|---|---|---|
| T262 | verify 子代理漏写 frontmatter 锚，无即时机械门 | ✅ DONE（sdflow-done §1.1 机械校验步骤） |
| T205 | code 域排除整个 openspec/（改 workflow/tools/ 不判 stale） | ✅ DONE（ship_gate 额外比较 workflow/tools/） |
| T86 | anchor_lint 未闭合 fence 不 fail-closed | ✅ DONE（一行 closed flag 检查） |
| T228 | secret_scan 含 NUL 字节漏判 | ✅ DONE（grep -a 强制文本模式） |
| T259 | review-loop-breaker ①档逻辑冲突（未修复也能关 Critical） | ✅ DONE（①档措辞修正：区分已解决/仍成立两条出口） |

---

### ~~B3~~ · setup.sh 安全加固 — ✅ 全部 DONE

| ID | 摘要 | 判定 |
|---|---|---|
| T24 | install_into 对既有软链零所有权校验（同名异物被 ln -snf 无声覆盖） | ✅ DONE（readlink 判据匹配自属 checkout） |
| T14 | Windows 指针分支补所有权检查 | ✅ DONE（读现有 workflow-path 内容判自属） |
| T18 | skills 软链切换无指向变更提示 | ✅ DONE（接管提示 旧→新） |
| T16 | install_sdflow 告警独立打印分支 | ✅ DONE（去掉冗余英文尾缀） |
| T263 | Python3 probe 统一（command -v 不一致） | ✅ DONE（统一用 $_py） |

---

### ~~B4~~ · sdflow-init 读写路径 — ✅ 全部 DONE

change `sdflow-init-readwrite-paths` 一次完成四条，归档于 2026-08-04。

| ID | 摘要 | 判定 |
|---|---|---|
| T63 | inject 多块收敛须 fence-aware + start/end 配对校验 | ✅ DONE |
| T64 | settings.json 原子写改唯一名关闭无锁降级 | ✅ DONE |
| T149 | lint_config 对重复键无告警 | ✅ DONE |
| T6 | 两个全局 hook 仅装 Claude 侧 | ✅ DONE |

---

### ~~B5~~ · recorder repo_root 四合一 — ✅ 全部 WONTDO

v2 迁移后 recorder 三份同步面已消失（只剩 `issues_v2.py` 一份），四条全属低概率边角（DoS/竞态/symlink 回落），
已有 timeout=30 + realpath 缓解，修法代价（Popen+定量读+进程组回收）与可利用性不成比例。

| ID | 摘要 | 判定 |
|---|---|---|
| T181 | 回落分支 lexical abspath != git 实际探测目录 | ✅ WONTDO（recorder_lock realpath 已兜） |
| T182 | stdout 无界读入（DoS 面） | ✅ WONTDO（timeout=30 限时窗） |
| T183 | TOCTOU 窗口（isdir 与 subprocess 之间被删） | ✅ WONTDO（走回落非假绿） |
| T185 | stderr 同样无界读入 | ✅ WONTDO（与 T182 同族） |

---

### ~~B6~~ · outside-voice-job 零碎硬化 — ✅ 全部已关

3 条在后续 change 中已修（T212/T219/T216），5 条直接修复（T213/T217/T218/T215/T220），333 passed。

| ID | 摘要 | 判定 |
|---|---|---|
| T212 | nonce 核验补 cwd==repo_root 同一性约束 | ✅ DONE（已有四项 identity 校验） |
| T213 | CLI_PROBE_TIMEOUT_SECONDS 改可调 | ✅ DONE（改环境变量 SDFLOW_CLI_PROBE_TIMEOUT） |
| T217 | except Exception 收窄为 (ValueError, TypeError) | ✅ DONE |
| T218 | rc_bad(CORRUPT) 路径重复非逐字节一致 | ✅ DONE（冻结条件扩展到 rc 文件存在即冻结） |
| T219 | cmd_worker 不校验 effort | ✅ DONE（已有 EFFORT_VALUES 校验） |
| T215 | 删除近似恒真旧断言 | ✅ DONE（删除） |
| T216 | collect 幂等双路径缺单路径回归锚 | ✅ DONE（已有完整单路径测试） |
| T220 | docstring 两处同族漏网 | ✅ DONE（订正判据⑤ + 组信号限定） |

---

### ~~B7~~ · hack/ 测试守卫补全 — ✅ 全部已关

4 条直接修复（T224/T260/T243/T166），3 条 WONTDO（T223 非缺陷备查、T225/T226 绑定外部条件）。2484 passed。

| ID | 摘要 | 判定 |
|---|---|---|
| T223 | async parity end marker 良性新增会假红 | ✅ WONTDO（fail-closed 设计，非缺陷） |
| T224 | efficacy 枚举漏 2 条 isinstance 早退分支 | ✅ DONE（补 2 条用例） |
| T225 | 补跑真实 Codex 宿主 voice efficacy 三门 | ✅ WONTDO（外部条件未就绪） |
| T226 | check 补 --run-dir 逐站点交叉核验 | ✅ WONTDO（与 T225 绑定） |
| T260 | Codex 子代理授权段三处无机械守卫 | ✅ DONE（补 parity 断言） |
| T243 | reference 路由测试放宽非空链接标签格式 | ✅ DONE（regex 放宽） |
| T166 | async end marker 边界未与 start 对称硬化 | ✅ DONE（精确匹配） |

---

### ~~B8~~ · ship_gate 小修集 — ✅ 全部已关

| ID | 摘要 | 判定 |
|---|---|---|
| T189 | checkbox normalize 已第 4 轮补语法分支，反转为白名单 | ✅ WONTDO（趋势信号非缺陷，白名单重构代价不成比例） |
| T197 | annotated tag OID 经 ^{commit} peel 被接受 | ✅ WONTDO（peel 是 git 标准做法，实现正确） |
| T206 | archived_verify_state 的 strip 口径不一致 | ✅ WONTDO（strip 只去尾部换行，无实际影响） |
| T195 | conftest helper 三处重复 subprocess.run | ✅ DONE（收口到 `_git`） |

---

### ~~B9~~ · sdflow-issues 脚本改造 — ✅ 全部 WONTDO

issues-v2-single-file-model change 已删除 `sdflow_issues_core`、v1 三脚本、等价测试，
四条的标的代码全部消失。T209（move 命令）经三仓实查零误判，不为从未发生的场景建命令。

---

### ~~B10~~ · lens-metric 体系补全 — ✅ 全部 WONTDO

四条均为度量体系设计级增强（非正确性），当前精度够用，触发条件=retro 跑出度量盲区时再议。

| ID | 摘要 | 判定 |
|---|---|---|
| T192 | emitter 输入 JSON 未落盘（SR-M 门后重算不可执行） | ✅ WONTDO |
| T254 | 行键无法表达 broad 层内跨模型双声 | ✅ WONTDO |
| T172 | 采纳/defer 二分无法表达边界变更 | ✅ WONTDO |
| T55 | 聚合器 glob 空 vs archive 不存在无法区分 | ✅ WONTDO |

---

### BW · 过时关闭（v8 新增 WONTDO） — ✅ 全部 WONTDO

v8 分诊：标的代码已删（v2 合并消除前提）、源 change 已归档（四件套不再修改）、与更完整 issue 重叠。

| ID | 摘要 | 判定 |
|---|---|---|
| T72 | batch lint 整行缺字段不校验 | ✅ WONTDO（issues.py 已被 v2 取代，旧 batch 格式已不存在） |
| T151 | recorder three-way parity guard 扩展 | ✅ WONTDO（sdflow-buglist/ 已删，v2 合并为 sdflow-issues） |
| T152 | 规范 mlh-p6 impl-reports 的 diff --check | ✅ WONTDO（源 change 已归档，impl-reports 是历史文档） |
| T157 | async-outside-voice proposal 仍写旧形态 | ✅ WONTDO（源 change 已完整归档） |
| T160 | 3600 上界依据应回写 design ADR-3 | ✅ WONTDO（源 change 已归档） |
| T167 | 四件套仍描述旧协议需 delta 同步 | ✅ WONTDO（归档已完成，delta sync 时机已过） |
| T177 | buglist add 必填校验不含根因 | ✅ WONTDO（sdflow-buglist 已删，v2 统一模型设计不同） |
| T180 | recorder 缺追加证据命令 | ✅ WONTDO（sdflow-todolist/buglist 已删，v2 set-status 有 --evidence） |
| T214 | OVBG-01 措辞对齐 5s deadline | ✅ WONTDO（与 T229 重叠，T229 更完整覆盖 OVBG-01+05） |

---

## 新排期批次详情

### B11 · outside-voice 脚本修复

**痛点**：voice 脚本有两个运行时安全面（timeout 禁用 + 进程杀不死）+ 四处正确性/测试缺口。
改 `sdflow-init/assets/hack/outside-voice.sh` + `outside-voice-job.py` + tests。

| ID | 摘要 | 危险度 |
|---|---|---|
| T176 | `--timeout 0` 不拒绝 → GNU timeout 语义禁用超时 = 进程挂死 | 高 |
| T227 | worker 无信号转发 + cleanup 不终止 runner_pid：取消杀不死计费进程 | 高 |
| T174 | fake-timeout 看门狗 `$(( sec * 10 ))` 遇非整数 sec 算术错 | 中 |
| T173 | ov_cleanup kill -KILL 兜底行无测试覆盖 | 中 |
| T230 | 出境 stdout 落盘无大小上限 | 低-中 |
| T178 | M3 磁盘满诊断锁 CI 无人看守 | 低-中 |

---

### B12 · workflow/tools 工具修复

改 `anchor_lint.py` + `trivial_shape.py` + `outside_voice_guard.py` + 仓级测试配置。

| ID | 摘要 |
|---|---|
| T139 | outside_voice_guard 双锚不校验一致性 |
| T140 | anchor_lint declared= 必填无向后兼容（旧格式锚 exit1） |
| T68 | anchor_lint load_enums fence 提前闭合（fail-closed 安全侧） |
| T56 | trivial_shape tests/ 排除不覆盖 tests/plugins/* |
| T188 | 跨 skill 同 basename 测试文件中断仓根全局收集 |

---

### B13 · sdflow-maintain 扫描器硬化

改 `maintain_scan.py` + `resolve-workflow.sh` + tests。

| ID | 摘要 |
|---|---|
| T93 | RULE_MARKERS bash 副本跨语言漂移无机验 |
| T94 | 告警文案跨脚本复述漂移 |
| T95 | test 缺 importorskip 降级 |
| T96 | 链接正则与目录名字符集不对称 → 非规范命名静默漏报 |

---

### B14 · sdflow-implement 小修

改 `sdflow-implement/SKILL.md` + `impl_route.py` + tests。

| ID | 摘要 |
|---|---|
| T261 | 两处引用已归档 change 路径死链（补 `archive/2026-07-10-` 前缀） |
| T250 | golden fixture 补收尾票形状覆盖 |
| T128 | PIPELINE_RECEIPT marker 无法区分显式声明与隐式缺省 |

---

### B15 · 文档 + 术语 + spec 订正

改 docs/ + CLAUDE.md + CONTEXT.md + openspec/specs/。

| ID | 摘要 |
|---|---|
| T199 | CLAUDE.md 写的 `pytest` 命令本机不可用 |
| T207 | docs/ 旧 skill 名（sdflow-buglist/todolist）刷新到 sdflow-issues |
| T142 | workflow-map.md 广度刷新（补 5 脚本 + hr-tg 三字段） |
| T229 | OVBG-01/05 spec 措辞已被实现证伪，需订正 |
| T252 | adr/0031 T10 单一源化补追踪条目 |
| T253 | 「第三类场景」命名脱钩 T10 |

---

### B16 · sdflow-init 小修集

改 `init.py` + `resolve-workflow.sh` + `assets/workflow/` 规则文件 + tests。

| ID | 摘要 |
|---|---|
| T12 | canonical 陈旧可观测（commit hash + 距上次 pull 天数） |
| T15 | update --dev 误报陈旧遮蔽告警 |
| T69 | copy_bundle 缺消费仓 update 端到端交叉不变量测试 |
| T130 | ff-generation-constraints.md「四件套」→「三件套」术语 |
| T131 | workflow.md wayfinder 硬编码 Claude 单宿主路径 |

---

## 建议执行顺序

```
B1-B10 ─── ✅ 全部已关
  │
BW (过时关闭) ─── ✅ 全部 WONTDO
  │
B11 (voice 脚本) ── 安全面：timeout 禁用 + 进程杀不死
  │
B12 (workflow/tools) ── 假阴 + 兼容性
  │
B13 (maintain 扫描器) ── 跨语言漂移
  │
B14 (implement 小修) ── 死链 + fixture
  │
B16 (sdflow-init) ── 可观测 + 术语
  │
B15 (文档清理) ── 文案/命名
```

---

### 延后池（~61 条）

不排期，条件触发时再捞：

| 类别 | 条数 | 代表 ID | 触发条件 |
|---|---|---|---|
| 评审编排大改（effort/去偏/裁决/跨模型） | 13 | T7, T41, T103, T106-T113, T121 | 评审成本再成瓶颈时 |
| 评审 SKILL 协议 DRY | 4 | T158, T161, T163, T196 | 协议再漂移一轮时 |
| bundle 规则/模版增强 | 10 | T9, T42, T57, T105, T109-T110, T114-T116, T119, T124 | 规则维护循环触发 |
| sdflow-implement 重构 | 7 | T191, T244-T246, T249, T251, T258 | tickets 管线跑够样本 |
| sdflow-done merge 精确化 | 2 | T51, T52 | merge 误停频繁时 |
| spec/架构 skill | 3 | T143, T144, T264 | 各自条件触发 |
| 度量体系 | 4 | T29, T54, T104, T108 | retro 再跑一轮看缺口 |
| Codex/跨模型 | 3 | T111, T162, T221 | codex deferred_executor 稳定 |
| outside-voice 设计级 | 3 | T31, T165, T256 | voice 成本/功能再触底 |
| embedded-test-sop 脚本化 | 2 | T83, T84 | 真实 embedded 消费仓出现 |
| roadmap/流程增强 | 5 | T122, T129, T141, T145, T169 | 各自条件触发 |
| 报告截断/产物归档 | 1 | T171 | 截断频繁影响审计时 |
| 其他零散 | 4 | T23, T62, T123, T134, T248 | 各自条件触发 |
