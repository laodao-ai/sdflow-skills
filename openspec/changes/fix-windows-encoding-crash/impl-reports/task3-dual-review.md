# Task 3 双轴审

## 首轮

- Standards：PASS（Python 工具栈领域清单未覆盖，未假称覆盖）。
- Spec：Important——另有两个生产调用已声明 UTF-8 但缺 `errors="replace"`，旧 13-site
  allowlist 同时漏掉它们。

## Fix 1 与复审

fix commit `16adc55` 补齐两处替换容错，并把契约测试改为动态发现所有非测试、非生成镜像的
生产 Python 文件。复审实测共 15 个直接 `subprocess.run(text=True)` 站点全部具备
`encoding="utf-8", errors="replace"`；canonical bundle 源仍在扫描范围，`openspec/` 只排除
托管/生成副本。Standards 与 Spec 均 PASS。

## 结论

PASS。Task 3 可补打完成信号。全量 pytest 的两项 Windows 收集期既有阻断未被计作本票通过证据；
本票聚焦契约测试通过。
