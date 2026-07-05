## Why

`drop-per-dir-review-stub`（已归档）合并时 defer 了两项 code-review 残差，构成批次 `drop-per-dir-review-stub` 的收尾：
- **CR-V1 → T44（P2）**：退役 hook 自愈 `retire_hooks()` 只挂在 `sdflow-init init/update`（消费项目铺设路径）；而装了工具链的机器另有一条更新路径 `git pull + setup.sh`（`/sdflow-upgrade`，升级工具链本身），**不调 retire**。升级后到下一次某项目跑 `sdflow-init update` 之前，存量 `~/.claude/hooks/change-review-stub.py` 仍会 fire——自愈没兜到最上游、必跑、早于一切 `sdflow-init` 的路径。
- **CR-V2 → T45（P3）**：`drop-per-dir-review-stub` 砍掉每目录 stub 后，根锚 `review.html` 的初始 scope 仅取 `location.pathname`、不读 hash，丢了「直接打开某 change 的 scoped 首屏/深链」（当时以「可接受降级」记录在案）。本次补齐该增强。

两项性质无耦合（后端部署自愈 / 前端深链），但同属该批次收尾、同围绕 review 工具生态，合并为一个 cleanup change 交付内聚。

## What Changes

- **T44（P2，基础设施）**：给 `sdflow-init/scripts/init.py` 增一个**独立子命令**（如 `retire-hooks` mode），只调既有 `retire_hooks()`、不碰 `openspec/`、不需要 `--root` 有 bundle（retire 只动 `~/.claude` 全局）；`setup.sh` 在 canonical/hack 刷新后调用它一次，把退役 hook 自愈**焊进工具链升级路径**。README/文档同步一句。
  - 复用现有 `retire_hooks()` 逻辑，**零重写**；两条更新路径（`init/update` 与 `setup.sh`）共用同一自愈。
  - **边界**：`setup.sh` 兜的是「装了 sdflow-skills 的机器」；纯消费机（无 `setup.sh`）仍靠 `sdflow-init init/update`（现状不变）。
- **T45（P3，功能增强）**：`sdflow-init/assets/workflow/tools/engine.js` 启动时若 `location.hash` 匹配 `#/changes/X/`（及 `#/roadmaps/X/`），以其作为 initialDir，恢复 `/review.html#/changes/X/` 的 scoped 首屏/深链；复用既有 hash-based navigate 机制，增量最小。

无 **BREAKING**：两项均为增量补齐，不改现有 `retire_hooks()` 行为、不回退根锚全树浏览能力。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`: ① retire hook 自愈的**触发路径**从「仅 `sdflow-init init/update`」扩到「亦经工具链升级路径 `setup.sh`」；② review UI 根锚从「仅 `location.pathname` 起 scope、放弃 scoped 深链（可接受降级）」升级为「亦读 `#/changes|roadmaps/X/` hash → scoped 首屏」，兑现原 delta 标注的后续增强。

## Impact

- **代码**：`sdflow-init/scripts/init.py`（+retire 子命令 CLI 路由）、`setup.sh`（+一步调用，含 `IS_WINDOWS` 分支下 `python3` 可用性兜底）、`sdflow-init/assets/workflow/tools/engine.js`（+hash → initialDir 解析）。
- **测试**：`sdflow-init/tests/`（retire 子命令 CLI 层 TDD，复用现有 retire_hooks 测试骨架）；engine.js 无 pytest 覆盖 → T45 验证走手测 / `embedded-test-sop`（tasks 标注）。
- **文档**：README 记 setup.sh 现也触发退役 hook 自愈。
- **部署**：改 `assets/workflow/tools/engine.js` 与 `assets/hack/`/`setup.sh` 后须在开发 checkout 重跑一次 `setup.sh` 才测得到（dev/runtime checkout 纪律）。
- **需求优先级**〔TG-19〕：T44 = **P2**（部署一致性，避免存量机遗留失败 hook）、T45 = **P3**（便利增强，浏览能力已不回退）。
- **合规声明**：无信任边界 / 敏感数据新增（retire 仅外科式摘 `~/.claude/settings.json` 既有注册，既有逻辑已 fail-safe）；不适用性能 NFR / 计费服务条款。

## Open Questions〔TG-21〕

- `setup.sh` 的 Windows 分支（`IS_WINDOWS=1`）下 `python3` 是否稳定可用？若不可用，retire 步应 **fail-safe 跳过 + 提示**（不阻断 setup），非硬失败——设计期确定降级策略。
