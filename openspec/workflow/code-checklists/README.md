# 代码审查规则集（通用 base + 领域 delta）

> 项目无关、可复用的**代码实现审查**规则集，在 `/review`（代码阶段）使用。
> 架构与 [`../spec-checklists/`](../spec-checklists/)（设计阶段审查）对称：**通用 base + 领域 delta**，
> 共用 [`../trigger-catalog.md`](../trigger-catalog.md) 的 TG 决定领域深度。

---

## 架构

```
  code-review-base.md           通用 base —— 任何代码都适用（语言无关）
        │  每次 /review 必过
        ▼
  domains/<domain>.md           领域 delta —— 按命中技术栈叠加
        backend.md              后端通用（DB/HTTP）
          └ backend-go.md       Go 语言习惯 (extends backend)
        embedded.md             嵌入式 RTOS+C 通用
          ├ embedded-ml307c.md  ML307C delta (extends embedded)
          └ embedded-esp32.md   ESP32 delta (extends embedded)
        [future] ...
```

每层只写自己新增的审查项；读某栈完整清单 = base + 对应领域链并集。

## 选用规则（与 spec-checklists 同源 TG）

`/review` 按变更**命中的 TG**（见 trigger-catalog）选领域，与设计期 autoplan 选 spec 领域**同一套触发**：

```
  命中 TG-01(后端) → code-review-base + backend(+go)
  命中 TG-02(嵌入式) → code-review-base + embedded(+芯片 delta)
  命中 TG-03(前端) → code-review-base + frontend（如有）
```

## ID 约定

| 前缀 | 层 |
|------|----|
| `CR-NN` | 通用 base |
| `CR-BE-NN` / `CR-GO-NN` | 后端通用 / Go delta |
| `CR-EMB-NN` | 嵌入式通用 |
| `CR-ML307C-NN` / `CR-ESP32-NN` | 芯片 delta |

ID 一经分配不复用、不重排。

## 与 spec-checklists 的关系

```
  设计期(autoplan) → spec-checklists/   "设计对不对"
  代码期(/review)  → code-checklists/   "实现对不对"
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

*规则集 v1 · 项目无关 · 代码审查（/review 阶段）*
