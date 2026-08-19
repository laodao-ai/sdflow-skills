# review-loop-breaker 账本 · harden-ticket-slicing

每轮 fix-review 后由编排层追加一行。格式 = `轮次 | 文件 | 指纹 | 严重度`。
计数窗口 = 全 change 生命周期（跨 ticket 累计，MUST NOT 按单票清零）。
本账本 git-tracked，**不构成机械门**——编排层仍需每轮自行读历史行 + 当轮结果比对完成判定。

熔断判据：(a) 同指纹连续 2 轮未消解；(b) 同一文件累计被 Critical/Important 命中 ≥3 轮
（与指纹无关的硬上限）。(a)(b) 同时命中时 (b) subsume (a)。

## Task 1

- 1 | `sdflow-init/assets/workflow/reference/change-decomposition-standard.md` | AND门判据近逐字复制、违反「与 BASE-18 互为指针不复制」 | Important（已派 fix）
- 1 | `sdflow-init/assets/workflow/reference/README.md` + `change-decomposition-standard.md` + `sdflow-init/assets/snippets/index-section.md` | 前置声明「被三处 SKILL 指针引用」当前为假（指针落在 Task 3） | Important（**编排层裁决：不成立，不派 fix**，见下方裁决记录）

### 编排层裁决记录（Standards 轴 finding #1）

**结论**：不成立，不修改文本；改为把「三处指针真实存在」钉成 Task 3 的硬验收核验点 + Task 5 收口 grep 核。

**理由（三镜 + 主次）**：
- **系统镜**：bundle 经全局 canonical 软链指向**运行 checkout**，未合并的开发分支对任何消费方不可见 ⇒ 不存在「对外为假」的窗口；而 reviewer 建议的修法（改将来时 / 注明「由 Task 3 接入」）要把**本仓票号与流程痕迹**写进要分发给消费仓的 bundle 文档，直接违反 DOC-1「正文即最终态，演进史进附录」。
- **用户镜**：change 作为整体落地后三处指针即存在，消费仓读者读到的一直是真陈述。
- **开发循环镜**：按其修法改，Task 3 还须回来二次改同一段话，纯 churn。
- **主次判定**：系统镜主导——「指针现在不存在 ⇒ 文本该改小」是通则③ 明列的「拿现状反驳目标」，目标态 producer（本 change）就是会产出那三处指针。

**该裁决的代价与兜底**：这条断言的成真**依赖 Task 3 真的落地三处指针**。兜底 = ① Task 3 的 dispatch prompt 显式要求 `grep -rln "change-decomposition-standard" sdflow-spec/ sdflow-roadmap/ sdflow-implement/ sdflow-code-review/` 命中全部四个文件；② Task 5 收口再核一次；③ 冷层 `/sdflow-code-review` 看到的是全票落地后的终态，此断言届时为真。

- 2 | `sdflow-init/assets/workflow/reference/change-decomposition-standard.md` | 同上指纹（AND门复制） | **已消解**（fix 轮 re-review 判通过，指针化后判定本体仅存 BASE-18 一处）
