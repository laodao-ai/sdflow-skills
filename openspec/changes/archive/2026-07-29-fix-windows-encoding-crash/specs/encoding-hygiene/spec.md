## ADDED Requirements

### Requirement: 入口脚本 SHALL NOT 因 stdout/stderr 编码崩溃

本仓所有含 `if __name__ == "__main__":` 的 Python 入口脚本（`hack/**`、`sdflow-*/scripts/**`、`sdflow-init/assets/{hack,hooks,workflow/tools}/**`，不含 `**/tests/**` 与 `openspec/workflow/tools/**` 托管镜像）SHALL 在 stdout/stderr 编码无法承载其输出字符时优雅降级（字符替换），而非抛出未捕获异常终止进程。

#### Scenario: Windows(GBK) 环境下打印含常见符号/emoji 的成功消息

- **WHEN** 入口脚本在 `sys.stdout.encoding` 为 `gbk`（如中文 Windows 默认 locale cp936）的进程中执行，且其 `print()` 输出包含 `✅` `🔴` `⚠` `✓` 等 GBK 编码表之外的字符
- **THEN** 脚本正常执行完毕、按其自身判定逻辑退出（成功场景退出码 0），不因 `UnicodeEncodeError` 中止

#### Scenario: UTF-8/兼容 locale 环境下行为不变

- **WHEN** 入口脚本在 `sys.stdout.encoding` 已是 UTF-8（或其它能承载全部输出字符的编码）的进程中执行
- **THEN** 输出内容与修复前逐字节一致（`reconfigure(encoding="utf-8")` 在已是 UTF-8 时是幂等操作）

#### Scenario: 标准流已被替换为不支持 `reconfigure` 的对象

- **WHEN** 入口脚本被 import 或执行时，`sys.stdout` / `sys.stderr` 已被调用方替换为不提供 `reconfigure` 方法的对象（如 `io.StringIO`）
- **THEN** 前导块 SHALL NOT 因此抛出未捕获异常终止进程（脚本以其自身逻辑继续执行）
- **AND** 此时前导块不生效、进程回退到宿主给定的编码行为——这是**已知且被接受的静默降级**（`design.md` Risks 显式记录），SHALL NOT 被视为"已受保护"

### Requirement: 机械门 SHALL 准确报告真实一致性状态，不因编码问题产生假红

`setup.sh` 现有的四道一致性门（`sync_principles.py` / `gen_workflow_guide.py` / `check_async_branch_parity.py` / `check_tier_resolution_parity.py`）与 `sdflow-init` 的 `init.py`（init/update 模式），其对外契约——判定内容是否漂移/是否铺设成功——SHALL 与运行环境的 stdout 编码无关。

#### Scenario: 内容一致（无漂移）但运行在 GBK 环境

- **WHEN** 四条通则 / WORKFLOW-GUIDE / async host 段落 / 档位解析段落实际内容与真相源一致，脚本在 GBK 环境下运行
- **THEN** 对应机械门报告"一致"（退出码 0），不因打印成功消息时的编码异常而被误判为"有漂移"

#### Scenario: `sdflow-init` init/update 在 GBK 环境下完整执行

- **WHEN** `python3 sdflow-init/scripts/init.py update --root <project>` 在 GBK 环境下运行，且全部文件系统操作（拷贝 bundle、注入托管区块、合并 config）已成功完成
- **THEN** 脚本以退出码 0 结束并打印完成汇总，不因末尾的成功横幅打印崩溃而以非零退出码误报"铺设失败"

#### Scenario: 真有漂移且运行在 GBK 环境（反向用例）

- **WHEN** 受守护内容**确实**与真相源不一致（真漂移），脚本在 GBK 环境下运行，且其失败消息含 `🔴` `⚠️` 等 GBK 编不出的字符
- **THEN** 对应机械门 SHALL 以非零退出码报告"有漂移"，**且 SHALL 完整打印该失败消息而不因编码崩溃**
- **AND** 该门 SHALL NOT 在打印失败详情的中途中止，致使用户只看到半条 `修：` 提示

