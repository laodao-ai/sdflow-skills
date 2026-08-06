# bundle skew 由分发链版本对比判定，不由逐能力内容探测判定

> 状态：**Accepted**（2026-08-06，`fix-probe-scan-precision` 拷问阶段收敛，用户拍板）· 关联 change：`fix-probe-scan-precision`

评审工具分两条**更新速度不同**的分发链：SKILL.md 走 symlink（`git pull` 即生效），
`openspec/workflow/` 下的 tools 与契约走拷贝（须 `sdflow-init update`）。二者不原子 ⇒ 存在
「新 SKILL × 旧 tools」窗口，若不在起手拦下，整轮评审（多镜 fan-out + 跨模型 voice）会在**末步**
lint 才 fail-closed，成本全部报废。

此前的拦法是**逐能力内容探测**：在两个评审 SKILL 的第零步各写一段散文，列举若干条"打开某文件、
grep 某字符串"的检查。`sdflow-code-review` 四条、`sdflow-spec-review` 两条（①②逐字重复）。

该形状有三个已实证的问题：

**① 它是补丁螺旋。** 每给 bundle 加一个特性，就要补一条信号——`absorb-gstack-review` 刚补了
③④两条（contract 的 `scope-audit:` 行、`anchor_lint` 的 `broad` token）。这正是 CLAUDE.md 基准 5
的警号形状：「当你发现每轮 review 都在同一个函数里补一个新的语法分支，那不是"还差最后一个 case"，
那是"这个函数本来就不该存在"」。

**② 它结构上无法被机械守。** SKILL 只描述"检查什么"、不给命令，实施者各自发挥写法；而要机械验证
"SKILL 里写的检查现在还对不对"，程序得先从 markdown 里把命令抠出来 = 手写 markdown 解析器，撞同一条
基准 5。∴ 探测写法失效时**没有任何东西会报警**，只能等下一次评审误停才被发现。

**③ 实证误停。** `absorb-gstack-review` 的 dogfood 首跑，信号②用
`sed -n '/```lens-metric-enums/,/```/p'`（无行首锚定）提取机读块，命中了文件散文里对该 fence 名的
一处提及（「机读取值域单一源见下方 … 的 ```lens-metric-enums``` 块」），截出一段散文 ⇒ 假阴 ⇒
差点硬停整轮评审，而 bundle 实际是新的。

本决策是 `openspec/CONTEXT.md`「**盘面即状态**」在 bundle skew 判定上的落点：判据取确定性产出
（版本 SHA），不取"对内容形态的一组猜测"。

## Decision

bundle skew 判据改为**分发链版本对比**：两条链各自在被刷新时写下自己的版本，探测 = 比两个字符串。

- **版本取值**：`git log -1 --format=%H -- sdflow-init/assets/workflow/`——即 **bundle 作用域**
  最后一次变更的 commit SHA，**不是整仓 HEAD**。整仓 HEAD 每个 commit 都变而 bundle 大多数 commit
  没动（实测：HEAD `0d024ae` 改的是 `setup.sh`，bundle 版本仍为 `ee5b4f4`），用 HEAD 会让源仓每提交
  一次就得 update 一次才能评审，方案会因烦人被绕过。
- **形式**：纯 40 位 commit SHA。**MUST NOT 用 `git describe --dirty`**——开发时工作树常脏，
  `-dirty` 后缀会让版本恒不相等、天天误报；脏状态应单独提示，不混进相等性判断。
- **写入点**：`setup.sh` 写全局侧（刷 canonical 时）、`init.py` 的 `copy_bundle()` 写消费仓侧
  （MUST 放在函数**内部**以同时覆盖 full / 非-full 两分支，否则源仓 `update --dev` 铺完没版本文件、
  反被自己的探测判成陈旧）。
