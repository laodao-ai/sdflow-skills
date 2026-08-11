# Tasks · implement-workflow-optimization-2026-08-p3

> Requirement ID 对照（specs/upstream-watch/spec.md）：
> **R1** 锚文件独占维护 + 锚推进绑定报告 · **R2** 四源采集降级不传染 ·
> **R3** schema fork drift 对比 · **R4** 分诊报告 · **R5** 入池衔接 · **R6** upgrade 陈旧提醒

## 1. 脚手架

- [ ] 1.1 建 `sdflow-upstream-watch/` 目录骨架：SKILL.md（frontmatter + 编排指令占位）、
      `scripts/upstream_watch.py`（4 行 reconfigure 前导 + `collect`/`advance` 子命令骨架）、
      `tests/` 空壳；跑 `python3 hack/sync_principles.py --apply` 注入通则托管块并确认
      自报投放面计数 +1（R1–R5 载体）
- [ ] 1.2 建 `openspec/upstream/` 数据目录约定（anchors.yaml 由脚本首轮创建，目录进 git；
      `reports/` 留 `.gitkeep` 或首份报告时建）（R1）

## 2. 机械层（scripts/upstream_watch.py）

- [ ] 2.1 anchors.yaml 读写（yq，三态错误语义：缺失=首轮初始化 / yq 失败=fail-loud 硬停 /
      值缺失=该源无锚）+ schema_version 与 `remind_after_days` 字段（R1）
- [ ] 2.2 gstack 采集器：既有 checkout `git fetch origin` + `log --name-only 锚..FETCH_HEAD`；
      checkout 缺失 → degraded（R2）
- [ ] 2.3 bare 缓存采集器（matt / superpowers 共用）：`clone --filter=blob:none --bare` 到
      `~/.cache/sdflow-upstream/`（已存在则 fetch）+ `log --name-only 锚..HEAD`；
      superpowers 限定插件子路径过滤；上游不可达 → degraded（R2）
- [ ] 2.4 openspec 采集器：`openspec --version` vs `npm view` 版本对照 + schema fork 双侧
      逐文件 sha256 对比（changed/added/removed 清单，零解析）；上游目录定位失败 →
      该子项 degraded（R2/R3）
- [ ] 2.5 本地元数据键路径断言（`installed_plugins.json` superpowers 条目 /
      `.skill-lock.json`）：断言失败 → 显式格式漂移 degraded，MUST NOT 静默给错锚（R2）
- [ ] 2.6 facts JSON 输出（per-source status/reason/commits/changed_paths/drift 清单，
      落 scratch）+ `advance` 前置校验（本轮报告文件不存在 → 非零退出、锚不动）（R1/R2）

## 3. 机械层测试（沙盒化，零网络零全局影响）

- [ ] 3.1 anchors 语义测试：首轮初始化 / yq 失败硬停 / 值缺失无锚（tmp_path + 假 HOME）（R1）
- [ ] 3.2 advance 门测试：报告缺失拒推锚（内容不变 + 非零退出）/ 报告在场正常推进 +
      `last_run` 更新（R1）
- [ ] 3.3 采集器降级矩阵测试：单源不可达其余照采（git 命令 stub 注入）/ 本地锚源缺失 /
      元数据格式漂移 fail-loud 不给错锚（R2）
- [ ] 3.4 schema drift 测试：changed/added/removed 三类各一例 + 上游目录缺失降级（R3）
- [ ] 3.5 测试覆盖图（TG-18，code path → 测试类型）落 tasks 附录或测试文件 docstring：

      | code path | 测试类型 |
      |---|---|
      | anchors 读写/首轮/坏文件 | 契约单测（tmp_path） |
      | advance 报告绑定门 | 契约单测（定点删报告必红） |
      | 四采集器 ok/degraded 分支 | 单测 + stub 注入（无网络） |
      | schema digest 对比 | 单测（构造双目录） |
      | facts JSON 形状 | 快照断言 |
      | upgrade 提醒行 | SKILL 指令层（无脚本，人工验收 6.3） |

## 4. SKILL 编排层

- [ ] 4.1 SKILL.md 编排正文：collect → 模型读 facts 写报告（按源分节 + 三分诊 + 每源采集
      状态行 + degraded 节「原因 + 上游 URL」不罢工）→ advance → 呈报人（R4）
- [ ] 4.2 首轮 seed 条款：报告 SHALL 含 T245/T246/T267 分诊条目；T245/T246 注明共享
      「解除 D8 mid 档钉死」前置人工决定（R4）
- [ ] 4.3 入池衔接条款：人拍板「吸」→ recorder `add` 显式 `source_change`；watch MUST NOT
      直接改池；frontmatter description 触发词收敛（避免与 sdflow-upgrade/issues 误触发）（R5）

## 5. 消费端与安装面

- [ ] 5.1 `sdflow-upgrade/SKILL.md` 追加第 5 步提醒段：读
      `~/.skills/sdflow-skills/openspec/upstream/anchors.yaml` 的 `last_run` + 阈值比较，
      缺失/不可解析静默跳过，零网络（R6）
- [ ] 5.2 README「Skills 列表」加 `sdflow-upstream-watch` 行；开发 checkout 跑
      `bash setup.sh` 验证新链建立 + `--check` 门绿（R1 载体安装面）

## 6. 首轮真实运行 + 收口

- [ ] 6.1 dogfood 首轮 `/sdflow-upstream-watch`：真跑 collect（四源真实网络）→ 报告落
      `openspec/upstream/reports/` → advance 建锚；gstack 节应含真 delta
      （`960c3a8..94993f7` 区间非空为预期基线）（R1/R2/R4 验收）
- [ ] 6.2 T264 → DONE（recorder set-status，evidence 指 schema drift 采集器实现 + 测试）；
      确认 T245/T246/T267 在首轮报告 seed 节在场后保持池内原状（R3/R4 收口）
- [ ] 6.3 全仓 `/usr/bin/python3 -m pytest` 绿 + 手工验收 upgrade 提醒两分支
      （超阈值提醒行 / 无锚静默）+ roadmap 阶段 3 里程碑回填草稿（hand-off 惯例）（R6 验收）
