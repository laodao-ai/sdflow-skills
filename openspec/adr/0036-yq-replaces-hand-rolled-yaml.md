# 7 份手搓 YAML/frontmatter 解析器统一委托外部 yq 二进制

> 状态：**Accepted**（2026-08-01，`shared-yaml-subset-parser` 拍板收敛）· 关联 change：`shared-yaml-subset-parser`
>
> **状态注记（2026-08，`adr/0039`）**：下文「7 个脚本」计数含消费仓镜像 `openspec/workflow/tools/anchor_lint.py`——
> 该镜像已随 `adr/0039`（消灭双链）停止铺设并从本仓删除，权威源 `sdflow-init/assets/workflow/tools/anchor_lint.py`
> 条目保留。计数应读作 **6 份**（见 `openspec/specs/yq-yaml-operations/spec.md` Purpose 与
> `hack/tests/test_yq_wrapper_consistency.py`），本文历史计数原文不改。

## Context

本仓 7 个脚本（`sdflow-init/scripts/init.py`、`sdflow-ship/scripts/ship_gate.py`、
`sdflow-implement/scripts/impl_route.py`、`openspec/workflow/tools/anchor_lint.py`
及其 bundle 副本、`sdflow-done/scripts/roadmap_writeback_draft.py`、
`sdflow-architecture/scripts/sad_schema.py`）各自手搓了一份 YAML/Markdown-frontmatter
子集解析器（合计 ~456 行），用于读 `config.yaml` 的顶层键/`model-tiers`/`metrics` 块，
以及读评审报告、plan、SAD 文档的 frontmatter。这些解析器长期各自独立演进、语法覆盖面
互不一致（有的处理引号剥离，有的不处理；有的能识别连字符键名 `ship-gate:`，有的靠
特判）。

CLAUDE.md 基准 5（无界不手搓）明确警告：「无界语法面（YAML 属此类）手搓解析器，
必然是对真实输入有 N 种罢工姿势的脆件……当你发现『每轮 review 都在同一个函数里补一个
新的语法分支』，那不是『还差最后一个 case』，那是『这个函数本来就不该存在』」。本仓的
YAML 消费面正处于这个信号里：`init.py` 的 `_parse_model_tiers_block`、`ship_gate.py`
的 `parse_ship_gate_frontmatter`、`sad_schema.py` 的 `parse_frontmatter` 都在历次
review 中反复补丁（tab 缩进检测、重复键检测、facts 内联误用检测……），且各自的补丁
互不共享——同一类语法角落在 7 处分别踩坑、分别修。

MIT 许可、13k+ stars 的 `mikefarah/yq`（Go 实现、单一二进制、无运行时依赖）已成熟到
可作为「让工具自己回答自己的语法」（basis-5 正解）的落点：本 change 拍板前的实测覆盖
了本仓全部现有场景——`config.yaml` 顶层键读写、嵌套 `model-tiers` 块、Markdown
frontmatter 读写（`--front-matter=extract/process`）、写操作注释保留、连字符键名
（`."impl-pipeline"`/`.ship-gate.design_approved`）。

## Decision

**7 个脚本的 YAML/frontmatter 解析器全部替换为对外部 `yq`（mikefarah/yq）二进制的
subprocess 调用**，各脚本内联一份 `~10 行` 的 `_yq()` 薄封装（不跨脚本共享——各脚本
「零依赖不变量」不允许互相 import，且封装体量小到共享收益低于耦合成本）。分工线：

- **语法层**（缩进、冒号、引号剥离、注释剥离、多文档判定、连字符键名）→ 全部委托 yq。
- **业务层**（顶层键白名单、枚举值校验、fleet/tier 键集校验、PASS/FAIL 判定）→ 保留
  Python 侧，在 yq 已解析出的 dict 上做判断。
- **少数无法委托的残余**（有确定性信号但 yq 语义与既有契约冲突的场景）→ 显式保留纯
  文本预扫描，逐脚本记录理由：
  - `ship_gate.py` 的 duplicate-key/tab-indent 检测（yq 对前者静默取最后值、对后者
    只报笼统词法错误，两者都是 yq 给不出的诊断精度，R11 明文保留）。
  - `roadmap_writeback_draft.py`/`sad_schema.py` 的 frontmatter 闭合性预扫描（yq 对
    没有第二个 `---` 的输入会把首行之后全部内容当同一份文档解析，若恰好合法会静默
    "解析成功"，与"未闭合→fail-closed"的既有契约冲突）。
  - `sad_schema.py` 的 `frontmatter_end`（`sad_scaffold.py` 用它做行级原地改写，需要
    "第几行是定界符"这一位置信息——yq 是值抽取器、不回答位置问题，这是有界字面定界符
    定位，非无界 YAML 解析，不违反 basis-5）。
  - `init.py` 的 `_schema_from_config`/`_set_schema_key`（yq 在"文档以 `--- # 注释`
    起始"这类真实存在的写法上，读写两侧各有一类会丢数据/丢键的缺陷，且两个缓解 flag
    互斥；该函数处理的语法面是"一个固定字面量键的定位与原地替换"，有界，继续手搓是
    因为手搓已经正确、且比 yq 更正确）。

