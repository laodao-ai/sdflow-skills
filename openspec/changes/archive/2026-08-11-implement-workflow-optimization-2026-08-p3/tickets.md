---
impl-pipeline: tickets
---

## Global Constraints

以下逐字摘自本 change design.md 的 MUST/MUST NOT/SHALL 硬约束与 Compliance 条款：

- 机械层「零解析上游内容」：delta 事实全部由 git / npm / sha256 自己回答（`ls-remote`、`log`、`npm view`、整文件 digest），不手搓任何上游格式解析器（基准 5）。
- 锚推进与报告产出绑定：anchors 只由脚本写，advance 以**报告路径 + facts 路径**双参数绑定本轮——不存在「锚走了、报告没了/报告是别轮的/报告漏转录」的静默丢轮。
- 采集失败按源降级、fail-loud、不互相传染：单源不可达/格式漂移只降级该源节。
- anchors.yaml 读写走 `yq`（三态错误语义：文件缺失=首轮初始化；yq 失败=fail-loud；值缺失=该源视为无锚首轮），含 mikefarah-flavor 探测 idiom（各自实现、不跨目录 import；非 mikefarah 家族 yq 直接报错阻止误用）。
- 脚本起手守卫检测 cwd 非 sdflow-skills 仓时 fail-loud 退出，不在其他项目写入任何文件（proposal A4）。
- 全部外部子进程统一数字化超时（单点常量，默认 60s/次调用），超时按该源 degraded 处置。
- git 源取 delta 前先 `git merge-base --is-ancestor 锚 HEAD`：非祖先→该源 degraded「锚失效」。
- bare 缓存 fetch 失败→删缓存重 clone 一次自愈，再失败才 degraded。
- `installed_plugins.json` per-plugin 多记录数组取值：优先 scope=user，无则取版本最大。
- superpowers 追踪 marketplace.json 中 superpowers 条目的 `source.sha` 字段变化序列，MUST NOT 用路径过滤（该仓不 vendor 插件内容）。
- facts JSON 落 `openspec/upstream/.facts/<UTC时间戳>.json`，`.gitignore` 该目录。advance 观测值只读 facts、禁网络；degraded 源锚逐字保留。
- 报告文件名含 UTC 时间戳到秒，一次运行一份，MUST NOT 覆盖既有报告。
- 分诊证据不足时 MUST 标「观望/待核查」不硬判吸/不吸。
- 吸收候选附预生成 recorder add 命令（含 source_change）。
- git 跟踪产物中的本机路径一律 tilde 记法不展开（本仓为公开仓）。
- 新增 Python 入口脚本带 4 行 reconfigure 前导（CLAUDE.md 机械门）。
- 测试沙盒化（tmp_path + 可注入路径/命令 stub，无网络依赖），零全局影响。

### Task 1: 脚手架 + anchors 基础设施 + cwd 守卫

**Blocked-by:** none
**R-ID:** R1, R7

建立 `sdflow-upstream-watch/` 目录骨架与核心基础设施：

1. 建 `sdflow-upstream-watch/` 目录：SKILL.md（frontmatter + 编排指令占位）、`scripts/upstream_watch.py`（4 行 reconfigure 前导 + `collect`/`advance` 子命令骨架 + argparse 入口）、`tests/` 目录。
2. 跑 `python3 hack/sync_principles.py --apply` 注入通则托管块并确认自报投放面计数 +1。
3. 建 `openspec/upstream/` 数据目录（`reports/` 留 `.gitkeep`）。
4. 实现 cwd 守卫（两子命令起手 git remote 判定，非 sdflow-skills 仓 fail-loud 不写文件）。
5. 实现 anchors.yaml 读写层（yq，三态错误语义 + mikefarah-flavor 探测）+ `schema_version` 与 `remind_after_days` 字段。
6. 实现外部子进程统一超时常量（单点定义，默认 60s）。
7. 测试覆盖：cwd 守卫（非本仓 cwd 拒绝零写入）+ anchors 语义（首轮初始化 / yq 失败硬停 / 值缺失无锚）。

- [x] SKILL.md 骨架已建、通则托管块已注入（sync_principles --apply 绿且计数 +1）
- [x] `openspec/upstream/` 目录在 git 中（reports/ 有 .gitkeep）
- [x] cwd 守卫在非 sdflow-skills 仓 cwd 下 fail-loud 退出且零写入
- [x] anchors.yaml 三态读写正确（缺失=初始化 / yq 坏=硬停 / 值缺失=无锚）
- [x] mikefarah-flavor yq 探测正确，非 mikefarah 报错
- [x] 超时常量单点定义且 argparse 入口可用
- [x] 上述各路径有对应 pytest 测试绿

### Task 2: 四源采集器 + facts 输出 + advance 门

**Blocked-by:** 1
**R-ID:** R1, R2, R3

在 Task 1 建立的骨架上实现全部采集逻辑与锚推进门：