- **缺失即陈旧**：读不到版本文件 ⇒ 判定陈旧并硬停。语义自洽——从没跑过新版 update 的消费仓正是陈旧态；
  与第零步 `resolve-models.sh` 的 `[ -x ]` 预检同 idiom。
- **非 git 环境**：两侧同为 `unknown` ⇒ 相等 ⇒ 放行（fail-open）。与 `setup.sh:735` 现有
  `|| echo "unknown"` 降级一致；改 fail-closed 会让非 git 安装完全跑不了评审。
- **不等即硬停**，不降级为警告。硬停发生在起手（尚未 fan-out、未跑 voice），损失仅为重新起手；
  放行的代价是整轮白跑。报错文案 MUST 含「跑 `sdflow-init update`」。
- 两个评审 SKILL 的内容信号散文**整段删除**（code-review 四条、spec-review 两条）。

**这不是新造机制**：`~/.sdflow/hack/capability-manifest.json`（`setup.sh` 所写，供
`outside-voice-job.py preflight` 检 skew）已是同款模式的先例。`sdflow-code-review/SKILL.md:557`
明写「两条分发链不可互相替代……capability manifest 正是在这一步写；消费仓的
`openspec/workflow/tools/` 走 `sdflow-init update`」——即 **hack 链有 manifest、bundle 链没有**，
缺的那半才不得不用手工内容信号补。本决策把已有模式补全到另一条链。

## Considered Options

- **本方案（分发链版本对比，选中）**：探测逻辑从 O(特性数) 降为 O(1)，新增 bundle 特性时零改动，
  且版本文件是可执行验证的确定性产出、可被 pytest 机械守。代价 = 精确性下降（版本不等未必真不兼容），
  见 Consequences。
- **把四条命令写字面进两个 SKILL（砍掉）**：`fix-probe-scan-precision` 的 todo 原推荐。砍掉理由：
  ① 结构上排除机械守（见上 ②），命令失效时静默，等于把本次的坑原样留在原地、只是这次写对了；
  ② 两个 SKILL 各写一遍 ⇒ 新增漂移面，而本仓对"两 SKILL 共享同一段"的既有解法是脚本化或等值门
  （`check_async_branch_parity.py`），等值门只保证两处一样、不保证它对；③ 补丁螺旋未止。
- **下沉 `tools/skew_probe.sh`，SKILL 只调用并读退出码（砍掉）**：解决了机械守与两处重复。
  砍掉理由：**它仍然是"检查内容特征"，只是把补丁螺旋从散文搬进了脚本**——每加一个 bundle 特性，
  还是要往脚本里加一个 check。治标不治本。
- **给 bundle 全文件算内容指纹（砍掉）**：能同时探到"手改部署副本不回灌"。砍掉理由：把 O(1) 的
  版本对比变回 O(n) 的逐文件校验，绕回本决策要消灭的形状；且该风险已有独立机制覆盖（CLAUDE.md:172
  明令禁止手改下游副本）。见 Consequences 的接受项。

## Consequences

- **版本不等未必真不兼容**——改了 bundle 里任何一个文件（哪怕与评审工具无关）都会让版本变、触发一次
  硬停。**这是本决策明确接受的代价**：误报成本 = 起手硬停一次 + 一次秒级 `sdflow-init update`；
  漏报成本 = 整轮评审白跑。方向上宁可多报。
- **手改消费仓部署副本而不回灌，探测不到**（版本文件不变）。**但现有内容信号同样探不到**——本决策
  未引入新洞，只是没修既有洞。该风险面由 CLAUDE.md:172 的明令与「部署副本漂移只在 update 时暴露」
  的既有认知覆盖。
- **新增两个落盘点与两处写入逻辑**（`setup.sh` / `init.py`），**同时删除**两个 SKILL 里各一整段
  内容信号散文。净复杂度下降。
- **本地 pin 仓不受影响**：`init.py:266-268` 注释确认 pin 仓 pin 的是**规则**、`tools/` 仍走 update
  刷新，版本文件照样有效。
