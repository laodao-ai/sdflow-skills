# spec-review-report.md — review-tool-followups

> 阶段二设计评审（sdflow-spec-review 编排）。一份合并报告。
> 前置：本 change 已经 grill（design 二次加固）。本评审补 prevention 焊不住的残差：广审 + 领域镜 + 对抗验证。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG-03/19/23，均不在 HR-TG 子集{04,06,07,08,09,16,17,26}，不开领域 cross-model" -->

## 镜阵与触发

- **触发**：TG-03（前端 engine.js）· TG-19（多需求 P2/P3）· TG-23（ADR）。**HR-TG 无命中** → 不开领域 cross-model。
- **Step1 广审（native）**：codex 跨模型外声（4）+ 独立 Claude 广审镜（9），见 `gstack-review.md`。
- **Step2 多镜**：领域镜（frontend.md FE-01/02/03 + backend.md BE-04/10）· 对抗验证镜（证伪 4 高信号 + 挖新爆点）。
- **接地镜显式跳过**（1.4 防重叠，非静默省）：Step1 独立 Claude 广审镜已逐行核验代码事实（engine.js/init.py/setup.sh 全部行号），重复接地无增量。

## 一、决策登记区

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [自动决策] 直接采信高置信 + 清晰修法 → 已回填 design/spec/tasks [spec-review-amendment] │
│ [需拍板]  ≥2 方案 / 扩 T44 责任边界 → 设计 HARD-GATE 一次拍板                      │
│ [已裁掉]  证伪 / 降级 → 连理由留痕（反静默压制）                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

### [需拍板] — 设计门一次性过

**Q-D1〔scope·NEW-2〕settings.json 原子写：本 change 修 vs defer todolist？**
- 背景：`_deregister_hook_in_settings`（init.py:313）truncate-in-place `open("w")`+`json.dump`，无锁非原子。T44 把它接进 `/sdflow-upgrade`，而升级常**从活跃 Claude Code 会话内跑**——恰 CC 自己写 settings.json 时 → 丢更新/撕裂 JSON；崩在 dump 中留坏 JSON，retire 的 fail-safe 读又会静默 no-op 掩盖损坏。T44 使"与活跃会话并发"从边缘变常态。
- 选项：**(A) 本 change 修**（`_deregister` 改 temp 文件 + `os.replace` 原子落，~10 行，略超 T44"复用 retire_hooks 零重写"边界但同文件同函数）／(B) defer todolist（守 T44 纯接线边界，风险留存）。
- **推荐 A**。三镜：系统镜=原子写消除撕裂+掩盖链，是 T44 放大的真实风险；用户镜=避免 settings.json 损坏（用户所有 hook 全丢）；开发循环镜=小改高值，defer 则风险每次升级都在。主次：**用户镜（损坏后果重）＋系统镜（T44 放大了它）** → 本 change 修。
- 后果：A 令 T44 diff 多一个函数（`_deregister` 原子化）+ 一条测试；B 令已知竞态带进生产。

**Q-D2〔scope〕Windows python 命名修到哪？（BE-10 ∩ NEW-5，两镜收敛）**
- 背景：`command -v python3` 在 Windows/Git-Bash（解释器常名 `python`）解析空 → retire 被 fail-safe 静默跳过 → **Windows 机经 /sdflow-upgrade 永拿不到 retire 自愈**（T44 在 Windows 上等于零收益）。且消费仓 `sdflow-init update` 路径同名假设、同洞。
- 选项：**(A) setup.sh 探测退化 `python3 || python`（+ 消费仓 update 路径同修）**／(B) 仅 setup.sh 修，init.py 侧 python3 命名审计记 todo／(C) 维持现状、design 只承认"Windows 可接受降级"。
- **推荐 A**。三镜：系统镜=一处探测退化，小；用户镜=Windows 用户真正拿到 T44 收益（否则声明支持的平台零收益）；开发循环镜=同名假设散在多处，一次修净 vs 留洞复现。主次：**用户镜（声明支持的平台不能零收益）** → A。
- 后果：A 关闭 Windows 洞；C 令 T44 的"闭升级窗口"承诺在 Windows 落空、只是文档承认。

**Q-D3〔risk·BR-9 CEO〕最险活在 P3（T45）无自动化测试——如何兜？**
- 背景：评审揭穿 T45 的 Q3 陈旧-404 处理远比"最小增量单分支"重（须改 navigate 错误契约 / bootstrap 自派发 + 防递归 + notice 注入顺序），而 engine.js 无 pytest、T45 是 P3。低优先级功能扛最重的回归风险。
- 选项：**(A) 完整实现 Q3 + 紧手测清单**（tasks 3.2 已列四态，补 404 态断言）／(B) 拆 Q3 陈旧-404 出去做 follow-up todo，本 change 只落深链happy-path + 最小"清坏 hash 回根"（放弃显式 notice = 退回可接受降级）。
- **推荐 A**。三镜：系统镜=评审已把机制钉死（自派发+replaceState清hash+专用notice节点），实现路径明确；用户镜=B 放弃 notice 即重蹈 CR-V2 的静默降级；开发循环镜=A 一次做全，B 又留一个 followup。主次：**开发循环镜（别再拆出第三个 followup）＋用户镜（notice 是反静默承诺）** → A，但 3.2 手测清单硬约束 404 态。
- 后果：A 要求实现者严格照评审钉的机制走 + 手测四态；B 令深链回归风险低但 UX 退化。

### [自动决策] — 已回填 [spec-review-amendment]（高置信 + 清晰修法）

