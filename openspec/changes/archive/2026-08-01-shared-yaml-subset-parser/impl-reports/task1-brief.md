### Task 1: setup.sh 依赖预检系统

**Blocked-by:** none
**R-ID:** R1, R2

`setup.sh` 新增 `check_dependencies()` 函数，在 `install_sdflow` 之后、门禁检查之前统一检测并报告全部运行依赖（python3 ≥ 3.7 / git / yq / openspec / pytest）。既有 python3 检测逻辑迁入此函数。yq 检测含 mikefarah vs kislyuk 区分（`--version` 输出含 `mikefarah`）。缺失时按平台输出安装指引（brew/winget/snap）。不中止 setup.sh（降级汇报）。

- [ ] `setup.sh` 运行后输出每项依赖一行状态（✓/✗/·）
- [ ] yq 已安装但为 kislyuk/yq 时输出警告 + 正确版本安装指引
- [ ] yq 未安装时输出 ✗ + 三平台安装命令
- [ ] 必要依赖缺失时在末尾汇总安装指引，但不中止 setup.sh
- [ ] 既有 python3 检测逻辑已从原位迁入 `check_dependencies()`，不重复

