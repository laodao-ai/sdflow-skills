# sdflow-init 健壮性清理批（T21/T22/T48/T49）

## Why

`sdflow-init/scripts/init.py` 及其调用路径在历次 review 中 defer 了 4 项健壮性/代码质量残差（均已入 todolist、批次 `sdflow-init-hardening`），交本 cleanup change 一轮清完。四项同模块（init.py 为主）、同类（健壮性）、个体低危，属相关合批——不改 `sdflow-init` 铺设能力的行为契约，只让它在**并发 / 畸形输入 / Python2 环境**下不静默出错。

四项 triage 时的低影响判断（保留其诚实）：T49 因 RETIRED 幂等下次重收敛、T21 仅手工粘贴畸形态产生、T22 仅 `-W error` 加严才暴露、T48 Python2 近绝迹——但四者均有明确失效面（数据丢失 / 锚错位 / 19 Unraisable warning / f-string 解析崩），清之无损行为契约、有净健壮性收益。

## What Changes

四项修复，主落 `sdflow-init/scripts/init.py`（T48 连带 `setup.sh` python 探测）+ 对应 tests：

- **T49**（`init.py:_deregister_hook_in_settings` · 代码质量 · **数据丢失面**，主）：settings.json 已用 temp+`os.replace` 解撕裂 JSON，但读（`json.load`）→改→`os.replace` 之间仍有并发 lost-update TOCTOU 窗口——两进程各基于旧内容读写，一次修改被静默覆盖。用 `fcntl.flock` 在**独立 lockfile** 上串行化整个「读-改-写-replace」临界区（`flock(LOCK_EX)`）。`fcntl` 仅 POSIX——Windows 无 `fcntl` 时 best-effort 降级为无锁（保持现行为、留注释声明局限，不新增崩溃面）。调用契约（返回是否 deregister）不变。
- **T22**（`init.py` · 代码质量）：多处 `open(path).read()` / `json.load(open(path))` 无 context manager（`-W error` 下 19 个 `PytestUnraisableExceptionWarning`，文件句柄靠 GC 关闭）。统一改 `with open() as f:`，句柄确定性释放。写侧（已 `with`）不动。
- **T21**（`init.py:inject` / `_find_marker_line` · 代码质量）：畸形态加固——① 多个重复旧 marker 区块只修第一个；② `_find_marker_line` 的 `text.index` 在**行内嵌入相同 marker 文本**时可能锚错位。改为逐行精确匹配 marker 行、检测并处理多重复块（幂等下不自然产生，仅手工粘贴畸形态，记债性修复）。
- **T48**（`setup.sh` python 探测 · 基础设施）：探测在 `python3` 缺失时 fallback 到裸 `python`，可能是 Python2 → 喂 init.py 在 f-string **解析期**崩（留晦涩 SyntaxError traceback）。**真修点在调用侧 setup.sh**：选定解释器后校验 `sys.version_info >= (3,6)`，非 py3.6+ 则跳过并给清晰非致命提示（复用现有 fail-safe 尾式），不喂 init.py。**诚实 scope 修正**：init.py 内加 `sys.version_info` 守卫**无效**——Python 整模块编译先于任何语句执行，f-string 在别处，守卫语句根本来不及跑（故不加无功能的假守卫，仅在 init.py 头补一句「需 3.6+、由调用侧 setup.sh 把关」文档注释）。**scope 边界**：只修 setup→init.py 这条实际触发路径的探测，不做「全仓每 .py 逐一加守卫」大扫除（属 Leg3 正交批范畴，避免本 change 膨胀）。

## Impact

- **代码**：`sdflow-init/scripts/init.py`（T49/T22/T21/T48）、`setup.sh`（T48 python 探测）。
- **测试**：`sdflow-init/tests/`（每项补反证哨兵测试：T49 并发 lost-update 不丢 / T22 `-W error` 零 Unraisable / T21 多重复块 & 内嵌 marker 文本 / T48 版本守卫触发）。
- **能力契约**：`sdflow-init` 铺设行为不变，无 spec delta。
- **风险**：低。T49 触并发逻辑面、T21 触解析逻辑面 → **cold code-review 层真跑**（不作正交批跳镜，遵 `cold-code-review-load-bearing`）。跳 grill/spec-review/设计门（无新设计决策，flock/版本守卫均标准解）。
