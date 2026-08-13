# Spec 质量规则集（通用 base + 领域 delta）

> 项目无关、可复用的 spec 质量规则集。架构为 **通用 base + 领域 delta**：
> 任何 spec 先过 base；再按变更命中的技术栈，叠加 `domains/` 下对应领域规则。
> 领域可持续扩展，新增领域不改 base。

---

## 架构

```
  spec-quality-base.md          通用 base —— 任何 spec 都适用(domain-agnostic)
        │  每个 spec 必过
        ▼
  domains/<domain>.md           领域 delta —— 按命中的技术栈叠加,可多选、可分层
        backend.md              后端服务通用
          └ backend-go.md       Go delta (extends backend)
        embedded.md             嵌入式 RTOS+C 通用
          ├ embedded-ml307c.md  ML307C delta (extends embedded)
          └ embedded-esp32.md   ESP32 delta (extends embedded)
        frontend.md             前端 / UI 通用
        [future] ...            新领域在此扩展
```

**分层原则**:每层只写**自己新增的规则(delta)**,通过 `extends:` 声明父层,绝不整份复制父层内容。
读一个芯片 delta = 读 `base` + `embedded` + `embedded-<chip>` 三层并集。

---

## 选用规则（哪个 spec 过哪些清单）

1. **base 永远过**——无条件。
2. 变更**实际涉及**某技术栈 → 叠加该领域链。例：
   - 改 Go 后端服务 → `base` + `backend` + `backend-go`
   - 改 ML307C 固件 → `base` + `embedded` + `embedded-ml307c`
   - 跨栈变更 → 多条领域链并集
3. **不涉及的领域不要叠**——避免无关项稀释注意力（轻量变更可只过 base）。

---

## 规则 ID 约定（稳定、可引用）

每条规则有稳定 ID，前缀标明所属层，便于被模版/lint/约束等下游引用：

| 前缀 | 层 | 示例 |
|------|----|----|
| `BASE-NN` | 通用 base | `BASE-01 完整性` |
| `BE-NN` | backend 通用 | `BE-03 Auth 边界` |
| `GO-NN` | backend-go delta | `GO-01 errgroup 生命周期` |
| `EMB-NN` | embedded 通用 | `EMB-02 任务栈预算` |
| `ML307C-NN` / `ESP32-NN` | 芯片 delta | `ESP32-02 OTA 双槽安全` |

ID 一经分配不复用、不重排——删除规则只留空号，新增规则取新号。

## 落点列（base 每条标注，供下游生成视图）

base 规则带 `落点` 标签，指明该规则最终**怎么落地执行**（这是规则集之外的多视图基础）：

| 落点 | 含义 | 下游产物 |
|------|------|---------|
| **T** | 模版槽位 | spec/design 模版里的固定章节，空槽即可见缺失 |
| **C** | 生成约束 | 生成时主动行为（grep/阻塞），见 `../ff-generation-constraints.md` |
| **S** | 自动扫描 | lint 式机械检查（占位符、形容词 NFR…） |
| **R** | 对话/评审 | 需人判断，留 `/sdflow-spec` 相位 B 拷问 / `/sdflow-spec-review` |

---

## 领域注册表

| 领域文件 | extends | 适用栈 | ID 前缀 | 状态 |
|---------|---------|-------|--------|------|
| `domains/backend.md` | base | 后端服务（任意语言） | `BE-` | ✅ 就绪 |
| `domains/backend-go.md` | backend | Go | `GO-` | ✅ 就绪 |
| `domains/embedded.md` | base | RTOS + C 嵌入式 | `EMB-` | ✅ 就绪 |
| `domains/embedded-ml307c.md` | embedded | ML307C（蜂窝模组） | `ML307C-` | ✅ 就绪 |
| `domains/embedded-esp32.md` | embedded | ESP32-C3（WiFi SoC） | `ESP32-` | ✅ 就绪 |
| `domains/frontend.md` | base | 前端 / UI（任意框架） | `FE-` | ✅ 就绪 |
| `domains/devex.md` | base | developer-facing 交付面（CLI/API/SDK/skill/配置面，TG-28，**spec-review-only**） | `DX-` | ✅ 就绪 |

---

## 如何新增一个领域（扩展约定）

1. 在 `domains/` 建 `<domain>.md`，文件头声明 `extends: <父层>`（base 或某领域）。
2. **只写本层新增规则**，每条取新 ID（前缀=领域简称）。不复制父层任何条目。
3. 每条规则给出：触发条件（什么变更需要查）、检查点、为什么（防什么失效）。
4. 在上方「领域注册表」登记一行。
5. 不改 base、不改父层——扩展是纯增量。

---

*规则集版本：v1 · 项目无关通用版*
