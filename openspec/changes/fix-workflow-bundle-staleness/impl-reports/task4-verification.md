# Task 4: 实现验证（收尾）

## 聚合套件证据

| 层 | 命令原文 | 退出码 | SHA |
|---|---|---|---|
| unit | `/usr/bin/python3 -m pytest -W error -x -q` | 0 | 5feb0b15ad0478876dbc37cc40976b598cd95a7a |
| integration | — | 未覆盖 | 本仓无集成测试层（纯 skill 仓，无 API/DB） |
| e2e | — | 未覆盖 | 本仓无 e2e 层（skill 仓无运行时端到端场景） |

## 收尾门序列

1. `sync_principles --check` ✅ 28 个投放面一致
2. `gen_workflow_guide --check` ✅ GUIDE 与单一源一致
3. `init.py update --root .` ✅ INDEX/GUIDE 镜像刷新（过程中发现 _marker_schema bug 并修复）
4. 全仓 pytest 2649 passed, 10 skipped, 0 failed ✅

## Success Metrics 复扫

- C4（/review 残留）：0 命中 ✅
- C8（号段漂移 TG/BASE/CR）：0 命中 ✅

## 三处矛盾对读

- P3c：README:18 ↔ quality-layering §五 口径一致 ✅
- G2：spec-review:72 ↔ workflow.md G2 口径一致 ✅
- index-section /clear ↔ workflow.md:134 口径一致 ✅

## 附带修复

- `sdflow-init/scripts/init.py` `_marker_schema()` 放宽 .openspec.yaml 键校验（openspec CLI 会写 created/skip_specs 等额外字段，旧校验只允许 schema 一个键导致 update fail）
