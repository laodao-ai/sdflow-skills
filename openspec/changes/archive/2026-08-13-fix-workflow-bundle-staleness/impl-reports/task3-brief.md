### Task 3: reference 处置 + 同族面治 + config 同步

**Blocked-by:** none
**R-ID:** D6, D7, D8, D9

reference 文件处置（横幅/标注/移动）、同族失鲜面治（index-section / config.template / config.yaml / docs），具体位点：

- `Spec_Quality_Collaboration.md` 顶部加历史横幅
- `Spec_Quality_Methodology.md` 顶部加 L1 历史举例标注（仅标注，不逐处改写）
- `git mv reference/Token_Saving_Strategies.md docs/` + 移动后顶部加历史横幅 `[A6]`
- `PRD_vs_Spec.md`:27,64,104,112 opsx:ff→sdflow-spec + 顶部历史举例标注 `[A5]`
- `config.template.yaml`:23-27 去号段 + blurb 现行化
- `snippets/index-section.md` 按内容定位改 6 行（:10/:11/:12/:13/:18/:19）`[A1]`
- `docs/sdflow-fable5/02-module-reference.md`:160 去号段上界 `[A3]`
- 本仓 `openspec/config.yaml` 与 template 同款行手动同步，diff 对照确认无分叉

- [ ] reference 三文件横幅/标注均已添加
- [ ] `Token_Saving_Strategies.md` 已 git mv 至 `docs/` 且有历史横幅
- [ ] `PRD_vs_Spec.md` 4 处 opsx:ff 已改 + 顶部标注已加
- [ ] `index-section.md` 6 行全部按 A1 修正
- [ ] `config.template.yaml` 号段去上界 + blurb 现行化
- [ ] `openspec/config.yaml` 与 template 同款行一致（diff 对照）
- [ ] `docs/sdflow-fable5/02-module-reference.md`:160 号段已改

