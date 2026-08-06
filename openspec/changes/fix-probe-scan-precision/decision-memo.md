---
schema_version: 1
change: fix-probe-scan-precision
branch: feat/fix-probe-scan-precision
generated_at: 2026-08-06T17:40:00+08:00
decision_hash: 80c788cca7bc
---

# 决策纪要 · fix-probe-scan-precision

## 目标态

让 skew 探测与残留扫描的写法精确到不产生假阴/假阳，并订正文档对仓根 `openspec/workflow/` 层的描述。

## 拍板决策

- **D1 T269 从「删两个孤儿副本」改为「订正 CLAUDE.md 措辞 + 关闭 T269 为误判」** — 依据：那两个文件
  在消费仓是活件，T269 的「功能死件」判断只对源仓成立，而它抱怨的真问题（`grep gstack` 假阳）与 T270
  同根因——都是**扫描/探测写法不精确导致误判**，正解是修探测不是删数据；**砍掉的候选**：①让 `init.py`
  区分源仓/消费仓、源仓不铺（砍因：给 init.py 加一个只为源仓服务的分支，且源仓 dogfood 真实性下降）
  ②照原 todo 删文件 + 加防重铺机制（砍因：与 update 的托管刷新语义正面冲突，每次 update 都要打架）。
  **证据锚**：「人 2026-08-06 明确确认（回复『同意』）」

- **D2 用「bundle 版本对比」整体替代四条内容特征信号（人提出，推翻 todo 与我先前的两个方案）** —
  依据：四条信号是「每加一个 bundle 特性补一条」堆出来的（本 change 原本还要再加③④两条），命中
  CLAUDE.md 基准 5 的警号形状「每轮都在同一处补新分支 ⇒ 这个东西本来就不该长这样」；版本对比是 O(1)，
  加多少特性探测逻辑零改动，且不存在 fence 提取撞散文这类假阴面（T270 的坑在此方案下**不存在**）。
  **砍掉的候选**：①把四条命令写字面进两个 SKILL（砍因：结构上无法机械守，见 C5；且两处重复）
  ②下沉 `skew_probe.sh`（砍因：仍是「检查内容特征」，只是脚本化了——补丁螺旋没停，加特性还要加 check）。
  **证据锚**：「人 2026-08-06 明确提出并确认（『init 时自动生成一个记录当前 git 版本的文件就可以了，
  检查时对比 git 版本号』/ 回复『同意』）」
- **D3 版本形式 = 纯 git commit SHA，MUST NOT 用 `git describe --dirty`** — 依据：开发时工作树常脏，
  `-dirty` 后缀会让版本恒不相等、天天误报；脏状态应单独提示，不混进相等性判断。**证据锚**：人 2026-08-06 确认
- **D4 两条分发链各自在被刷新时写下自己的版本，探测 = 比两个字符串** — 依据：`setup.sh` 刷全局、
  `init.py update` 刷消费仓 bundle，各写各的落点，语义自洽无第三方协调。**证据锚**：人 2026-08-06 确认
- **D5 非 git 环境两边同为 `unknown` ⇒ 相等 ⇒ 放行（fail-open）** — 依据：与 `setup.sh:735` 现有
  `|| echo "unknown"` 降级一致；改 fail-closed 会让非 git 安装完全跑不了评审。**证据锚**：人 2026-08-06 确认
- **D6 版本取值用 bundle 作用域而非整仓 HEAD**：`git log -1 --format=%H -- sdflow-init/assets/workflow/` —
  依据：整仓 HEAD 每个 commit 都变、而 bundle 大多数 commit 没动，用 HEAD 会让源仓每提交一次就得
  update 一次才能评审，方案会因烦人被绕过；bundle 作用域精确匹配「bundle 是不是旧的」这个探测语义。
  **砍掉的候选**：整仓 `git rev-parse HEAD`（砍因：见上实测）。
  **证据锚**：实测 `git rev-parse HEAD`=`0d024ae`（改 setup.sh）vs
  `git log -1 --format=%H -- sdflow-init/assets/workflow/`=`ee5b4f4` ⇒ 二者确实不同，误报真实存在

