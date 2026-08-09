## REMOVED Requirements

### Requirement: outside-voice 复用三判归约为单一 reason_code

**Reason**: 复用判定对象 `gstack-review.md` 随 Step1 自持化(autoplan 原生执行退役,ADR 0040)不复存在;design-voice 恒自跑(D5)后不存在「复用 vs 重开」分支,三前置(来源 mode / 新鲜度 / 结构)失去判定物。`outside_voice_guard.py` 及其测试删除(tasks 3.1)。〔spec-review-amendment:本 capability 整体退役原缺 delta,评审五声独立命中(E1/X-1/K-8/adv1-F3/adv2-F5)后补〕

**Migration**: 无承接——能力对象消失。矩阵分类逻辑(`classify_combo`)的另一份本地重实现保留在 `anchor_lint`(见 `host-adaptive-execution` 的 MODIFIED delta:跨工具 golden 随之改为 anchor_lint 单工具全笛卡尔自测)。`openspec/INDEX.md` 中本 capability 行与工具清单行同步移除(tasks 4.3)。

### Requirement: 新鲜度用源文件 fs-mtime 直比、纯 stdlib、门控外置〔spec-review Q-C·撤销 grill Q3〕

**Reason**: 同上——复用路径整体退役,新鲜度判定无消费方。

**Migration**: 无。

### Requirement: 坏输入 fail-closed

**Reason**: 同上——脚本删除,fail-closed 契约随之退役。

**Migration**: 无。