> 本 Scenario 是与"内容一致"那条对称的反面。警示符号出现在**失败**消息里的频率高于成功消息，∴ 失败路径的编码安全比成功路径**更**吃紧——只验证成功路径等于漏掉了更该验证的那一半。

### Requirement: 新增机械门守护 reconfigure 前导块的三项契约

`hack/check_encoding_hygiene.py` SHALL 对目标 glob 下每个含 `if __name__ == "__main__":` 的入口脚本，**分别**检查三项契约在场：① `sys.stdout` 的 `reconfigure` 调用 ② `sys.stderr` 的 `reconfigure` 调用 ③ `errors="replace"`。缺任一项时 SHALL 以非零退出码报告缺失清单**并指明缺的是哪一项**，且该门 SHALL 独立于其余四道门运行（任一门脚本缺失不影响本门执行）。

判据 SHALL 作用于**整个文件**，SHALL NOT 设行数窗口。排除规则 SHALL 锚定仓库根路径，SHALL NOT 使用任意深度通配。

#### Scenario: 新脚本遗漏 reconfigure 前导

- **WHEN** 仓内新增一个含 `if __name__ == "__main__":` 的入口脚本，且未调用 `reconfigure`
- **THEN** `check_encoding_hygiene.py` 以非零退出码报告该脚本路径

#### Scenario: 前导块只覆盖了 stdout（部分契约缺失）

- **WHEN** 某入口脚本只对 `sys.stdout` 调用了 `reconfigure`，未覆盖 `sys.stderr`（或缺 `errors="replace"`）
- **THEN** `check_encoding_hygiene.py` 以非零退出码报告该脚本，并指明缺失的是三项契约中的哪一项

#### Scenario: 入口脚本的 `import sys` 位置很靠后

- **WHEN** 某入口脚本因长模块 docstring 使其 `import sys` 落在第 190 行之后（如 `sdflow-ship/scripts/ship_gate.py`），且其后已正确插入完整前导块
- **THEN** `check_encoding_hygiene.py` SHALL 判定该脚本**通过**，SHALL NOT 因前导块不在文件开头而误报缺失

> 这条守的是本 change 的自反性：一个为消除假红而建的门，SHALL NOT 自己制造假红。

#### Scenario: bundle 源文件不被镜像排除规则连坐

- **WHEN** `sdflow-init/assets/workflow/tools/` 下的某源文件缺前导（该路径与被排除的镜像路径 `openspec/workflow/tools/` 共享尾段 `workflow/tools`）
- **THEN** `check_encoding_hygiene.py` SHALL 检出该文件，SHALL NOT 因排除规则匹配到尾段而将其一并排除

#### Scenario: 全部入口脚本均满足三项契约

- **WHEN** 目标 glob 下所有入口脚本都已满足三项契约
- **THEN** `check_encoding_hygiene.py` 以退出码 0 报告通过

### Requirement: subprocess 文本解码与文件写入 SHALL 显式声明 UTF-8 编码

本仓 Python 脚本中 `subprocess.run(..., text=True, ...)` 与 `Path.write_text(...)` 调用 SHALL 显式声明 `encoding="utf-8"`（`subprocess` 场景另加 `errors="replace"` 容错），不依赖进程 locale 的隐式默认编码。

#### Scenario: 读取含中文字符的 git commit message

- **WHEN** 脚本通过 `subprocess.run(["git", "log", ...], text=True)` 读取包含中文字符的 commit message，且运行环境 locale 非 UTF-8
- **THEN** 解码使用显式 `encoding="utf-8", errors="replace"`，不因 locale 默认编码解码失败而抛 `UnicodeDecodeError`

#### Scenario: 写入产出文件

- **WHEN** 脚本通过 `Path.write_text(content)` 写入产出文件，且运行环境 locale 非 UTF-8
- **THEN** 写入使用显式 `encoding="utf-8"`，产出文件为 UTF-8 编码，供后续 UTF-8 读取方正确解析
