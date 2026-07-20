## 1. design 域：`-m` → `--cc`（P0，修已上线假阳）

- [ ] 1.1 `frame_touched_paths` 协议改 `git diff-tree --cc -r --raw --no-renames -z --no-commit-id --root <帧>`；docstring 改写 `-m` 段，写明「`-m` 逐 parent 输出、parent2 常早于锚 ⇒ 重报锚前历史 ⇒ 例行 merge 假阳」
- [ ] 1.2 确认 `::` 三列形态在既有 `:`-前缀成对解析器下无需改解析（grill 已实测，实现期复验一次）
- [ ] 1.3 回归：design 域现有全部用例通过。**唯一允许改的用例是「例行 merge 假阳」一类**——其他任一用例需要改 = 语义额外变了 = 停下重判

## 2. code 域：改树比较（P0，关闭三个 fail-open）

- [ ] 2.1 新增 `code_changed_paths(root, sha)`：`git diff --raw --no-renames -z <sha> HEAD`，返回路径列表；非零退出 → `None`
- [ ] 2.2 `is_stale` 的 code 分支重写为单次调用 + 谓词（存在非 `openspec/` 前缀路径即失鲜）；删除逐帧循环
- [ ] 2.3 `code_changed_paths` 返回 `None` ⇒ 判失鲜 `category="enum-failed"`。**MUST NOT** 当空集跳过
- [ ] 2.4 逐条判定 design 域各防护在 code 域的方向，结论落 impl-report（merge / rename / 枚举失败 = 须补；控制字符 = 方向反转，锁新方向）

## 3. git 调用失败落进退出码契约（P1）

- [ ] 3.1 定义 `GitUnavailable` 异常；`run_git` / `run_git_rc` / `run_git_bytes` 三处捕获 `FileNotFoundError` 与 `subprocess.TimeoutExpired` 后抛出
- [ ] 3.2 三处统一 `timeout=30`，附注释说明判据来源（对齐 `buglist.py::repo_root`：文件系统卡死判定线，非性能预算）
- [ ] 3.3 `main()` **整个函数体**捕获 `GitUnavailable` → `UNKNOWN(6)` + 可读诊断。注意 `--root` 解析处的 `run_git` 在 `decide()` 之前，只包 `decide()` 会漏

## 4. code 域触发点诊断（P2）

- [ ] 4.1 code 域失鲜时填 `StaleResult` 的 detail（`paths` / `category`），复用 `_stale_trigger_hint` 渲染
- [ ] 4.2 category 词表：`code-touched`、`enum-failed`（与 design 域同名同义）
- [ ] 4.3 `sha`/`subject` 无值可填 → 注释写明是 ADR-5 已接受的代价，**MUST NOT** 为凑 sha 退回逐帧
- [ ] 4.4 断言机读 JSON 与人读文案同源

## 5. 测试与变异证明

- [ ] 5.1 code 域 evil-merge 用例（经 `is_stale` 入口，非只调 helper）
- [ ] 5.2 code 域 rename 用例：`git mv <非openspec路径> openspec/...` ⇒ 失鲜
- [ ] 5.3 code 域枚举失败用例 ⇒ 失鲜且 `category="enum-failed"`
- [ ] 5.4 code 域控制字符路径用例 ⇒ **fresh**（锁新方向），用例旁注明老 fail-closed 的成因
- [ ] 5.5 **例行 merge 不假阳**：design 域与 code 域各一例（侧支只碰对方域外路径 ⇒ fresh）
- [ ] 5.6 树语义两条行为锁定：改动后改回 ⇒ fresh；锚被 amend 成孤儿且树等值 ⇒ fresh
- [ ] 5.7 `code-review-report` 消费方首个用例（今天零覆盖；现存唯一 code 域用例走的是 `verify-report`）
- [ ] 5.8 `FileNotFoundError` 用例：`PATH` 无 git ⇒ exit 6（非 exit 1、非 traceback）
- [ ] 5.9 `TimeoutExpired` 用例（注入假 git 或 mock）⇒ exit 6
- [ ] 5.10 **变异证明**：逐条删除 5.1–5.9 各自守护的守卫，确认对应用例变红。结果逐条落 impl-report。**MUST NOT** 以"用例存在且为绿"充当证明
- [ ] 5.11 全套件回归（仓根 `pytest`），并在 merge 后于 `main` 上再跑一次

## 6. 文档与收尾

- [ ] 6.1 `ship_gate.py` 头注释更新：两域各用什么原语、为什么不统一（指向 adr/0026）；「已知不覆盖」段补本次登记的残余面（design 域 `timeout` 总量上界 30N）
- [ ] 6.2 hand-off 说明双向行为变更：撞 code 域失鲜先确认不是真漏审；此前被设计门假阳卡住的 change 会自然放行

## 测试覆盖图〔TG-18〕

```
                    ┌──────────────── is_stale 公共入口 ────────────────┐
                    │                                                   │
          scope=design（逐帧 + --cc）                      scope=code（树比较）
                    │                                                   │
    ┌───────────────┼───────────────┐         ┌──────────┬──────────┬───┴──────┬──────────┐
    │               │               │         │          │          │          │          │
既有用例(不改)  例行merge不假阳  --cc 回归  evil-merge  rename迁入  枚举失败  控制字符  例行merge
BR-7 真值表 8 格     5.5            1.3        5.1        5.2        5.3      5.4(fresh)  不假阳
内容豁免/短路次序     │              │          │          │          │          │        5.5
rename/枚举失败      │              │          └──────────┴────┬─────┴──────────┴──────────┘
    │                │              │                     [变异证明 5.10]
    └── 全部原样通过 ┘         [变异证明 5.10]                  │
                                                    ┌──────────┴──────────┐
                                              树语义两条锁定          消费方覆盖
                                              改回⇒fresh 5.6      code-review-report 5.7
                                              孤儿锚⇒fresh 5.6    verify-report(既有)

          ┌──────────── git 调用层（跨两域，main 入口） ────────────┐
          │                                                          │
  FileNotFoundError → exit 6                          TimeoutExpired → exit 6
          5.8                                                  5.9
          └──────────────────── [变异证明 5.10] ────────────────────┘

  覆盖口径：每个叶子 = 一个经公共入口求值的用例 + 一次「删掉守卫即变红」的变异证明。
  MUST NOT 只调内部 helper（fix-design-gate-freshness-proxy 的 rename 用例即此形态，
  在真实洞存在时仍为绿）。
```
