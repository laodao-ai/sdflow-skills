# Open Issues 分批清理路线图

> 版本：v4（2026-08-04，B6 完成）
> 总量：119 条 open todo（0 条 open bug）

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
| **B7** | hack/ 测试守卫补全 | 7 | 中 | 小 | 可立即开 |
| **B8** | ship_gate 小修集 | 4 | 中 | 中 | 可立即开 |
| ~~B9~~ | ~~sdflow-issues 脚本改造~~ | ~~4~~ | -- | -- | ✅ 全部 WONTDO（v2 架构已消除前提） |
| **B10** | lens-metric 体系补全 | 4 | 中 | 中 | 可立即开 |
| **延后池** | 评审编排大改 / implement 重构 / bundle 增强 / 度量 / 文档… | ~95 | 低-中 | 中-大 | 条件触发 |

---

## 批次详情

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
| T205 | code 域排除整个 openspec/（改 workflow/tools/*.py 不判 stale） | ✅ DONE（ship_gate 额外比较 workflow/tools/） |
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

### B7 · hack/ 测试守卫补全（7 条）

| ID | 摘要 |
|---|---|
| T223 | async parity end marker 良性新增会假红 |
| T224 | efficacy 枚举漏 2 条 isinstance 早退分支 |
| T225 | 补跑真实 Codex 宿主 voice efficacy 三门 |
| T226 | check 补 --run-dir 逐站点交叉核验 |
| T260 | Codex 子代理授权段三处无机械守卫 |
| T243 | reference 路由测试放宽非空链接标签格式 |
| T166 | async end marker 边界未与 start 对称硬化 |

---

### B8 · ship_gate 小修集（4 条）

| ID | 摘要 |
|---|---|
| T189 | checkbox normalize 已第 4 轮补语法分支，反转为白名单 |
| T197 | annotated tag OID 经 ^{commit} peel 被接受 |
| T206 | archived_verify_state 的 strip 口径不一致 |
| T195 | conftest helper 三处重复 subprocess.run |

---

### ~~B9~~ · sdflow-issues 脚本改造 — ✅ 全部 WONTDO

issues-v2-single-file-model change 已删除 `sdflow_issues_core`、v1 三脚本、等价测试，
四条的标的代码全部消失。T209（move 命令）经三仓实查零误判，不为从未发生的场景建命令。

---

### B10 · lens-metric 体系补全（4 条）

| ID | 摘要 |
|---|---|
| T192 | emitter 输入 JSON 未落盘（SR-M 门后重算不可执行） |
| T254 | 行键无法表达 broad 层内跨模型双声 |
| T172 | 采纳/defer 二分无法表达边界变更 |
| T55 | 聚合器 glob 空 vs archive 不存在无法区分 |

---

### 延后池（~104 条）

不排期，条件触发时再捞：

| 类别 | 典型 issue | 触发条件 |
|---|---|---|
| 评审编排层大改（effort scaling / 去偏 / 跨模型终局） | T103, T107, T112, T113, T106 | 评审成本再成为瓶颈时 |
| sdflow-implement 重构（票数 / 选档 / review-package） | T245, T246, T249, T251, T258 | tickets 管线再跑几轮积累样本 |
| bundle 规则/模版增强 | T110, T114, T115, T124, T119 | 规则维护循环触发 |
| 度量体系 | T29, T54, T104, T108 | retro 再跑一轮看缺口 |
| sdflow-roadmap 存量迁移 | T129 | 首个新流程 roadmap SHIPPED |
| embedded-test-sop 脚本化 | T83, T84 | 真实 embedded 消费仓出现 |
| Codex voice 架构性阻塞 | T162 | codex deferred_executor 稳定 |
| 文档/注释/术语对齐 | T199, T142, T134, T253, T252… | 顺手改或定期扫 |
| 四件套考古层清理 | T157, T167, T169, T160 | 对应 change 做 done 时顺带 |
| sdflow-done merge 检查精确化 | T51, T52 | merge 前误停频繁时 |
| 评审 SKILL 协议 DRY | T163, T161, T196, T158 | 协议再漂移一轮时 |
| 测试/CI | T188, T155, T203, T151, T152, T56 | 偶发失败再现时 |

---

## 建议执行顺序

```
B1 (voice 协议) ─── ✅ 全部已关
     │
B2 (假绿门)    ─── ✅ 全部已关
     │
B3 (setup 安全) ─── ✅ 全部已关
     │
B4 (init)      ─── ✅ 全部已关
     │
B5 (repo_root) ─── ✅ 全部已关
     │
B6 (voice-job) ─── ✅ 全部已关
     │
  ┌─ B7 (hack测试) ──┬── B8 (ship_gate) ──── 可并行
  │                    │
  └─ B10 (lens) ──── 可并行
```

B1–B6、B9 已全关。下一步 B7、B8、B10 按需并行。
