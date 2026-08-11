# Task 1 impl-report: 脚手架 + anchors 基础设施 + cwd 守卫

**R-ID:** R1, R7
**Ticket:** Task 1（tickets.md）
**范围声明**：本票只建立骨架 + 机械层基础设施（cwd 守卫 + anchors.yaml 三态读写层）。
四源采集逻辑、facts JSON、`advance` 报告+facts 绑定门属 Task 2；SKILL 编排正文与
`sdflow-upgrade` 消费端属 Task 3——均未在本票实现，SKILL.md 与脚本 docstring 已如实
标注「脚手架阶段」。

## 做了什么

1. **目录骨架**
   - `sdflow-upstream-watch/SKILL.md`：frontmatter（`name`/`description`，description 已
     标注「脚手架阶段」防止提前误触发）+ 通则托管块 + 状态说明（本阶段范围/未实现清单）。
   - `sdflow-upstream-watch/scripts/upstream_watch.py`：4 行 reconfigure 前导 + `collect`/
     `advance` 子命令骨架 + argparse 入口。
   - `sdflow-upstream-watch/tests/test_upstream_watch.py`。
   - `openspec/upstream/reports/.gitkeep`（`openspec/upstream/` 数据目录进 git）。

2. **通则托管块注入**：`python3 hack/sync_principles.py --apply` 回填
   `sdflow-upstream-watch/SKILL.md`（apply 前 `--check` 报该文件缺失/漂移，apply 后
   `--check` 报「23 个投放面全部一致」——较本次改动前 +1，符合验收条款）。

3. **cwd 守卫（proposal A4，R7）**：`guard_cwd()`——
   - 用 `git rev-parse --show-toplevel` 从调用者 cwd 解析实际仓根（不假定 cwd 就是仓根，
     支持从仓内任意子目录调用）；不在任何 git 仓库内 → `CwdGuardError`。
   - 对解析出的仓根跑 `git remote get-url origin`，非零退出或不含
     `laodao-ai/sdflow-skills` 子串 → `CwdGuardError`。
   - `cmd_collect`/`cmd_advance` 起手即调用 `guard_cwd()`，`main()` 捕获
     `CwdGuardError` 打印 `fail-loud: ...` 到 stderr 后 `return 1`，守卫失败路径不触碰
     任何后续写入代码。

4. **anchors.yaml 三态读写层（R1 / TD4）**：
   - `_resolve_yq()`：mikefarah-flavor 探测 idiom（`shutil.which` → `yq --version` 输出含
     `mikefarah` 才接受），同 `sdflow-retro/scripts/retro_report.py::_yq` 各自实现、不跨
     目录 import。未安装 / 非 mikefarah 家族 → `AnchorsError` 并附安装指引。
     **与 retro_report 的差异**：不做进程内缓存（本工具每轮调用个位数次，缓存收益可忽略，
     无缓存换来测试可独立控制每次探测结果，docstring 已记此权衡）。
   - `load_anchors(path)`：文件缺失 → 返回默认骨架（`schema_version=1`、`last_run=None`、
     `remind_after_days=30`、`sources={}`，首轮初始化语义，不触发 yq）；文件存在但 yq 解析
     失败 → `AnchorsError` fail-loud 硬停；文件存在且可解析 → 返回结构化 dict。
   - `get_source_anchor(anchors, source)`：某源字段缺失/为空 → `None`（"值缺失=该源视为
     无锚"）。
   - `write_anchors(path, anchors)`：整份覆盖写，走 `yq -o=yaml -P '.' -`（JSON 是合法
     YAML 1.2 子集，mikefarah yq 直接把它当输入重新格式化输出，零手写 YAML 序列化字符串，
     基准 5 合规）。

5. **超时常量**：`SUBPROCESS_TIMEOUT_SECONDS = 60` 单点定义，`_run()` 唯一子进程入口
   统一消费（`guard_cwd`/`_resolve_yq`/`_yq_read`/`write_anchors` 均经此函数，无第二处
   裸 `subprocess.run`）。

## 测试

`sdflow-upstream-watch/tests/test_upstream_watch.py`，19 个用例，全部沙盒化
（`tmp_path` + `monkeypatch.chdir`/`monkeypatch.setattr`，零网络零全局影响）：

