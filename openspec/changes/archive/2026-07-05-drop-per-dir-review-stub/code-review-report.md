## code-review 报告 — drop-per-dir-review-stub

> 阶段三独立冷主审（path 2 手工实现后的兜底）。薄配置：2 对抗镜 + 1 历史镜 + code outside-voice(codex)；
> 无领域镜（纯 Python skill 脚本，不命中 domains）、无 HR-TG 跨模型（未触发）、无第 3 对抗镜（普通档）。

### 命中范围
- 栈：纯 Python skill 脚本 + pytest（无 backend·go / embedded / frontend 领域栈）
- 清单：CR base（CR-01~09，逐条以对抗镜承载）；无领域 delta
- diff base：`git merge-base main HEAD` = ecb5a4c；范围 16 文件 +446/−370（含删除）
- Step1 scope-drift/完成度：主 session 内联 + 对抗镜 B（子代理）承载 → 无 drift、无回退、完成度真实（详见下）

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
> 〔honest 降级留痕〕gstack `/review` 已安装但**未原生调用**——1852 行重流程 vs 本 change 以删除为主的小体量，
> 按比例把 scope-drift + 计划完成度审计交由主 session 内联 + 专职对抗镜 B（fresh 子代理）承担，非伪装原生。

<!-- sdflow:hr-tg v1 hit="none" evidence="纯 Python skill 脚本清理 + 一处小函数，无 gate 关键路径/嵌入式/安全敏感触发" -->

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="none" findings="4" truncated="false" -->

### Findings（置信 ≥80）

| # | 严重度 | 项 | 证据 | 裁决 |
|---|---|---|---|---|
| CR-F1 | Medium-High | retire 反注册对畸形 settings 不 fail-safe → 崩 init/update | `init.py:_deregister_hook_in_settings`（原 `(h or {}).get`）：hooks 列表混非 dict 元素 → AttributeError；command 非 str → TypeError；外层 try 只接 OSError/shutil.Error，异常冒穿终止整个 init/update，违 docstring「结构异常 fail-safe」承诺 | ✅ **已修 [impl-review-fix]**：加 `_hook_command()` isinstance 守卫（非 dict/非 str → 判不匹配保留）+ 2 负例测试 `test_malformed_non_dict_hook_element`/`test_non_string_command`。对抗镜 A 有复现，codex V3 同证 |
| CR-V2 | Medium | spec/proposal 措辞 overstate——根锚"经路径 scope 导航"实为全树浏览，丢了 scoped 深链 | engine.js 初始 scope 仅取 `location.pathname`、不读 hash/query；根 `/review.html` bootstrap 到 INDEX（全树）。每目录 stub 曾靠自身 pathname 给 scoped 首屏/深链，移除后须从 INDEX/树点进 | ✅ **已修 [impl-review-fix]**（措辞诚实化）：spec delta×2 + proposal（加可接受降级 Non-Goal）+ 两 SKILL 改为"全树浏览、放弃 scoped 深链=可接受降级"。深链增强 defer→T45 |
| CR-F2 | Low | engine.js:52 注释悬引已删的两个生产者 | `sdflow-init/assets/workflow/tools/engine.js:51`「see init.py / change-review-stub.py / gen_review_stub.py」——活跃分发文件（随 copy_bundle 铺进每消费仓），Task4 sweep 漏 | ✅ **已修 [impl-review-fix]**：改「see init.py's copy_review_tool」 |
| CR-F3 | Low | tasks 3.4/proposal 声称跑 `pytest sdflow-roadmap/tests/` 全绿，但目录已删 → 不可复现 | tasks.md:28 / proposal:22 | ✅ **已修 [impl-review-fix]**（措辞订正）：改为"目录随删除消失、roadmap 纯 Markdown 无专属 pytest、跑仓级 pytest 确认无回归"。对抗镜 B + codex V4 同证 |
| CR-V1 | Medium-High | 退役 hook 自愈未接进 toolkit 标准更新路径（setup.sh/README） | retire_hooks 只在 sdflow-init init/update 跑；README 更新=git pull+setup.sh，setup.sh 不调 retire → 存量 ~/.claude/hooks/change-review-stub.py working copy 在 sdflow-init update 前仍 fire | ⏸ **defer → T44**（接线属 setup.sh 责任扩张，超本 change ADR-1 范围；见下「合并后须做」）。codex V1 |

### 已裁掉（反静默压制，可审计）
- **X1 子串匹配收紧**（codex V3 后半 / 对抗镜A 攻击面1）：`name in command` 子串匹配理论可误删把该文件名作参数的无关 hook。**裁掉**——与既有 `ensure_global_hook` 同款子串语义（非本次引入回归）、现实无 hook 以 `change-review-stub.py` 作 arg、收紧到精确路径反有 `$HOME` 展开不匹配风险。保留子串。
- **X2 历史镜「hook 48h 内加了又删」**：流程精度观察（初期加了个很快识别为冗余的 hook），非代码缺陷，不计 finding；反证及时识别清理的制度有效。
- **X3 fail-safe 半途态**（对抗镜A 攻击面5）：坏 JSON 时跳过反注册但仍删脚本 → 理论悬空态。裁掉——坏 JSON 时 Claude Code 本就加载不了该 settings（hook inert），且下次 JSON 修好后每跑必自愈，与既有 ensure_global_hook 同款。已有 `test_bad_json_settings_is_failsafe` 覆盖。
- **X4 todolist T6 陈旧提及**（对抗镜B 点5）：T6 动机仍写"两 guard"，本 change 后 Claude 侧只剩 ff0——非本 change 文件、超范围，hand-off 标注留意，不动 issue 池。

### 修复 / defer 台账
- **自动修 4 项 [impl-review-fix]**：CR-F1（代码+2测试）、CR-V2（措辞×5处）、CR-F2（注释）、CR-F3（措辞×2）。
- **defer 2 项 → todolist**：T44（CR-V1 部署自愈接线，P2）、T45（CR-V2 深链 hash 路由增强，P3）。
- **无 ≥2 方案需 T10 复核**（fixes 均单一确定修法）。
- **voice 分桶**：codex 采纳 3（CR-F1/CR-F3 印证 + CR-V2 直接采纳）/ 裁掉 1（X1 子串收紧）/ defer 2（CR-V1→T44、CR-V2 增强→T45）· fallback 0（codex 成功，未回落）。
- 回归：仓级 364 pytest 全绿（+2 负例锁 CR-F1）；`openspec validate` 通过。

### 合并后须做（CR-V1 缓解，写进 hand-off）
> 本仓（dogfood 消费者）合并本 change 后须先跑一次 `sdflow-init update`（或 `init`）触发 retire_hooks 自愈，
> 清掉本机 `~/.claude/hooks/change-review-stub.py` + settings 注册，否则该 working copy 仍会在新建 change 时产每目录 stub。

### 结论
- ☑ 建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）
- ☑ defer 残差已入 todolist（T44/T45，hand-off 会引用）

<!-- ship-gate: code-review=pass -->
