# hand-off — add-codex-host-support

> 日期：2026-07-16 · Verify：✅ PASS（见 verify-report.md）· 收尾：/sdflow-done（Claude 宿主）

---

## 🔴🔴 最重要的一条：Codex efficacy **未验即合并**（用户 C 授权、风险自负）

**本 change 是 BREAKING 契约变更，其核心目标（Codex 宿主里真跨模型 outside voice）押在两个至今未在真实 Codex 宿主验证的假设上**：

- **A1**：`CODEX_THREAD_ID` 在 Codex 各形态（交互 / headless / `codex exec` / spawned subagent）都存在（宿主判定正信号）。
- **A3**：Codex 宿主能成功发出 `claude -p --tools "Read,Grep,Glob" --strict-mcp-config --add-dir <repo>` 网络请求并拿到 findings（反向跨模型 voice 的前提）。

**现状**：本轮收尾跑在 **Claude 宿主**（`CLAUDECODE=1`），**A1/A3 无法从 Claude 宿主验证**。tasks **0.1 / 0.2 / 0.3（效能前置门）+ 10.1（Codex 宿主端到端）确实未做**，复选框已诚实保持未勾 + 说明。proposal 假设表 A3 仍标「未在真实 Codex 沙箱内验证」。

**superpowers-plan.md 原定「实现+冷审后 STOP，不自动 done/merge，等 Codex 测过再收尾」——本次收尾是用户在被明确告知后显式授权（选项 C）"未验即合并、风险自负"而推进的，非流程默认。**

**风险方向**：失效方向"安全"（fail-loud 降级 / 同族 fallback，**不假绿**），但**若假设不成立，则 Codex 主力形态（headless/CI）下本 change 的目标 efficacy = 0**（Codex 里永远拿不到真跨模型意见）。合并不会让 Claude 宿主行为退化（10.2 回归已验、存量聚合逐行一致），但**Codex 侧的目标交付未经证实**。

**合并后 MUST 补做（把这段当欠债）**：在真实 Codex 宿主跑 A1（各形态 `CODEX_THREAD_ID`）+ A3（`claude -p` 能否拿到 findings）+ Codex e2e（10.1：`host="codex" runner="claude"` 锚 + anchor_lint 绿）；把实测真值写回 proposal 假设表 + design Risks。**任一在主力形态失效 ⇒ 须补 headless 替代信号或缩 scope**（design Migration step 0 已定该纪律）。

---

## ✅ 完成了什么（Claude-side，均附机验锚点，见 verify-report.md）

- **宿主/档位解析** `resolve-models.sh`：4 分支正信号判宿主 + 机队档位映射 + `printf %q`/字符集 eval 注入加固（test_resolve_models.py，25 passed；含 D1 含空格 root 引号回归）。
- **anchor_lint**：`host` 必填 + always-on 合法组合矩阵（`classify_combo`/`check_legal_combo`，metrics 门控之前无条件调用）+ fan-out 一致性 lint（读 `mirrors=`）+ 不判宿主边界锁 + **B1 补 OV 行 3 不变量校验**（test_anchor_lint.py，115 passed）。
- **lens_metric_emit**：`--host` 单一源受控 fail-closed（parse_known_args + extras 拒）+ 行键升 `(lens,host,runner,site)` + runner=none 合法 + 零执行不变量自检。
- **outside_voice_guard**：same-family 七码 + 本地重实现矩阵 + 全笛卡尔跨工具 golden；**C1 删除 codex#N prose 补位旁路 fail-open**（test_outside_voice_guard.py，42 passed）。
- **lens_metric_aggregate**：双代兼容读（claude-fallback→claude,claude；无 host→claude）+ host 分组 + 存量归档逐行一致回归。
- **outside-voice.sh**（v1.3.0）：preflight 探目标 runner · runner 分叉 · secret_scan/render_prompt 单份共用 + D8 脱敏 · **A1 反向 claude 路径承重墙第四旗 `--settings` 读围栏（permissions.deny 挡凭证库，本机实测硬拦）+ 出境侧 secret_scan** · HOST=unknown 不跑 voice（test_outside_voice.py，51 passed）。
- **两评审 SKILL + model-tiers**：档位按机队分列 · 锚文法 host= · **V1 eval 带防护四步次序（unset+预检+捕获+校验 fail-loud）** · **V2 F8 fallback-unavailable 分支** · **B2 模板锚补 host=** · skew 探测 fail-loud。
- **消费铺设**：claude-section/AGENTS.md Codex 子代理授权声明 · fanout-capability 锚 · 子代理不可用缩 roster 诚实边界。
- **文档收尾**：workflow-map.{md,html} 字段表同步；全量 pytest **1426 passed** + setup 两道门（sync_principles/gen_workflow_guide --check）绿；Claude 宿主 e2e 行为不变（10.2）。
- **code-review 处置**：冷全 change 层抓 8 findings（C1/B1/V1/A1 4 高危 + V2/D1/B2 + C2 defer），全部 objective 代码修复已清、TDD + 真 claude e2e（code-review-report.md，verdict pass）。

## ⏳ 未完成 / 延后

- **🔴 Codex efficacy 真机验证**（见顶部）——0.1/0.2/0.3/10.1，deferred 至 Codex 宿主，用户 C 授权未验即合并。**这是最高优先级的合并后欠债。**
- **批次 `add-codex-host-support`**（见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`）：
  - **T149**（代码质量）`init.py` lint_config `metrics.enabled` 重复键无告警（valid 恒 True，潜在一致性盲点）。
  - **T150**（功能增强）`outside-voice.sh` preflight 未按 ADR-6「真跑一次」补真探针（V5：CLI 未认证/模型无效仍返回 ready，失效漏到 exec）。
- **design-writeback（本次 done/archive 已随 delta 一并订正，见 archive 记录）**：A1 design 安全表沙箱不对称 · B1「均查」决策记录 · V3 v1-reason_code compat · V4 ADR-0024 措辞 · V5 ADR-6「真跑一次」措辞。
- **Minor（verify 登记，不阻塞）**：无核心代码缺口。

## ▶ 下一阶段建议

1. **最优先**：用户在真实 Codex 宿主补跑 A1/A3/Codex-e2e，把实测真值写回 proposal/design；若失效则另开 scope 收缩 change。
2. **运行时生效**：本 change 改了 `assets/hack/`（`outside-voice.sh`/`resolve-models.sh`）——合并后须在运行 checkout（`~/.skills/sdflow-skills`）`git pull` + **重跑 `bash setup.sh`**（copy 非 symlink，pull→setup 窗口期"新 SKILL 调旧脚本"）。
3. **清批次 `add-codex-host-support`**（T149/T150）：可并入下个相关 change 或单开一个小 cleanup change 一起清；优先级低。
4. **roadmap**：本 change 无 roadmap 关联（独立 change），无需回填。