1. gstack 采集器：既有 checkout `git fetch origin` + `merge-base --is-ancestor` 锚祖先守卫 + `log --name-only 锚..FETCH_HEAD`；checkout 缺失→degraded；首轮以本地 checkout HEAD 为天然锚出真 delta。
2. bare 缓存采集器（matt / superpowers 共用缓存层）：`clone --filter=blob:none --bare` 到 `~/.cache/sdflow-upstream/`（已存在则 fetch；fetch 失败→删缓存重 clone 自愈）+ is-ancestor 守卫；matt 取 `log --name-only 锚..HEAD`；superpowers 取 marketplace.json superpowers 条目 `source.sha` 字段变化序列（MUST NOT 路径过滤）。
3. openspec 采集器：`openspec --version` vs `npm view` 版本对照 + schema fork 双侧逐文件 sha256 对比（changed/added/removed 清单，零解析）。
4. 本地元数据键路径断言（`installed_plugins.json` superpowers 条目 / `.skill-lock.json`）：断言失败→显式格式漂移 degraded；多记录数组取值策略：优先 scope=user、无则版本最大。
5. facts JSON 输出（per-source，落 `.facts/<UTC时间戳>.json` + `.gitignore`）。
6. `advance` 双参数前置校验（报告缺失/报告缺 facts 任一 commit sha→非零退出锚不动；观测值只读 facts 禁网络；degraded 源锚逐字保留）。
7. 测试覆盖：advance 门（报告缺/缺 sha 拒推/正常推/degraded 不动）+ 采集器降级矩阵（单源不可达/超时/本地缺失/格式漂移/多 scope/非祖先/缓存自愈）+ schema drift（changed/added/removed + 上游缺失降级）+ superpowers 字段追踪 + R5 不改池不变量 + facts 形状快照断言。

- [x] gstack 采集器在有 checkout 时产出正确 delta（含首轮天然锚逻辑），checkout 缺失时 degraded
- [x] bare 缓存采集器正确处理 matt（log --name-only）和 superpowers（marketplace.json source.sha 字段追踪）
- [x] bare 缓存 fetch 失败自愈一次、再失败 degraded
- [x] is-ancestor 守卫对三个 git 源生效，非祖先时 degraded
- [x] openspec 采集器版本对照 + schema drift 清单（changed/added/removed）正确
- [x] 元数据键路径断言失败→格式漂移 degraded（不给错锚）；多 scope 取值正确
- [x] facts JSON 形状正确落盘 + .gitignore 生效
- [x] advance 门：报告缺失拒推/缺 sha 拒推/正常推进 + last_run 更新/degraded 锚不动
- [x] 单源失败不传染（四源降级矩阵测试绿）
- [x] R5 不变量：collect+advance 后 issues 树无变化
- [x] 上述全部路径有对应 pytest 测试绿

### Task 3: SKILL 编排层 + 消费端

**Blocked-by:** 2
**R-ID:** R4, R5, R6

实现 SKILL.md 编排正文（模型驱动分诊报告成文）与 sdflow-upgrade 提醒段：

1. SKILL.md 编排正文：collect → 模型读 facts 写报告（`reports/<UTC时间戳>.md` 不覆盖既有报告；按源分节 + 三分诊 + 每源采集状态行 + degraded 节「原因 + 上游 URL」不罢工 + 格式漂移分支指本地文件与键路径 + 吸收候选附预生成 recorder add 命令含 source_change）→ advance（报告+facts 双参数）→ 呈报人。
2. 首轮 seed 条款：报告 SHALL 含 T245/T246/T267 分诊条目；T245/T246 注明共享「解除 D8 mid 档钉死」前置人工决定。
3. 入池衔接条款：人拍板「吸」→ recorder add 显式 source_change（报告内预生成命令模板）；watch MUST NOT 直接改池；frontmatter description 触发词收敛 + 声明单仓专用。
4. `sdflow-upgrade/SKILL.md` 追加第 5 步提醒段：读 `~/.skills/sdflow-skills/openspec/upstream/anchors.yaml` 的 `last_run` + 阈值比较，缺失/不可解析静默跳过，零网络。
5. README「Skills 列表」加 `sdflow-upstream-watch` 行（注明单仓专用）。

- [x] SKILL.md 编排正文完整（collect→报告→advance→呈报全路径）
- [x] 报告模板含三分诊、每源状态行、degraded 不罢工展示、格式漂移指本地路径
- [x] 吸收候选条目附预生成 recorder add 命令（含 source_change）
- [x] 首轮 seed 含 T245/T246/T267 条目
- [x] frontmatter description 触发词不与 sdflow-upgrade/sdflow-maintain 冲突、声明单仓专用
- [x] sdflow-upgrade 第 5 步提醒段：超阈值提醒/缺失静默跳过/未超阈值不提醒
- [x] README Skills 列表已更新

### Task 4: 首轮 dogfood + 收口

**Blocked-by:** 3
**R-ID:** R1, R2, R3, R4

跑首轮真实 `/sdflow-upstream-watch`（真网络四源采集）并收口散点：

1. 开发 checkout 跑 `bash setup.sh` 验证新链建立 + `--check` 门绿。
2. 真跑 collect（四源真实网络）→ 报告落 `openspec/upstream/reports/` → advance 建锚。
3. 验证 gstack 节含真 delta（`960c3a8..` 区间非空为预期基线）。
4. T264 → DONE（recorder set-status，evidence 指 schema drift 采集器实现 + 测试）。
5. 确认 T245/T246/T267 在首轮报告 seed 节在场后保持池内原状。
6. 全仓 `/usr/bin/python3 -m pytest` 绿。
7. 手工验收 upgrade 提醒两分支（超阈值提醒行 / 无锚静默）。

- [x] setup.sh 新链建立成功 + sync_principles --check 绿
- [x] 首轮 collect 四源均产出 facts（ok 或 degraded 各有据）
- [x] 报告落盘且 gstack 节含真 delta
- [x] advance 建锚成功（anchors.yaml 已创建、last_run 已写入）
- [x] T264 已 set-status DONE（evidence 指采集器）
- [x] T245/T246/T267 池内原状未变
- [x] 全仓 pytest 绿
- [x] [e2e] upgrade 提醒超阈值时输出一行含天数的提醒、无锚时静默跳过

### Task 5: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task5-verify-all.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [x] 单元测试证据齐全并通过
- [x] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [x] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
