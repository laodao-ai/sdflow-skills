### Task 4: 接通交付、文档与真实 Windows 验证

**Blocked-by:** 2,3
**R-ID:** EH-ENTRY, EH-GATE, EH-IO

把新机械门作为独立守卫接入安装流程，给后续贡献者提供永久模板，并让 Windows CI 同时覆盖强制 GBK、真实 code page、控制台与重定向、初始化流程及实际子进程解码路径；完成非阻塞存量问题登记。

- [ ] 安装流程独立运行第五道门，失败输出符合契约，完整安装输出不含编码异常或 traceback
- [ ] 活文档包含入口脚本前导模板与第五道门说明
- [ ] Windows CI 的触发路径覆盖全部受影响脚本目录，新增步骤均显式使用 bash
- [ ] Windows CI 覆盖强制 GBK 的安装与初始化、至少 7 个文本子进程站点及非法字节替换行为
- [ ] Windows CI 在不设置 `PYTHONIOENCODING` 时覆盖 cp936 控制台与重定向管道
- [ ] 存量 `python3` 探测写法不一致已登记为本 change 关联 todo

