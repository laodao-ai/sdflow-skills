# Tasks · implement-workflow-optimization-2026-08-p3

> Requirement ID 对照（specs/upstream-watch/spec.md）：
> **R1** 锚文件独占维护 + 锚推进绑定报告+facts · **R2** 四源采集降级不传染 ·
> **R3** schema fork drift 对比 · **R4** 分诊报告 · **R5** 入池衔接 · **R6** upgrade 陈旧提醒 ·
> **R7** 仅限本仓运行守卫 [spec-review-amendment]

## 1. 脚手架

- [x] 1.1 建 `sdflow-upstream-watch/` 目录骨架：SKILL.md（frontmatter + 编排指令占位）、
      `scripts/upstream_watch.py`（4 行 reconfigure 前导 + `collect`/`advance` 子命令骨架）、
      `tests/` 空壳；跑 `python3 hack/sync_principles.py --apply` 注入通则托管块并确认
      自报投放面计数 +1（R1–R5 载体）
- [x] 1.2 建 `openspec/upstream/` 数据目录约定（anchors.yaml 由脚本首轮创建，目录进 git；
      `reports/` 留 `.gitkeep` 或首份报告时建）（R1）

## 2. 机械层（scripts/upstream_watch.py）

- [x] 2.0 [spec-review-amendment] cwd 守卫（两子命令起手 git remote 判定，非本仓 fail-loud
      不写文件）+ 外部子进程统一超时常量（单点定义，默认 60s/次）（R7/R2）
- [x] 2.1 anchors.yaml 读写（yq，三态错误语义：缺失=首轮初始化 / yq 失败=fail-loud 硬停 /
      值缺失=该源无锚；复用 retro_report.py 的 mikefarah-flavor 探测 idiom，各自实现不 import
      [spec-review-amendment]）+ schema_version 与 `remind_after_days` 字段（R1）
- [x] 2.2 gstack 采集器：既有 checkout `git fetch origin` + `merge-base --is-ancestor` 锚祖先
      守卫 [spec-review-amendment] + `log --name-only 锚..FETCH_HEAD`；checkout 缺失 →
      degraded；首轮以本地 checkout HEAD 为天然锚出真 delta [spec-review-amendment]（R2）
- [x] 2.3 bare 缓存采集器（matt / superpowers 共用缓存层）：`clone --filter=blob:none --bare`
      到 `~/.cache/sdflow-upstream/`（已存在则 fetch；fetch 失败 → 删缓存重 clone 一次自愈
      [spec-review-amendment]）+ is-ancestor 守卫；matt 取 `log --name-only 锚..HEAD`；
      **superpowers 取 marketplace.json superpowers 条目 `source.sha` 字段变化序列（MUST NOT
      路径过滤，该仓不 vendor 插件）** [spec-review-amendment]；上游不可达/超时 → degraded（R2）
- [x] 2.4 openspec 采集器：`openspec --version` vs `npm view` 版本对照 + schema fork 双侧
      逐文件 sha256 对比（changed/added/removed 清单，零解析）；上游目录定位失败 →
      该子项 degraded（R2/R3）
- [x] 2.5 本地元数据键路径断言（`installed_plugins.json` superpowers 条目 /
      `.skill-lock.json`）：断言失败 → 显式格式漂移 degraded，MUST NOT 静默给错锚；
      多记录数组取值策略：优先 scope=user、无则版本最大 [spec-review-amendment]（R2）
- [x] 2.6 facts JSON 输出（per-source status/reason/commits/changed_paths/drift 清单，落
      `openspec/upstream/.facts/<UTC时间戳>.json` + `.gitignore` [spec-review-amendment]）+
      `advance` 双参数前置校验（报告缺失 / 报告缺 facts 任一 commit sha → 非零退出、锚不动；
      观测值只读 facts、禁网络；degraded 源锚逐字保留 [spec-review-amendment]）（R1/R2）

## 3. 机械层测试（沙盒化，零网络零全局影响）

- [x] 3.1 anchors 语义测试：首轮初始化（per-source：gstack 天然锚真 delta / 其余当前态基线
      [spec-review-amendment]）/ yq 失败硬停 / 值缺失无锚（tmp_path + 假 HOME）（R1）
- [x] 3.2 advance 门测试：报告缺失拒推锚（内容不变 + 非零退出）/ 报告缺 facts sha 拒推锚
      [spec-review-amendment] / 报告在场正常推进 + `last_run` 更新 / degraded 源锚逐字不变
      [spec-review-amendment]（R1）
- [x] 3.3 采集器降级矩阵测试：单源不可达其余照采（git 命令 stub 注入）/ 单源挂起超时其余照采
      [spec-review-amendment] / 本地锚源缺失 / 元数据格式漂移 fail-loud 不给错锚 /
      多 scope 版本取值 [spec-review-amendment] / 锚非祖先 degraded [spec-review-amendment] /
      缓存损坏自愈一次 [spec-review-amendment]（R2）
