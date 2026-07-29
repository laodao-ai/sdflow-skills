---
impl-pipeline: tickets
---

## Global Constraints

- 消除全部 **28** 个入口脚本在 GBK 环境下因打印 Unicode 字符触发的崩溃。
- 补全 `subprocess text=True`（**15 个调用站点 / 14 个编辑点**）的显式编码，避免解码崩溃；`write_text()` 经复核**当前已全部带 `encoding="utf-8"`（0 处待补）**，本 change 只做核实确认并写进 spec 防回退。
- 新增机械门防止后续新脚本遗漏防护（面治而非点补）。
- 在真实 Windows CI（`windows-latest` + `PYTHONIOENCODING=gbk` 真实子进程）上验证，而非仅靠此前的 mac 模拟。
- 每个 skill 是独立分发目录，被 symlink/复制安装到消费者的 `~/.claude/skills/`，脚本之间**不能共享公共 Python 模块**。
- `openspec/workflow/tools/*.py` 是 `sdflow-init/assets/workflow/tools/*.py` 的托管镜像，只能改源。
- 🔴 **① 「前几行」这个窗口取消，改为全文匹配。**
- 🔴 **② 排除规则 MUST 锚定仓根，MUST NOT 用任意深度通配。**
- **三项契约**：对每个入口脚本**分别**验证 ① `sys.stdout` 的 `reconfigure` 调用在场、② `sys.stderr` 的 `reconfigure` 调用在场、③ `errors="replace"` 在场。缺任一项 ⇒ 报告该文件 + 缺的是哪一项。
- **失败输出契约**：本门失败时 MUST 与三道同侪门同构，给出 `修：` 行——逐文件列出「路径 + 缺哪一项契约」，并附 4 行模板的规范位置指针。
- `check_encoding_hygiene.py` 只有裸调用模式（无 `--apply`）。
- **这是有意为之**（放进 `__main__` 守卫内则被当库 import 的路径不受保护，而 lib 模块正是靠调用方的进程级 reconfigure 覆盖）。
- 本 change MUST 在 `CLAUDE.md` 的「修改本仓库的注意」段补一条（新增入口脚本须带 4 行前导，否则第五道机械门会拦），并由该门的失败输出指向它。

### Task 1: 建立编码卫生机械门

**Blocked-by:** none
**R-ID:** EH-GATE

交付一个独立、只读的编码卫生检查器，能完整发现目标入口脚本缺失 stdout、stderr 或替换容错契约的情况，并以仓根锚定的排除规则避免漏检 canonical bundle 源。检查器自身也必须满足被检查契约，且其正向、各类负向、长前导和镜像同尾路径边界均有常驻回归测试。

- [x] 检查器按整文件分别核验 stdout、stderr、`errors="replace"` 三项契约
- [x] 排除规则只排除测试与仓根下的托管镜像，不连坐 canonical bundle 源
- [x] 失败输出逐文件指出缺项并提供 `修：` 指针
- [x] 常驻测试覆盖完整前导、完全缺失、只缺 stderr、只缺替换策略、canonical 源漏前导和第 190 行后前导
- [x] 初次运行得到真实缺失集合，并核对为 28 个入口脚本

### Task 2: 让全部入口脚本在受限编码下优雅输出

**Blocked-by:** 1
**R-ID:** EH-ENTRY

把机械门发现的全部入口脚本统一保护起来，使 stdout 或 stderr 无法承载符号与 emoji 时改为字符替换而不崩溃；标准流不支持重配置时保持既定的静默降级。canonical bundle 只修改源，托管镜像由正式同步流程刷新。

- [x] 机械门发现的 28 个入口脚本全部具备顶层 stdout/stderr UTF-8 重配置与替换容错
- [x] 标准流缺少 `reconfigure` 时不会产生新的未捕获异常
- [x] canonical bundle 源完成修改，托管镜像通过正式 update 同步且副作用范围已核对
- [x] 编码卫生机械门重跑后缺失集合归零

### Task 3: 固化子进程文本解码与文件写入编码契约

**Blocked-by:** 1
**R-ID:** EH-IO

让所有文本模式子进程读取显式使用 UTF-8 和替换容错，同时保留原始字节判定路径的保真语义；对文件写入面用能识别多行调用的方式证明所有站点已显式使用 UTF-8，不制造无须改动的 diff。

- [x] 15 个文本模式子进程站点通过 14 个正确编辑点获得显式 UTF-8 与替换容错
- [x] git 保真比较仍走原始字节路径，函数封装处的两个调用点没有被错误加参
- [x] 所有新加替换容错的站点均完成判定路径过目且无未记录的假等值风险
- [x] 多行感知核验确认所有文件写入站点已显式使用 UTF-8，并把验证方式写入决策证据

### Task 4: 接通交付、文档与真实 Windows 验证

**Blocked-by:** 2,3
**R-ID:** EH-ENTRY, EH-GATE, EH-IO

把新机械门作为独立守卫接入安装流程，给后续贡献者提供永久模板，并让 Windows CI 同时覆盖强制 GBK、真实 code page、控制台与重定向、初始化流程及实际子进程解码路径；完成非阻塞存量问题登记。

- [x] 安装流程独立运行第五道门，失败输出符合契约，完整安装输出不含编码异常或 traceback
- [x] 活文档包含入口脚本前导模板与第五道门说明
- [x] Windows CI 的触发路径覆盖全部受影响脚本目录，新增步骤均显式使用 bash
- [x] Windows CI 覆盖强制 GBK 的安装与初始化、至少 7 个文本子进程站点及非法字节替换行为
- [x] Windows CI 在不设置 `PYTHONIOENCODING` 时覆盖 cp936 控制台与重定向管道
- [x] 存量 `python3` 探测写法不一致已登记为本 change 关联 todo

### Task 5: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4
**R-ID:** all

按聚合套件发现契约运行本 change 的单元、集成与 e2e 测试套件并全部通过，证据落入本票 impl-report；每个覆盖层记录命令原文、退出码与同一个最终提交 SHA，仓内确无对应测试层时记录「未覆盖」及判定依据。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」及判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」及判定依据）
