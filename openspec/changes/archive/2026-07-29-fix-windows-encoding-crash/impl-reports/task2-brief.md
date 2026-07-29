### Task 2: 让全部入口脚本在受限编码下优雅输出

**Blocked-by:** 1
**R-ID:** EH-ENTRY

把机械门发现的全部入口脚本统一保护起来，使 stdout 或 stderr 无法承载符号与 emoji 时改为字符替换而不崩溃；标准流不支持重配置时保持既定的静默降级。canonical bundle 只修改源，托管镜像由正式同步流程刷新。

- [ ] 机械门发现的 28 个入口脚本全部具备顶层 stdout/stderr UTF-8 重配置与替换容错
- [ ] 标准流缺少 `reconfigure` 时不会产生新的未捕获异常
- [ ] canonical bundle 源完成修改，托管镜像通过正式 update 同步且副作用范围已核对
- [ ] 编码卫生机械门重跑后缺失集合归零