- [x] 3.4 schema drift 测试：changed/added/removed 三类各一例 + 上游目录缺失降级（R3）
- [x] 3.4b [spec-review-amendment] superpowers 字段追踪测试：构造 bare 仓含 marketplace.json
      两次 source.sha 变更 → facts 出变化序列；R5 不改池契约测试：沙盒跑 collect+advance 后
      断言 `openspec/issues/` 树内容不变；R7 守卫测试：非本仓 cwd 拒绝且零写入（R2/R5/R7）
- [x] 3.5 测试覆盖图（TG-18，code path → 测试类型）落 tasks 附录或测试文件 docstring：

      | code path | 测试类型 |
      |---|---|
      | anchors 读写/首轮 per-source/坏文件 | 契约单测（tmp_path） |
      | advance 报告+facts 绑定门（含 sha ⊇ 校验、degraded 锚不动） | 契约单测（定点删报告/删 sha 必红）[spec-review-amendment] |
      | 四采集器 ok/degraded 分支（含挂起超时、非祖先、缓存自愈） | 单测 + stub 注入（无网络）[spec-review-amendment] |
      | superpowers marketplace.json 字段追踪 | 单测（构造 bare 仓）[spec-review-amendment] |
      | schema digest 对比 | 单测（构造双目录） |
      | facts JSON 形状 | 快照断言 |
      | R5 不改池不变量 | 契约单测（issues 树前后快照 diff）[spec-review-amendment] |
      | R7 cwd 守卫 | 契约单测（非本仓 cwd 拒绝零写入）[spec-review-amendment] |
      | upgrade 提醒行 | SKILL 指令层（无脚本，人工验收 6.3） |

## 4. SKILL 编排层

- [x] 4.1 SKILL.md 编排正文：collect → 模型读 facts 写报告（`reports/<UTC时间戳>.md` 不覆盖
      既有报告 [spec-review-amendment]；按源分节 + 三分诊〔证据不足标「观望/待核查」不硬判，
      可对候选 commit `git show` 取内容 [spec-review-amendment]〕+ 每源采集状态行 + degraded 节
      「原因 + 上游 URL」不罢工〔格式漂移分支指本地文件与键路径 [spec-review-amendment]〕+
      吸收候选附预生成 recorder add 命令含 source_change [spec-review-amendment]）→
      advance（报告+facts 双参数）→ 呈报人；关键错误/提醒文案确切原文定稿进脚本 docstring
      [spec-review-amendment]（R4）
- [x] 4.2 首轮 seed 条款：报告 SHALL 含 T245/T246/T267 分诊条目；T245/T246 注明共享
      「解除 D8 mid 档钉死」前置人工决定（R4）
- [x] 4.3 入池衔接条款：人拍板「吸」→ recorder `add` 显式 `source_change`（报告内预生成命令
      模板，替代纯 prose 约束 [spec-review-amendment]）；watch MUST NOT 直接改池；
      frontmatter description 触发词收敛（避免与 sdflow-upgrade/issues/**maintain**〔其
      description 已含「上游」字样 [spec-review-amendment]〕误触发）+ description 声明单仓专用
      [spec-review-amendment]（R5/R7）

## 5. 消费端与安装面

- [x] 5.1 `sdflow-upgrade/SKILL.md` 追加第 5 步提醒段：读
      `~/.skills/sdflow-skills/openspec/upstream/anchors.yaml` 的 `last_run` + 阈值比较，
      缺失/不可解析静默跳过，零网络（R6）
- [x] 5.2 README「Skills 列表」加 `sdflow-upstream-watch` 行（显式注明单仓专用，非通用铺设类
      [spec-review-amendment]）；开发 checkout 跑
      `bash setup.sh` 验证新链建立 + `--check` 门绿（R1 载体安装面）

## 6. 首轮真实运行 + 收口

- [x] 6.1 dogfood 首轮 `/sdflow-upstream-watch`：真跑 collect（四源真实网络）→ 报告落
      `openspec/upstream/reports/` → advance 建锚；gstack 节应含真 delta
      （`960c3a8..94993f7` 区间非空为预期基线）（R1/R2/R4 验收）
- [x] 6.2 T264 → DONE（recorder set-status，evidence 指 schema drift 采集器实现 + 测试）；
      确认 T245/T246/T267 在首轮报告 seed 节在场后保持池内原状（R3/R4 收口）
- [x] 6.3 全仓 `/usr/bin/python3 -m pytest` 绿 + 手工验收 upgrade 提醒两分支
      （超阈值提醒行 / 无锚静默）+ roadmap 阶段 3 里程碑回填草稿（hand-off 惯例）（R6 验收）
