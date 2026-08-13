# 代码审查规则集（通用 base + 领域 delta）

> 项目无关、可复用的**代码实现审查**规则集，在 `sdflow-code-review`（代码阶段，含 `sdflow-implement` Standards 轴必填槽）使用。
> 架构与 [`../spec-checklists/`](../spec-checklists/)（设计阶段审查）对称：**通用 base + 领域 delta**，
> 共用 [`../trigger-catalog.md`](../trigger-catalog.md) 的 TG 决定领域深度。

---

## 架构

```
  code-review-base.md           通用 base —— 任何代码都适用（语言无关）
        │  每次 sdflow-code-review 必过
        ▼
  domains/<domain>.md           领域 delta —— 按命中技术栈叠加
        backend.md              后端通用（DB/HTTP）
          └ backend-go.md       Go 语言习惯 (extends backend)
        embedded.md             嵌入式 RTOS+C 通用
          ├ embedded-ml307c.md  ML307C delta (extends embedded)
          └ embedded-esp32.md   ESP32 delta (extends embedded)
        frontend.md             前端 / UI 通用
          └ frontend-react.md   React delta (extends frontend)
        [future] ...
```

每层只写自己新增的审查项；读某栈完整清单 = base + 对应领域链并集。

## 选用规则（与 spec-checklists 同源 TG）

`sdflow-code-review`（及 `sdflow-implement` Standards 轴必填槽）按变更**命中的 TG**（见 trigger-catalog）选领域，与设计期 sdflow-spec-review 选 spec 领域**同一套触发**：

```
  命中 TG-01(后端) → code-review-base + backend(+go)
  命中 TG-02(嵌入式) → code-review-base + embedded(+芯片 delta)
  命中 TG-03(前端) → code-review-base + frontend(+frontend-react)
  命中 TG-27(LLM 集成面) → code-review-base + llm
```

## ID 约定

| 前缀 | 层 |
|------|----|
| `CR-NN` | 通用 base |
| `CR-BE-NN` / `CR-GO-NN` | 后端通用 / Go delta |
| `CR-EMB-NN` | 嵌入式通用 |
| `CR-ML307C-NN` / `CR-ESP32-NN` | 芯片 delta |
| `CR-FE-NN` | 前端通用 |
| `CR-REACT-NN` | React delta |
| `CR-LLM-NN` | LLM 集成面（code-review-only domain） |

ID 一经分配不复用、不重排。

## 与 spec-checklists 的关系

```
  设计期(sdflow-spec-review) → spec-checklists/   "设计对不对"
  代码期(sdflow-code-review + sdflow-implement Standards 轴)  → code-checklists/   "实现对不对"
  两者共用 trigger-catalog 决定领域；互不重复（一个审 spec，一个审 code）
```

## 领域注册表

| 文件 | extends | 栈 | ID 前缀 |
|------|---------|----|--------|
| `domains/backend.md` | base | 后端服务 | `CR-BE-` |
| `domains/backend-go.md` | backend | Go | `CR-GO-` |
| `domains/embedded.md` | base | RTOS+C | `CR-EMB-` |
| `domains/embedded-ml307c.md` | embedded | ML307C | `CR-ML307C-` |
| `domains/embedded-esp32.md` | embedded | ESP32-C3 | `CR-ESP32-` |
| `domains/frontend.md` | base | 前端 / UI（任意框架） | `CR-FE-` |
| `domains/frontend-react.md` | frontend | React | `CR-REACT-` |
| `domains/llm.md` | base | LLM 集成面（代码消费 LLM/agent 产出） | `CR-LLM-` |

## 扩展约定

新增领域的五步扩展约定（新建 domain 文件、ID 分配、登记注册表等）见
[`../spec-checklists/README.md`](../spec-checklists/README.md) §如何新增一个领域——两侧同法，
本侧 ID 前缀改用 `CR-` 系。

*规则集 v1 · 项目无关 · 代码审查（sdflow-code-review / sdflow-implement Standards 轴阶段）*
