## MODIFIED Requirements

### Requirement: 入口脚本 SHALL NOT 因 stdout/stderr 编码崩溃

本仓所有含 `if __name__ == "__main__":` 的 Python 入口脚本（`hack/**`、`sdflow-*/scripts/**`、`sdflow-init/assets/{hack,hooks,workflow/tools}/**`，不含 `**/tests/**`）SHALL 在 stdout/stderr 编码无法承载其输出字符时优雅降级（字符替换），而非抛出未捕获异常终止进程。

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

#### Scenario: bundle 源文件不再需要镜像排除豁免

- **WHEN** `sdflow-init/assets/workflow/tools/` 下的某源文件缺前导
- **THEN** `check_encoding_hygiene.py` SHALL 直接检出该文件；该门 SHALL NOT 保留任何针对 `openspec/workflow/tools/` 的排除分支。〔F26 定性订正〕该排除分支**在本 change 前就已不可达**——`TARGET_GLOBS` 五条 pattern 全部 root-anchored，从不把 `openspec/workflow/tools/**` 纳入候选集，本 change 是顺带清掉这个**既存**死码（而非"镜像消失后才成死码"）；其原守卫用例（引用 `openspec/workflow/tools/mirror.py` 者）为**恒真锚**（分支不可达 ⇒ 用例无论如何都绿），SHALL 删除或改写为对 `TARGET_GLOBS` root-anchored 锚定性的**正向**断言——判据：定点删除该断言所守的约束，用例必须变红

#### Scenario: 全部入口脚本均满足三项契约

- **WHEN** 目标 glob 下所有入口脚本都已满足三项契约
- **THEN** `check_encoding_hygiene.py` 以退出码 0 报告通过
