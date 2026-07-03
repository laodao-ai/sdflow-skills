# Tasks: sdflow-rebrand

> 决策真相源 = [proposal.md](./proposal.md) + [design.md](./design.md)（§三 RENAME-MAP / §四 D1-D8）+ [spec-review-report.md](./spec-review-report.md)。
> 全部未勾（ff + spec-review amendment，实现在阶段三）。需求 ID：**R-SR-1** 命名与品牌一致性 · **R-SR-2** 安装器品牌与 marker 兼容 · **R-SR-3** 托管区块 marker 迁移（ADDED，spec-review 新增）。
> spec-review 2026-07-03〔spec-review-amendment〕：新增 0 组前置修复（改名的硬依赖地基）；1.2 引用面扩至第⑥类；4.3 断言逐名 pattern + 挪至末位；5.3 真实激活改道 merge 后新会话 /sdflow-upgrade。
> **设计门拍板（2026-07-03）**：Q1=A（0 组纳入 scope）· Q2=维持 no-stub · Q3=追认 grill 跳过（T19 评估债保留）。

## 0. 前置修复（改名硬依赖的坏地基，先修后改名）〔spec-review-amendment〕

- [ ] 0.1 **修 `cleanup_orphans` dangling 枚举**〔autoplan F0 / 迁移镜 F1，双沙箱实证〕：`setup.sh:69` 尾斜杠 glob（`for entry in "$dest"/*/`）结构性看不见 dangling 软链（POSIX 语义悬空链不匹配目录 glob）——改 `find "$dest" -mindepth 1 -maxdepth 1` 枚举；`:70` 的 `[ -e ]` guard 同步梳理。**测试**：假 HOME 预置 dangling 自属链 → setup → 被清（此前该路径是死代码，无此测试即假绿）〔R-SR-1〕
- [ ] 0.2 **inject() 托管区块 marker 迁移**〔autoplan F1 CRITICAL〕：`init.py:33-35` 的 MARK_DOC/MARK_IDX 全文精确匹配且文案含 "opsx-project-init"——改**token 基匹配**（定位 `opsx-init:start` / `opsx-init:rules:start` 令牌行而非整串），新写 marker 文案更新为 sdflow-init、旧 marker 行天然被 token 命中替换。**测试**：预置旧 marker 区块的消费仓 CLAUDE.md → update → 区块被**替换**而非追加重复、旧块不失管〔R-SR-3〕

## 1. 改名执行（RENAME-MAP 驱动）〔R-SR-1〕

- [ ] 1.1 `git mv` ×9（一次提交保 rename 检测）：opsx-project-init→sdflow-init、opsx-done→sdflow-done、opsx-maintain→sdflow-maintain、opsx-roadmap-planner→sdflow-roadmap、spec-review→sdflow-spec-review、impl-review→sdflow-code-review、buglist-recorder→sdflow-buglist、todolist-recorder→sdflow-todolist、issues-recorder→sdflow-issues
- [ ] 1.2 功能性文本 sweep（RENAME-MAP × 引用面①-⑥，**显式文件清单**〔spec-review-amendment：原四类扩至六类〕）：
  - ① `assets/workflow/workflow.md` 步骤表 prompt
  - ② `assets/snippets/claude-section.md` + `index-section.md`（配套 skill 表 + 安装句）
  - ⑤ `setup.sh`——含 **:109/:133 承重路径**（`$REPO_DIR/opsx-project-init/assets/...` → `sdflow-init/assets/...`，install_sdflow 的 bundle 与 hack 源，改漏 = canonical 断链〔autoplan F4〕）；`scripts/init.py`（:4 自称 / :313 提示句）；`README.md` 列表；`CLAUDE.md` 正文（托管区块走 5.4 重注入）；`opsx-project-init/scripts/gen_review_stub.py:24` 用户可见报错文案〔F6〕
  - ⑥ **规则方法论文档**〔引用面镜 F1，运行时被 resolver 加载的活跃规则〕：`assets/workflow/spec-review.md`、`ff-generation-constraints.md`、`reference/quality-layering.md`、`reference/README.md`、`reference/Token_Saving_Strategies.md`、`tools/vendor/NOTICE.md`（仅我方自撰提示行）
  - ＋ `openspec/config.yaml` context 字段〔引用面镜 F2，每次 ff 注入 prompt 的活跃上下文〕
  - ＋ 低优先顺手：`assets/hooks/change-review-stub.py` 注释自称（功能无涉，引用面镜已核）
- [ ] 1.3 sibling 硬编码换新〔D4〕：`issues.py:64-65` 目录名 join → `sdflow-buglist`/`sdflow-todolist`；**全部 7 个测试文件**中的路径/目录名引用修正（三 recorder/issues tests + opsx-project-init tests 内 REPO 相对路径断言〔F6〕）
- [ ] 1.4 `sdflow-done/SKILL.md` §2.1 固定脚本路径三行（:109-111）换新名 + 兜底 find 提示句同步

