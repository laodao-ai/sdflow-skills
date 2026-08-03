## Task 1: T164 路径引号修正 —— 实现报告

### 范围

只做 T164（路径引号）。T148（`_FANOUT_MIRRORS` 镜名扩展）不属于本票，未触碰。

### 改动

**`sdflow-code-review/SKILL.md`**（async-branch marker 409-495 内 + marker 外两处）：

| 位置 | 原模板 | 修正后 |
|---|---|---|
| L436（marker 内） | `--context-file <f>` / `> {run-dir}/<site>.rc` | `--context-file "<f>"` / `> "{run-dir}/<site>.rc"` |
| L443（marker 内） | `--run-dir {run-dir} ... --context-file <f> --repo-root <repo-root>` | `--run-dir "{run-dir}" ... --context-file "<f>" --repo-root "<repo-root>"` |
| L448（marker 内） | `cleanup --run-dir <d> ...`（`reconcile --run-dir <d>`） | `cleanup --run-dir "<d>" ...`（`reconcile --run-dir "<d>"`） |
| L452（marker 内） | `collect --run-dir {run-dir}` | `collect --run-dir "{run-dir}"` |
| L462（marker 内） | `await --run-dir {run-dir}` | `await --run-dir "{run-dir}"` |
| L465（marker 内） | `reconcile --run-dir <确切目录>` | `reconcile --run-dir "<确切目录>"` |
| L466（marker 内） | `cleanup --run-dir <d> ...` | `cleanup --run-dir "<d>" ...` |
| L467（marker 内） | `cleanup --run-dir {run-dir}` | `cleanup --run-dir "{run-dir}"` |
| L396（marker 外） | `mkdir -p {change_dir}/.outside-voice` | `mkdir -p "{change_dir}/.outside-voice"` |
| L496（marker 外，fallback 行） | `--context-file <f>` | `--context-file "<f>"` |

**`sdflow-spec-review/SKILL.md`**（async-branch marker 405-491 内做字节对称修改，
marker 外的 L392/L492 各自独立同法修改）：改动内容与 code-review 逐字相同（marker 内段落
两文件本就逐字节相同，故 diff 一致；marker 外两处独立应用同一处修法）。

`<T>`、`<site>`/`<s>` 保持不加引号（design.md 已判定：clamp 后的整数字面量 / 受控枚举，
非注入向量）。

### 附带修复（非本票 scope 扩张，属「改一个被消费的字符串必须同步消费方」）

`hack/tests/test_async_branch_parity.py` 有两处**逐字节 golden** 断言直接硬编码了旧的
未加引号命令行，是 marker 段内容的直接消费方：

- `test_codex_dispatch_command_line_is_byte_exact`：`_DISPATCH_COMMAND_LINE` 常量
- `test_codex_branch_gates_auto_fallback_on_unknown_cost`：`need` 元组里的
  `"cleanup --run-dir <d> --site <s> --cancel"` 子串

两处按新引号形态同步更新，否则加引号后这两条测试必然假红——不属于扩大范围，是让改动后
的测试套件保持真实反映现状（CLAUDE.md 通则①「动一个被多处消费的字符串前先查谁在用它」）。

grep 全仓确认无其他消费方（`sdflow-architecture/SKILL.md`、`outside-voice-job.py` 自身
usage 注释、`openspec/specs/outside-voice-background-jobs/spec.md`、archive 下的历史
change 文档等命中的都是无关模板/历史记录，未在本票改动清单内，未触碰）。

### 验证

- `python3 hack/check_async_branch_parity.py` → `✅ 2 处 async host 调度段逐字节一致`
- `python3 -m pytest hack/tests/test_async_branch_parity.py -v` → 41 passed
- 全仓 `grep -nE` 复核 marker 内外目标模式均已无未加引号残留（见 diff）
- `git diff --stat`：`hack/tests/test_async_branch_parity.py`（4 行）、
  `sdflow-code-review/SKILL.md`（20 行）、`sdflow-spec-review/SKILL.md`（20 行）

### 未做/遗留

无。5 项验收复选框对应的改动均已完成，parity 守卫通过。验收复选框本身按信号权威表由
双轴审通过后补打，本报告不勾。