**yq 通过系统包管理器全局安装**（`brew install yq` / `winget install --id
MikeFarah.yq` / `snap install yq`），与 git/python3/openspec CLI 同层级视为运行依赖；
`setup.sh` 新增 `check_dependencies()` 统一检测并给出安装指引（含 mikefarah/yq 与
kislyuk/yq 的身份区分——两者命令名相同但语法不兼容）。

## Considered Options

- **本方案（yq 全量替代，选中）**——依据见上。
- **共享子集解析器**（把 7 份手搓实现合并成 1 份内部共享模块）：砍掉，理由：仍需
  维护手搓代码，只是把维护面从 7 处收敛到 1 处，风险性质不变（无界语法面手搓解析器
  依旧存在，依旧会在下一个未预见的语法角落罢工），且与「各脚本零依赖、不跨脚本
  import」的既有边界冲突。
- **PyYAML 降级封装**（`import yaml`，找不到则退化为手搓兜底）：砍掉，理由：
  ① 违反零依赖不变量（`MUST NOT import yaml`——脚本被 symlink 进任意消费仓，多数
  消费仓无 PyYAML，`import` 会 `ImportError` 崩溃，与 fail-closed 相悖）；② "找不到
  则退化为手搓兜底"等于两套实现都要维护，复杂度不降反升。
- **自管二进制**（把 yq 二进制放进 `~/.sdflow/bin/` 由 setup.sh 分发）：砍掉，理由：
  需要自己做平台判断、版本更新、架构检测（x86/arm）——这些包管理器已经做好，重新
  实现是自找维护成本，且与 git（同样靠系统包管理器/预装）的处理方式不一致。
- **只改 `config.yaml` 消费者**（3 个脚本改 yq，`frontmatter` 消费者维持手搓）：砍掉，
  理由：yq 实测同样覆盖 Markdown frontmatter 场景，留 4 个脚本不改会形成"一半用 yq、
  一半手搓"的混合态，比"全部统一"更难维护、更难判断"这个脚本的 YAML bug 该去哪修"。

## Consequences

- **零依赖不变量的精神收窄**：原表述「MUST NOT 依赖任何外部 YAML 工具」收窄为
  「MUST NOT `import` YAML 解析库」——yq 是外部二进制（同 git 的既有先例），subprocess
  调用不算 Python 依赖。这是本 ADR 引入的唯一一处对既有不变量措辞的调整，后续任何
  「零依赖」相关讨论都应识别这一收窄，不要误读为"完全零外部工具"。
- **诊断精度整体下降**：手搓解析器能对多数坏输入精确点名"哪一行/哪个字段"；yq 委托后，
  整份文档的语法错误（如一处漏冒号）会让**整份文件**判定解析失败，调用方只能拿到 yq
  的原始错误文本，不再有"局部容错、精确定位"的能力。7 个脚本的既有测试套件中，凡依赖
  这类精确诊断的断言均已随之重写（改为验证"yq 报告解析失败"这一行为，而非具体错误
  文案）——这是委托 yq 换取"不再手搓 YAML 解析器"的既定代价，不是缺陷。
- **新增运行依赖 yq**：开发者/CI 环境须安装 yq（mikefarah/yq，非 kislyuk/yq）。
  `setup.sh` 的 `check_dependencies()` 与各脚本的 `_yq()` 均在缺失/身份不对时给出
  清晰的安装指引，不静默失败；CI（`mechanical-gates.yml`）显式安装并钉版本，不依赖
  runner 镜像预装。
- **写操作注释保留不保证 100% 字节不变**（空行/尾部注释位置可能有微调）：影响面小
  （本仓写操作路径少，均已在各自测试中核验语义不变），接受。
- **`~456` 行手搓 YAML 解析代码归零**：`_strip_inline_comment` / `_find_top_level_block`
  / `_second_level_keys` / `_parse_model_tiers_block`（旧版行扫描器）/ `_extract_scalar`
  / `frontmatter_end` 之外的所有手写 YAML 语法扫描函数均已删除或收窄为纯业务判断，
  换来的是"每轮 review 在某个脚本里挖到新 YAML 语法分支"这一常态的消失（basis-5 的
  目标态）。
- **回滚代价**：revert 需要同时恢复 7 处手搓实现 + 撤回 `setup.sh`/CI 的 yq 依赖声明；
  各脚本 `_yq()` 内联、不跨脚本共享，revert 可逐脚本独立进行，不要求一次性整体回滚。