- cwd 守卫：非 git 仓 / 错误 remote / 无 remote 三种拒绝 + 匹配 remote 接受（含从子目录
  调用）+ CLI 层零写入验收（`collect`/`advance` 在非本仓/错误 remote cwd 下非零退出、
  stderr 含 `fail-loud`、目录零新增条目）。
- argparse 入口：`--help` 列出两个子命令、无子命令报错、`main(["collect"])` 在匹配仓内
  正确越过守卫（返回码 2 = 阶段占位而非守卫失败的 1）。
- 超时常量单点定义。
- anchors 三态：缺失文件返回初始化骨架 + 任意源 `get_source_anchor` 为 `None`；
  语法坏的 YAML（真 yq 解析失败）fail-loud；有效文件里某源字段缺失视为无锚；yq 未安装
  fail-loud；伪造非 mikefarah 版本字符串的假 yq 二进制触发 mikefarah 检测报错。
- `write_anchors` + `load_anchors` round-trip；`write_anchors` 产出人类可读 YAML
  （非裸 JSON 字面量，佐证走 yq 转换）。

```
$ /usr/bin/python3 -m pytest sdflow-upstream-watch/tests/ -q
...................
19 passed
```

**TDD 验证过程中发现并修复一处 tautological 测试 bug**：`test_yq_non_mikefarah_flavor_
rejected` 最初用 `match="mikefarah"` 断言异常消息——mutation 测试（临时禁用 mikefarah
检测分支）后仍显示 PASSED，排查发现 pytest 生成的 `tmp_path` 目录名基于测试函数名截断
（`test_yq_non_mikefarah_flavor_r0`），恰好包含 `mikefarah` 子串，与 fallback 异常消息
（`"yq failed on <该路径>: "`）中的路径部分巧合匹配，造成假绿。改为匹配脚本源码里的确切
错误短语 `"检测到的 yq 不是 mikefarah/yq"` 后，重新跑 mutation 测试确认：mutation 态红、
恢复态绿。

其余关键路径也逐一做了「破坏实现 → 确认对应测试红 → 恢复 → 确认绿」核验：cwd 守卫的
remote 匹配分支、`load_anchors` 缺失文件骨架分支、`write_anchors` 走 yq 而非裸
`json.dumps` 写入分支——均按预期变红。

## 全仓回归（补充自检，非本票验收范围）

`/usr/bin/python3 -m pytest -q`（全仓）在本票范围外，属 Task 5「聚合套件发现契约」的验收项
（`tickets.md` Task 5）。本票执行期启动过一次全仓自检运行作补充信号，但该次运行耗时超出
合理等待窗口未取得终态（本仓测试数量大、部分套件含真实子进程/git 操作，非本票新增代码
导致）；本票新增文件均为**新增**（`git status` 确认零改动既有文件），不修改任何既有脚本、
测试或共享常量/谓词，引入全仓回归的风险面为零。本票自身验收面
（`sdflow-upstream-watch/tests/`）19/19 绿且逐条 mutation 验证，已完整覆盖。

## 与 Global Constraints / design.md 的对应

- 零解析上游内容：本票未触碰任何上游内容采集（Task 2 范围），机械层目前只碰
  `anchors.yaml` 自有 YAML 与 git/yq 自身输出。
- cwd 守卫 fail-loud 不写文件：CLI 层测试直接断言目录零新增条目。
- 统一超时常量单点定义：`SUBPROCESS_TIMEOUT_SECONDS`。
- yq 三态错误语义 + mikefarah-flavor 探测：`load_anchors`/`_resolve_yq` 实现，测试覆盖。
- git 跟踪产物本机路径 tilde 记法：本票未产出任何含本机绝对路径的 git 跟踪内容
  （`anchors.yaml` 尚未被脚本写入过真实数据，仅测试用 tmp_path，不入库）。
- 4 行 reconfigure 前导：`upstream_watch.py` 顶部已加。

## 未做 / 遗留给后续 Task

- 四源采集器、facts JSON、`advance` 的报告+facts 绑定门（Task 2）。
- SKILL.md 编排正文、`sdflow-upgrade` 提醒段、README 登记（Task 3）。
- 首轮 dogfood 真实运行（Task 4）。
