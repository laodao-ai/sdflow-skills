## 1. 版本写入（P0 · 两条分发链各一处）

- [ ] 1.1 `setup.sh`：刷 canonical 软链的同一步写全局侧版本到 `~/.sdflow/bundle-version`——取值
  `git -C "$REPO_DIR" log -1 --format=%H -- sdflow-init/assets/workflow/`，失败降级字面 `unknown`
  （沿用 `:735` 现有 `|| echo "unknown"` idiom）；**MUST NOT 用 `git describe --dirty`**〔Req:
  host-adaptive-execution·探测判据 = 分发链版本对比〕
- [ ] 1.2 `sdflow-init/scripts/init.py`：在 **`copy_bundle()` 函数内部**写消费仓侧版本到
  `openspec/workflow/.bundle-version`。**MUST 放函数内、不放调用点 `:1127`**——`full=True`（源仓
  `--dev` 整刷）与 `full=False`（消费仓常规 update）两分支共用该出口，放调用点会漏掉 `--dev` 路径，
  导致源仓铺完无版本文件、反被自己的探测判成陈旧〔Req: 同上〕
- [ ] 1.3 两处取值命令与降级行为 SHALL 一致（同一条 `git log -1 --format=%H -- <bundle>`、同一个
  `unknown` 降级），否则两侧恒不相等 ⇒ 永久误报〔Req: 同上〕

## 2. 判据替换（P0 · 两个评审 SKILL，同一段措辞）

- [ ] 2.1 `sdflow-code-review/SKILL.md` 第零步 skew 段：**删除四条内容信号整段**（含
  `absorb-gstack-review` 刚加的③④：contract 的 `scope-audit:` 行、anchor_lint 的 `_MIRRORS_LEGAL`
  含 `broad`），替换为版本对比判定表（相等/不等/缺失/双 unknown 四态）〔Req: 同上·四个 Scenario〕
- [ ] 2.2 `sdflow-spec-review/SKILL.md` 第零步 skew 段：**删除两条内容信号整段**，替换为与 2.1
  **逐字一致**的判定表——同一判据 MUST NOT 各写一套（现状①②逐字重复已是漂移面，本 change 收敛）
  〔Req: 同上〕
- [ ] 2.3 两处替换 MUST 保留既有语义契约措辞不变：fail-loud、硬停时点（任何 fan-out / 调 emitter /
  落 v2 锚之前）、「MUST NOT 产出无锚报告 / MUST NOT 落 v1 旧锚（假绿）/ MUST NOT 静默清零本段」
  ——这些不随判据形式改变〔Req: 同上·Scenario 两侧版本不等则 fail-loud 硬停〕
- [ ] 2.4 报错文案 SHALL actionable 且按缺失侧分流：消费仓侧缺/不等 → 提示 `sdflow-init update`；
  全局侧缺 → 提示 `bash setup.sh`〔Req: 同上·Scenario 任一侧版本文件缺失同样判陈旧〕

## 3. 机械守（P0 · hack/tests/）

- [ ] 3.1 新增 pytest 覆盖**写入点**：`setup.sh` 跑完后 `~/.sdflow/bundle-version` 有内容且形如
  40-hex 或 `unknown`（沿用 `test_install_agents.py` 的假 HOME 真跑 bash 模式 + 「真实目录未被动过」
  护栏）〔Req: 同上〕
- [ ] 3.2 新增 pytest 覆盖 `copy_bundle()` **两分支**：`full=True` 与 `full=False` 跑完后消费仓
  `openspec/workflow/.bundle-version` 均有内容（`tmp_path` + monkeypatch `BUNDLE_SRC`，零全局影响）
  〔Req: 同上；本条即 1.2「放函数内」的机械守——放错位置时 `full=True` 分支当场红〕
- [ ] 3.3 新增测试：两处取值命令一致性（1.3 的机械守）——断言两侧对同一 checkout 取到相同版本值
- [ ] 3.4 **诚实边界 MUST 写进测试文件 docstring**：判定逻辑在 SKILL 指令层（主 session 执行），
  本组测试守的是**写入点与取值命令**两个机械面；「SKILL 是否真照判定表执行」仍由执行方自报，
  **MUST NOT 声称机械保证**。与现状相比是净增益——现状连写入点都没有，整条路径零机械覆盖

## 4. 文档订正与记录闭环（P1）

- [ ] 4.1 `CLAUDE.md` 订正仓根 `openspec/workflow/` 描述：由「只保留 `tools/`」改为实际形态并写明各自
  理由——`tools/`（`ship_gate.py:953-955` 参与 code 域失鲜判定的真代码）+ `lens-metric-contract.md`
  （`anchor_lint.py` 运行时机读依赖，须与 tools/ 同批刷新）+ `WORKFLOW-GUIDE.md`（人读手册）+
  本 change 新增 `.bundle-version`。目的：让下一个人 grep 到它们时不再误判为死件〔Req: proposal·文档订正〕
- [ ] 4.2 关闭 `T270`（由本 change 解决，`set-status DONE` + evidence 锚本 change 名）
- [ ] 4.3 关闭 `T269` 为**误判**——`set-status` 时 MUST 写明判定依据（那两个文件在消费仓是活件，
  `init.py:266-278` 注释为证；真问题是 grep 假阳、与 T270 同根因，已由本 change 从判据侧解决），
  **MUST NOT 静默关闭**〔Req: proposal·关闭 issues〕

## 5. 验证与收尾（P0-P1 共用出口）

- [ ] 5.1 全仓 pytest 绿（`/usr/bin/python3 -m pytest`——含 3.x 新增用例）
- [ ] 5.2 Success Metrics 核验：两个评审 SKILL 的探测段内不再有逐能力内容检测描述
  （`grep -n "lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL" sdflow-code-review/SKILL.md
  sdflow-spec-review/SKILL.md` 在探测段内归零；其它段落的合法引用不计，逐条判定并写明）；
  `openspec validate --strict` 绿
- [ ] 5.3 三态实测（真跑，非推演）：构造版本相等 ⇒ 放行；改一侧使不等 ⇒ 硬停且文案含
  `sdflow-init update`；删一侧文件 ⇒ 硬停。三态各贴命令与输出
- [ ] 5.4 **发布纪律写进 hand-off**：本 change 同改 SKILL（symlink 即时）与 bundle（拷贝惰性），
  合并后**首次评审必然硬停一次**（消费仓尚无版本文件）——这是设计内的 fail-loud 路径、非缺陷；
  正确顺序 = push → 运行 checkout `git pull` → **立即** `bash setup.sh` → 各消费仓 `sdflow-init update`

## 测试覆盖图（TG-18）

```
code path                              测试类型
─────────────────────────────────      ─────────────────────────────
setup.sh 写全局侧版本               →  假 HOME 真跑 bash（3.1）
copy_bundle() full=True 分支写版本   →  tmp_path + monkeypatch BUNDLE_SRC（3.2）
copy_bundle() full=False 分支写版本  →  同上（3.2）
两处取值命令一致                     →  pytest 断言同 checkout 取值相等（3.3）
SKILL 判定表（四态）行为             →  真跑三态实测（5.3，指令层无自动化）
两个 SKILL 判定段措辞一致            →  人审（markdown 指令资产；未加等值门，见 design Risks）
CLAUDE.md 订正                       →  人审（纯文档）
```