| # | 主题 | 修法（回填 design/spec/tasks） | 来源（收敛） |
|---|------|--------------------------------|--------------|
| A1 | **Q3 建不在 navigate 上**（navigate 吞错返 undefined，"回落 bootstrap"招递归） | design ADR-2 + tasks 2.3 改：bootstrap **自派发** loadDoc/loadDir（复制 endsWith 逻辑 + currentPath/pushState 记账）于自己 try/catch，404 走 `initialDir==='/'` 的 INDEX 路径**而非重调 bootstrap**，回落前 `history.replaceState` 清坏 hash 防递归。**诚实改口**："增量最小单文件单分支" → "engine.js 内多分支，navigate 契约微调或 bootstrap 自派发" | OV-1+BR-2+FE-02+F-B✅+F-D✅ |
| A2 | **notice 注入顺序**（innerHTML= 会擦掉） | spec/tasks：notice MUST 在 fallback 渲染**之后**、用专用 DOM 节点 `insertAdjacentHTML`/`appendChild`，MUST NOT 用 `contentBody.innerHTML=`（否则被 loadDoc/loadDir 擦→违反静默守卫） | NEW-1+BR-4+FE-02 |
| A3 | **origin 守卫抽 pathname** | spec/tasks：守卫 MUST `new URL(rawHash,origin).pathname` 提取后喂 navigate，非 origin-compare-then-use-raw（顺带归一 %2F 编码 NEW-6）；措辞"复用244"改"re-apply 同一 origin 检查、硬写一行" | OV-3+BR-5+F-C✅+NEW-6 |
| A4 | **retire 分支须在 osroot 前** | tasks 1.2 + design：`retire-hooks` MUST 在 `main()` 或 `run()` 顶**早分支**（先于 init.py:356 osroot 检查），route 到只跑 `retire_hooks()` 的函数；setup 默认 `--root "."` 使此位置载重 | BR-7+NEW-3 |
| A5 | **set -e 构造钉死** | spec/tasks：setup.sh 那行 MUST 以 `\|\| echo`/`\|\| true` 收尾（非仅 `command -v` 门控、非 if-guard——then-body 仍受 set -e） | OV-4+BR-1+BE-04+F-A（PARTIAL：design 已对，钉实现构造） |
| A6 | **Windows python 探测**（见 Q-D2，setup.sh 侧先自动落 A） | setup.sh 探测 `python3 || python`；design ADR-1 Windows 段改口：非单纯"缺 Python"，是"launcher 命名差异致系统性漏 retire" | BE-10+NEW-5 |
| A7 | **`#/` 一致性** | tasks 注：`#/` → slice='/' MUST 走 `initialDir==='/'` 的 INDEX 分支（非 navigate('/') 裸列表），与无-hash 一致 | NEW-4 |
| A8 | **history.state / initialDir** | tasks 注：初始深链成功后 `replaceState({path},'',hash)` 使 Back 回深链；`initialDir` const→computed/let 一处算 hash→守卫→pathname 供 currentPath+popstate 共用 | OV-2+BR-6 |
| A9 | **clean 机 no-op 静默** | tasks 注：retire 无残留时该路径静默/单行 dim，不打印满 banner（spec 已言 no-op） | BR-8 |

### [已裁掉] — 反静默压制（连理由留痕）

| # | 原始发现 | 裁定 | 理由 |
|---|----------|------|------|
| X1 | marked.js 在 hash-render 路径是新依赖风险 | **证伪** | loadDoc:202 无 marked 时已降级 `<pre>`，深链复用 loadDoc 不变，非新险（对抗镜自证伪） |
| X2 | F-B 子claim：改 navigate 返回值须复审 onLinkClick+popstate caller | **降级/部分驳** | 二 caller 忽略 navigate 返回值，**加**返回值向后兼容——核心 F-B 成立，此子claim夸大（对抗镜自纠） |
| X3 | FE-01 深链首屏 fetch 无超时 + 并发 navigate 竞态 | **降级 low·记 todo** | 既有问题，T45 未显著恶化（本地 server "慢网络"概率低）；不阻塞本 change，defer todolist |
| X4 | set -e 会因"新 setup 调旧 init.py"窗口爆 | **降级** | F-A 核实：/sdflow-upgrade 里 git pull 先更新两文件再 setup，窗口largely hypothetical；A5 的 `\|\| echo` 收尾已兜住即便发生 |

## 二、认可项（examined & sound，两镜交叉确认）

`_home_claude` CLAUDE_CONFIG_DIR 同源 · `_deregister` write-only-if-changed 真 no-op（无 mtime 抖）· 协议相对 `#//evil.com` 被 origin 比较正确拒 · server-root 兜路径遍历(`#/etc/passwd`→404) · `copy_bundle`/`copy_review_tool` 未触无部署回归 · ADR-0（合一）+ eager-retire/opt-in-ensure 不对称自洽。

## 三、收敛口

- 自动决策 A1–A9 已回填 design/spec/tasks（[spec-review-amendment]）。
- **3 项需拍板（Q-D1/D2/D3）留设计 HARD-GATE**——建议人工一次性过本报告拍板。
- 拍板批准后进 writing-plans / 实现。**评审揭穿的核心**：T45 的 Q3 远比原设计估的重（navigate 契约 + 防递归 + notice 注入顺序），实现须严格照 A1/A2 钉的机制走，否则反静默承诺静默落空。

## 四、设计门拍板记录

- **2026-07-05 · 用户批准（设计 HARD-GATE）**：3 项需拍板 **Q-D1 / Q-D2 / Q-D3 全采推荐 A**——① settings.json 原子写本 change 修（task 1.4b）；② Windows `python3 || python` 双修 setup.sh + 消费仓 update 路径（task 1.3）；③ 完整实现 T45 Q3 + tasks 3.2 四态手测硬约束。A1–A9 自动决策一并生效。批准进 writing-plans / 实现。

<!-- ship-gate: design-approved -->
