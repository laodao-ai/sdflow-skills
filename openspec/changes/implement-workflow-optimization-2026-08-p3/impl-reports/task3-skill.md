# Task 3 实现报告：SKILL 编排层 + 消费端

## 范围

Task 3 是纯 Markdown 编排层交付——不写 Python 代码，只补全 `sdflow-upstream-watch/SKILL.md`
的编排正文、`sdflow-upgrade/SKILL.md` 第 5 步陈旧提醒段、README Skills 列表登记。机械层
（`scripts/upstream_watch.py` 的 collect/advance）由 Task 2 交付，Task 3 不改动脚本，
仅在 Markdown 里编排如何调用它。

## 交付物

### 1. `sdflow-upstream-watch/SKILL.md`

- frontmatter `description` 由脚手架阶段占位改为完整触发描述：明示单仓专用（其他项目 cwd
  下调用会被机械 cwd 守卫拒绝）、与 `sdflow-upgrade`（升级工具链）/`sdflow-maintain`（扫结构）
  的职责区分说明，避免误触发。
- 编排正文按运行序列四步落笔：
  1. `collect`（相对路径调脚本，含 cwd 非本仓/anchors 不可解析的 fail-loud 说明）。
  2. 模型读 `.facts/` 下最新一份 JSON（按文件名字典序取最新，命令：
     `ls -1 openspec/upstream/.facts/*.json | sort | tail -1`）写报告（UTC 时间戳文件名，
     `date -u +%Y%m%dT%H%M%SZ`，不覆盖既有报告）。
  3. `advance <报告路径> <facts路径>`（含 sha 漏转录时的处置指引：回步骤 2 补全，不得绕过
     校验手改 anchors.yaml）。
  4. 呈报人（报告路径 + 每源状态 + 吸收候选条数 + 明确不代人拍板执行 recorder add）。
- 报告模板逐源分节：gstack / matt / superpowers / OpenSpec，每源含采集状态行
  （ok/degraded/首轮）；degraded 分支呈现「原因 + 上游 URL」，**本地元数据格式漂移分支例外**
  ——matt 的 `.skill-lock.json`、superpowers 的 `installed_plugins.json` 两处均改为呈现
  本地文件路径 + 具体键路径断言指引（而非上游 URL 模板）；superpowers 节额外说明
  `commits` 与 `source_sha_sequence` 按同一索引一一对应、逐项配对呈现（避免只摘录
  source.sha 序列丢掉 advance 校验依赖的 marketplace 仓 commit sha）；OpenSpec 节明示
  「对比基线 = 已安装版本，非 registry 最新版」（拍板 Q1）。
- 证据不足条款：MUST 标「观望/待核查」不硬判，允许对候选 commit 按需 `git show` 取内容
  （blobless clone 按需拉 blob）。
- 首轮 seed 条款：报告模板含 T245/T246/T267 三条 seed 分诊条目，T245/T246 注记共享
  「解除 design D8（matt-workflow-integration）implementer 档位钉死 mid 档」这一前置人工
  决定（原文依据：`openspec/issues/open/todo/T245.md`/`T246.md` 备注段，两条互相引用同一
  前置决定，T246 原文建议"与 T245 合并讨论"）。
- 入池衔接：watch MUST NOT 直接改池；报告内为每条吸收候选预生成 `sdflow-issues` 的
  `issues_v2.py add` 命令（todo/bug 两个模板），显式传 `source_change: "sdflow-upstream-watch"`
  作为固定溯源标记——**不留空等自动探测**（自动探测会把记录误挂到当时活跃的 change 目录，
  污染该 change 的 sweep 圈选，此为已知坑，见 memory `recorder-add-auto-change-trap`）。

### 2. `sdflow-upgrade/SKILL.md` 第 5 步

追加「陈旧提醒」步骤（TD6）：读运行 checkout `~/.skills/sdflow-skills/openspec/upstream/anchors.yaml`
的 `last_run` 与 `remind_after_days`（`yq -o json`），三态处置：

- 文件不存在 / `last_run` 为 null / yq 解析失败（含未安装）→ 静默跳过，不输出不报错。
- 距今超过阈值 → 输出一行提醒（含天数 + `/sdflow-upstream-watch` 指引）。
- 未超阈值 → 不输出。

MUST NOT 发起网络请求、MUST NOT 使 upgrade 因本步失败而中断——三条处置均已在正文写明。

### 3. README

Skills 列表新增一行 `sdflow-upstream-watch`（分类「维护（单仓专用）」），并同步更新表下方
「数据类 skill」脚注（该 skill 带 `scripts/` + `tests/`，与既有列表里其余数据类 skill 同构，
此处补入避免脚注与实际目录结构脱节——与本次 README 改动同一处，非另开范围）。

## 通则符合性

- **①**：recorder `add` 的准确 CLI 形状（`--pool`/`--json`、`_ADD_ALLOWED_KEYS` 白名单、
  `source_change` 无独立 flag、`add` 不校验 `priority`/`type` 词表）经派发 Explore 子代理
  实读 `sdflow-issues/SKILL.md` 第 230-264 行与 `scripts/issues_v2.py` 第 421/453-459/1311-1314
  行核实，未凭记忆下笔。T245/T246/T267 三条 seed 条目内容与 D8 关联依据同样实读
  `openspec/issues/open/todo/T245.md`/`T246.md` 原文（第 22 行备注）核实。
- **③**：未缩小 brief 范围——四份交付物（SKILL.md 编排正文、sdflow-upgrade 第 5 步、README、
  本报告）全部完成；`tickets.md` 复选框与 checkpoint 标签按信号权威表留给双轴审后的执行模式
  补打，未越权代打。
- **④**：报告模板用一份 Markdown fenced 示例覆盖四源结构差异（不为每源单独写一套模板），
  recorder 命令只给 todo/bug 两个够用模板，未过度设计成可配置的命令生成器。

## 验证

- `/usr/bin/python3 -m pytest sdflow-upstream-watch/tests/ -q` → 58 passed（Task 3 未改
  `scripts/`，此次运行是确认 Markdown 改动未意外影响 Task 2 交付的机械层）。
- `git diff` 亲验三份改动文件：`sdflow:principles` 托管块（两个 SKILL.md）均未被触碰
  （diff hunk 范围核实在 frontmatter 与 principles-block 之后）。

## 未做 / 遗留

- 未修改 `openspec/changes/.../tickets.md`（复选框与 checkpoint 标签按信号权威表交执行模式
  在双轴审后补打）。
- 未触碰 `CLAUDE.md`「常用命令」段列出的「带脚本+测试的 skill」清单（该清单缺
  `sdflow-upstream-watch`/`sdflow-implement`，是 Task 2 遗留的既有脱节，不在本票 brief 范围
  内，如实记录不代为修正）。