## 2. 触发词重写〔R-SR-1，D2〕

- [ ] 2.1 9 个改名 SKILL.md description 重写：换 slash 新名与自称；原触发场景语句集全保留；旧名指称清零
- [ ] 2.2 产出 `trigger-map.md`（随 change 留档）+ **机械断言**〔autoplan F9：抽查太薄违 adr/0006〕：每 skill 列旧 description 的触发短语集，脚本核验其**逐条 ⊆ 新 description 文本**（grep 循环即可），断言输出留档——人工抽查仅作补充非主锚

## 3. 品牌收拢〔R-SR-2〕

- [ ] 3.1 新建 `VERSION` = `0.9.0`；`setup.sh` 摘要输出 `sdflow-skills v${VERSION}`
- [ ] 3.2 marker：新写 `.sdflow-skills`；`.laodao-skills` 兼容**收窄**〔autoplan F8：Windows 双仓共存下全量兼容会误刷 laodao misc 拷贝〕——仅当目录名 ∈ RENAME-MAP 旧名∪新名∪保留名单时才把旧 marker 识别为自属；名单外的 `.laodao-skills` 拷贝一律视为非自属 skip（laodao 仓自己的 misc 财产）。涉及 setup.sh :37/:41/:45/:52/:84 五处判断点〔迁移镜 F4：非一行活〕
- [ ] 3.3 品牌叙述清扫：snippets/README/CLAUDE.md 正文"来自 laodao-skills"类表述；laodao 旧仓不动（Non-Goals）

## 4. 测试与断言〔R-SR-1/2/3〕

- [ ] 4.1 新增测试：跨改名孤儿清理（**依赖 0.1 已修**；断言旧链消失+新链存在，双向）；marker 兼容收窄（名单内识别/名单外 skip 两向）；marker token 迁移防重复区块（0.2）；setup 版本行 `sdflow-skills v0.9.0`；安装布局冒烟（readlink canonical + hack 两脚本，〔F4/F12〕）
- [ ] 4.2 存量测试路径修正后全量 `python3 -m pytest -q` 全绿无 warning
- [ ] 4.3 **白名单反向断言（挪至 5.4 之后执行，本组仅定义）**〔autoplan F2/F3/F5〕：
  - **逐名定制 pattern 防子串碰撞**：`spec-review`/`impl-review` 等用负向匹配排除新名（如 `grep -rP '(?<!sdflow-)spec-review'`）；`workflow/spec-review.md` 规则**文件名**不改（它是方法论文档名非 skill 名）→ 文件名命中白名单化，只断言文内 slash/skill 指称
  - **白名单补全**：+`openspec/issues/`（债池历史记录）+`docs/`+`memo-*.md`+`openspec/config.yaml` 之外的历史行……以 spec-review-report 附录清单为准
  - 断言命令逐条写死（每旧名一条），输出留档 change 目录

## 5. 激活与文档收尾

- [ ] 5.1 落 `adr/0007-sdflow-naming-consolidation.md`：命名决策 + plugin/半量否决 + **LOW 8 项收录**（impl→code 非机械映射理由、openspec-upgrade 豁免理由、双品牌过渡、回滚边界"消费仓侧非自动回滚"等〔autoplan LOW/F10〕）
- [ ] 5.2 ROADMAP：`extract-sdflow-repo` 行更名 `sdflow-rebrand`（supersede 注记 + 状态推进）
- [ ] 5.3 〔spec-review-amendment 重写：F7/迁移镜 F2/F3——**实现期禁跑真实 setup**〕实现期验证 = 4.1 沙箱测试（假 HOME，全隔离）；**真实激活改道**：merge + push 之后、**新会话**经 `/sdflow-upgrade` 在 canonical（`~/.skills/sdflow-skills`，REPO_NAME 匹配旧链可清）执行 pull+setup——时序自然断开自指（本 session 后续 /impl-review /opsx-done 继续用运行 checkout 旧名版本，不受 dev 改名影响）
- [ ] 5.4 `python3 sdflow-init/scripts/init.py update --dev --root .` 同步 instance 与托管区块（marker 迁移 0.2 在此实测生效）→ **随后执行 4.3 断言**（顺序硬约束：断言最后，防托管区块假 FAIL〔F3〕）
- [ ] 5.5 hand-off 升格〔F11 + 引用面镜 F3〕：①消费仓迁移验收项（跑 `sdflow-init update` + 确认托管区块新名，带"下次使用前"时限）；②新会话触发抽查清单（3 条真实语句）；③用户全局 `~/.claude/CLAUDE.md` 旧名示例提醒（仓外，grep 网够不到，非强制）；④merge 后 `/sdflow-upgrade` 激活步骤