- **D7 写版本的动作放在 `copy_bundle()` 内部，覆盖 full/非-full 两分支** — 依据：`init.py:1127`
  `copy_bundle(root, full=dev)` 两分支共用一个出口，放调用点会漏掉源仓 `update --dev` 路径，
  导致源仓铺完没版本文件、反被自己的探测判成陈旧。**证据锚**：`sdflow-init/scripts/init.py:1127`
- **D8 版本不等 ⇒ 硬停，不降级为警告** — 依据：硬停发生在**起手**（尚未 fan-out、未跑 voice），
  损失仅为重新起手；放行的代价是整轮评审白跑；与既有 pull→setup 纪律同构。报错文案 MUST 含
  「跑 `sdflow-init update`」。**证据锚**：现有四条信号即硬停语义（`sdflow-code-review/SKILL.md:206`），
  本决策维持该强度不变

## 承重约束

- **C1 那两个文件在消费仓是活件，不是死件** — 验证方式：读 `init.py` 非-full 分支的拷贝逻辑与其注释；
  **证据锚**：`sdflow-init/scripts/init.py:266-278`——contract 注释「是 tools/anchor_lint.py 的运行时
  机读依赖（读 lens-metric-enums 块），须与 tools/ 同批刷新，否则本地 pin 消费仓 update 后『新脚本+旧
  契约无块』永久 fail-closed」；guide 注释「【给人看的】完整手册……人需要一份不用跳文件的完整参考」
- **C2 仓根 `openspec/workflow/tools/` 有真消费方，不可一并清理** — 验证方式：全量 grep 引用点；
  **证据锚**：`sdflow-ship/scripts/ship_gate.py:953-955` `tools_spec = (b"openspec/workflow/tools/",)`
  注释「含真运行代码（anchor_lint.py 等），排除整棵 openspec 会漏判」——它参与 code 域失鲜判定
- **C3 行首锚定的单条 grep 已足够精确，fence 块提取非必需** — 验证方式：对真实 contract 实跑；
  **证据锚**：`grep -c "^runner:.*none" lens-metric-contract.md` = 1（精确命中 :28）；散文里的同名条目
  形如 `- runner∈ {claude, codex, none, unknown}`（:11，行首为 `- `、用 `∈` 非 `:`）⇒ 不被 `^runner:` 误命中
- **C4 两个评审 SKILL 共享信号①②，spec-review 侧有完全相同的假阴风险** — 验证方式：逐字比对两处探测段；
  **证据锚**：`sdflow-code-review/SKILL.md:206`（四信号）与 `sdflow-spec-review/SKILL.md:180`（信号①②
  描述逐字相同）⇒ 只修 code-review 是点补，两处同治才是面治（基准 3）
- **C5 散文里的字面命令结构上无法被机械守** — 验证方式：推演测试可行性；
  **证据锚**：要测「SKILL 里写的命令是否仍对」必须先从 markdown 里提取命令 = 解析 markdown（基准 5
  禁手搓无界语法面）⇒ 「写进 SKILL 散文」这个方案**结构上排除了机械守**，只能靠下一次 dogfood 误停
  一轮评审才发现（本次即该路径）
- **C6 探测产物自身缺失，本身即最强的 bundle 陈旧信号（鸡生蛋自解）** — 验证方式：推演旧 bundle 场景；
  **证据锚**：旧 bundle 无版本文件 ⇒ SKILL 读不到 ⇒ 该缺失**正是**「bundle 陈旧（从没跑过新版 update）」
  的判定结果，语义自洽且比内容信号更早触发；与 `resolve-models.sh` 的 `[ -x ]` 预检同 idiom
  （`sdflow-code-review/SKILL.md` 第零步已有先例）。〔本条原为 `skew_probe.sh` 而立，D2 改用版本对比后
  论证同样成立，故保留并改述——判据形状不变：产物缺失 = 陈旧〕
