# Tasks · add-frontend-checklists

> 追溯：本 change `skip_specs: true`（见 proposal Capabilities），任务不挂 Requirement ID，
> 逐条标注 proposal 优先级（P0/P1）与 design 决策号；条目内容源 = `research/absorption-candidates.md`（已拍板）。

## 1. Domain 条目落盘（P0）

- [ ] 1.1 `spec-checklists/domains/frontend.md` 增补 FE-06~FE-13（候选表 A 组 8 条，逐条对照原文检查点）+ 文件头机械层前置注记〔D5〕
- [ ] 1.2 新建 `spec-checklists/domains/frontend-react.md`：REACT-01~03（C 组，extends frontend，REACT-03 标 `[仅RSC]`〔D6〕）+ 机械层前置注记
- [ ] 1.3 新建 `code-checklists/domains/frontend.md`：CR-FE-01~08（B 组，extends base；CR-FE-06 注「CR-04 的前端特化」〔D4〕；CR-FE-07/08 以纯键盘交互口径措辞，不用 a11y/辅助技术叙述）+ 机械层前置注记
- [ ] 1.4 新建 `code-checklists/domains/frontend-react.md`：CR-REACT-01~07（D 组，extends frontend，CR-REACT-07 标 `[仅RSC]`〔D6〕）+ 机械层前置注记

## 2. 接线（P0）

- [ ] 2.1 `trigger-catalog.md` TG-03 领域列：`frontend` → `` `frontend`(+`frontend-react`) ``（与 TG-01/02 记法同构）
- [ ] 2.2 `spec-checklists/README.md`：架构图加 frontend-react 分支、ID 约定表加 `REACT-` 行、领域注册表加 frontend-react 行
- [ ] 2.3 `code-checklists/README.md`：架构图加 frontend 链、选用规则 L33「frontend（如有）」接实为 `frontend(+frontend-react)`、ID 表加 `CR-FE-`/`CR-REACT-` 行、注册表加 2 行

## 3. 同步与留痕（P1）

- [ ] 3.1 `checklists-guide.html`：覆盖表与「frontend code 缺失」类表述更新为目标态（只动表格与文案区块，不动脚本/样式；改后自检标签配对与目录锚点）
- [ ] 3.2 `openspec/INDEX.md` L23-24 括注标注 frontend 链就绪
- [ ] 3.3 核验 `research/absorption-candidates.md` 附件完整（26 条 + 备选冻结区 + 拍板头注 + 来源清单）

## 4. 收尾核验（P0）

- [ ] 4.1 proposal Success Metrics 逐条自验：`grep -rn "frontend（如有）"` 归零；TG-03 行含 delta 记法；两侧注册表行数；4 文件 ID 连续无冲突、形制一致（extends 头 + 表 + 尾注）
- [ ] 4.2 全仓 pytest 兜底（`/usr/bin/python3 -m pytest`），确认无既有断言受影响
