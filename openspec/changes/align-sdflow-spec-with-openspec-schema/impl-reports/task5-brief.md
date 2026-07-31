### Task 5: 建立回归测试与安装刷新门

**Blocked-by:** 2, 3
**R-ID:** SA-05, SA-17, SW-SCHEMA

版本门、迁移顺序、整删重拷、schema 内容契约、配置窄 patch 与相位 C 载荷契约均有反恒真回归覆盖；权威 bundle 变更后完成一次安装刷新并通过全仓测试。

- [ ] 版本门覆盖 `<1.7.0`、`1.10.0`、命令缺失和非数字输出
- [ ] 迁移覆盖缺绑定补写、已有绑定 no-op、archive/stray 跳过、单项失败阻止 config 切换
- [ ] copy bundle 覆盖权威源删除文件后的孤儿清理
- [ ] schema 内容覆盖 id/generates、委派标记和两条 requires 边
- [ ] update 模式 schema 单键改写覆盖且其余 config 内容 byte-identical
- [ ] 每条新增测试均先通过定点破坏验证非恒真
- [ ] 完成安装刷新后全仓 `pytest` 通过