- **C7 本仓已有同款 manifest 模式，但只覆盖了两条分发链中的一条** — 验证方式：读实际落盘文件 + SKILL 自述；
  **证据锚**：`~/.sdflow/hack/capability-manifest.json` 实内容为
  `{"entries": {"outside-voice-job.py": "28dbed6d…", "outside-voice.sh": "8e8742c3…",
  "skill-principles.md": "ed61e1e2…"}, "generation": "41183542…", "schema_version": 1}`（`setup.sh` 所写，
  供 `outside-voice-job.py preflight` 检 skew）；而 `sdflow-code-review/SKILL.md:557` 明写
  「两条分发链不可互相替代……**capability manifest 正是在这一步写**；消费仓的 `openspec/workflow/tools/`
  走 `sdflow-init update`」⇒ **hack 链有 manifest、bundle 链没有**，缺的那半才不得不用四条手工内容信号补。
  ∴ D2 不是新造机制，是把已有模式补全到另一条链
- **C8 `setup.sh` 已在算版本，但只打印未落盘** — 验证方式：读源码；
  **证据锚**：`setup.sh:735` `version="$(git -C "$REPO_DIR" describe --tags --always --dirty 2>/dev/null || echo "unknown")"`
  ——仅用于汇总打印，没有写进 `~/.sdflow/` 供消费方比对（D3 另定改用纯 SHA，故此处不复用其 describe 形式，
  只复用「取版本 + `|| unknown` 降级」这一 idiom）


## 接受的边角

- **手改消费仓部署副本（不回灌）探测不到** — 概率：低（CLAUDE.md:172 明令禁止「只改某个下游项目的
  `openspec/workflow/` 后忘记回灌」）；影响：中（副本与权威源漂移，下次 update 被覆盖）；完美成本：高
  （要给 bundle 全文件算内容指纹，把 O(1) 的版本对比变回 O(n) 的逐文件校验）。
  **为何接受**：① 现有四条内容信号**同样探不到**这种手改，本方案未引入新洞、只是没修既有洞；
  ② 为它加内容指纹会绕回本 change 要消灭的补丁螺旋（基准 5）；③ 已有独立机制覆盖该风险面
  （memory「部署副本漂移只在 update 时暴露」+ CLAUDE.md 明令）。
- **本地 pin 仓不受影响，无需特殊处理** — `init.py:267` 注释确认 pin 仓 pin 的是**规则**、
  `tools/` 仍走 update 刷新 ⇒ 版本文件对 pin 仓照样有效。此条非风险，登记以免未来读者重复推演。

## 三镜代价

命中 TG-23（≥2 合理方案：字面命令 / `skew_probe.sh` / 版本对比三选一），书面写满：

- **系统镜**：新增两个落盘点（全局 `~/.sdflow/` 一处、消费仓 `openspec/workflow/` 一处）与两处写入逻辑
  （`setup.sh` / `init.py`）；**同时删除**两个 SKILL 里各一整段内容信号散文（code-review 四条、
  spec-review 两条）。净复杂度下降：探测逻辑从 O(特性数) 降为 O(1)，新增 bundle 特性时零改动。
  与本仓既有 `capability-manifest.json` 模式同构（C7），不引入新范式。可回退（两处写入 + 两段 SKILL 措辞）。
- **用户镜**：bundle 真变更后首次评审会硬停一次，提示跑 `sdflow-init update`（秒级）；
  相比现状，**消除了「工具其实是新的却被误判为旧」的假阴误停**（本 change 的起因）。
- **开发循环镜**：新增探测信号的成本从「改两个 SKILL 的散文 + 无法机械守」降为**零**（版本对比自动覆盖）；
  且命令正确性可被 pytest 机械守（现状结构上做不到，C5）。
- **主次判定**：**开发循环镜为主**——本 change 的根本目的是终止「每加特性补一条信号」的补丁螺旋并让它可
  机械守；系统镜次之（净复杂度下降）；用户镜为附带收益。
