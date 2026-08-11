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

- [ ] gstack 采集器在有 checkout 时产出正确 delta（含首轮天然锚逻辑），checkout 缺失时 degraded
- [ ] bare 缓存采集器正确处理 matt（log --name-only）和 superpowers（marketplace.json source.sha 字段追踪）
- [ ] bare 缓存 fetch 失败自愈一次、再失败 degraded
- [ ] is-ancestor 守卫对三个 git 源生效，非祖先时 degraded
- [ ] openspec 采集器版本对照 + schema drift 清单（changed/added/removed）正确
- [ ] 元数据键路径断言失败→格式漂移 degraded（不给错锚）；多 scope 取值正确
- [ ] facts JSON 形状正确落盘 + .gitignore 生效
- [ ] advance 门：报告缺失拒推/缺 sha 拒推/正常推进 + last_run 更新/degraded 锚不动
- [ ] 单源失败不传染（四源降级矩阵测试绿）
- [ ] R5 不变量：collect+advance 后 issues 树无变化
- [ ] 上述全部路径有对应 pytest 测试绿

