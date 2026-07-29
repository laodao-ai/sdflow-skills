# Task 4 双轴审

## 首轮

Standards 与 Spec 均发现同一承重缺口：workflow 调用 `issues.py reindex`，没有进入 `sweep`
里的四个文本子进程调用点，因此实际只覆盖 3/7，原覆盖声明不成立。

## Fix 1 与复审

fix commit `b08a28a` 把 GBK CI 步骤改为受控真实 `issues.py sweep` 行为测试。测试先生成临时
bug fixture，再执行真实 sweep，并断言调用序列 `scan → triage → scan → batch-add → reindex`
以及每次 UTF-8/replacement 参数；四个 issues 调用点加 retro 的 1 个与 ship_gate 的 2 个文本路径，
合计满足 7。双轴复审均 PASS。

## 结论

PASS。Task 4 可补打完成信号。真实 CP936 console/redirect 行为仍由 Windows CI 承重，本机只验证
workflow 结构与可执行的 GBK 聚焦测试，未假称远端 job 已跑。
