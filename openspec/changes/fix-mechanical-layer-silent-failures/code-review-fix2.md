# code-review-fix2 — test_outside_voice_utf8.py M3 磁盘写满用例的 macOS CI 假红修复

对象：`sdflow-init/tests/test_outside_voice_utf8.py::test_exec_disk_full_render_meta_gets_unconditional_stderr_diagnostic`。
背景：M3（`do_exec` 在 `render.meta` 为空时打不依赖磁盘的兜底诊断）的产品代码本身正确，但锁它的
测试脚手架在 macOS CI runner 上假红（CI run `29673453574`）。本次只动测试脚手架，**未碰
`outside-voice.sh` 产品代码**。

## 根因

`_run_disk_full_scenario` 用固定字节数（`fill_to(8000)`）表达"留几 KB 可用空间"这个目标。
`os.statvfs` 报告的可用空间在实际发生【分配块级别】的 quantization——本机默认 4096 字节分配块下，
同一个字节目标填盘后落地的可用空间是 4096 还是 8192 这类整块数，取决于该 macOS 版本 /
`newfs_hfs` 默认参数下 catalog 元数据的一次性开销（这个开销在不同 runner 上不同）。开发机上
这个字节数恰好落在"够 `mkdtemp` 建目录、不够写完整 ~5KB prompt"的那个块；CI runner 上落在
"连 `mkdtemp` 都不够"的块——workdir 建不出来，执行流根本走不到 `render_prompt`，而变异体
（还原成旧版"读到啥转发啥"）在同样"建不出 workdir"的场景下，也会打出 `mktemp` 自己的 shell 层
诊断，导致"变异体 stderr 应全空"这条差异化断言失真变红。

## 方案：A（自适应块级校准）为主 + 窄口径 skip 兜底，未走 B（放松断言）

**为什么选 A**：A 直接消灭假红的根因（前提本身建不起来），且是"让文件系统自己回答"（基准 5）
而非继续猜一个字节数；B（放松变异体断言到"非空也算过"）会直接废掉本用例唯一的承重来源
（差异化验证），任务要求里明确排除这条路。

**A 的具体实现**（`sdflow-init/tests/test_outside_voice_utf8.py`）：

1. **块粒度自适应探测**（新增 `_calibrate_min_free_blocks` + `_fill_leaving_blocks`）：不再赌
   一个字节数，改为在【这一块全新 ramdisk】上从 1 个分配块开始试建目录，失败就加到 2 块、3
   块……直到成功，探测到的目录随即删除（把空间还给可用池——此时 catalog b-tree 该发生的一次性
   扩容已经发生且是粘性的，不会随 `rmdir` 缩回去，所以随后真实脚本自己的 `mktemp -d` 只会比探测
   更宽松）。8 块内探测不出 ⇒ 判定本次建不起前提 ⇒ `pytest.skip`（不是断言失败）。
2. **ramdisk 格式化块大小从默认 4096 缩到 512**（`newfs_hfs -b 512`，HFS+ 允许的最小值，仅有
   "非最优"警告、无功能损失，catalog/extent b-tree 节点大小仍是 4096）：默认 4096 的块粒度和
   本场景要卡的目标写入量（完整 prompt ~5146 字节）是同一数量级，1 块之差就能把"mkdir 刚好够、
   写不下 prompt"翻成"mkdir 都不够"或"prompt 也写得下"——本地压测证实两种翻车都真实发生过。
   缩到 512 后，同一开销相对目标写入量的粒度误差从 ~80%（4096/5146）降到 ~10%（512/5146）。
3. **窄口径兜底 skip**（`_shell_level_enospc_noise`，检测 `"mktemp 失败:"` 或
   `"No space left on device"` 这两类 shell/coreutils 自己的原生诊断）：即便经过 1+2 的校准，
   仍有极小概率（本地 100 次压测中 9 次）撞见"建前提本身在走到 M3 差异化代码之前就失败"——
   这些原生诊断在真实版/变异版之间完全相同（因为它们来自变异未触碰的更早代码），若不拦截会
   使差异化断言失真。命中 ⇒ `pytest.skip`，skip 文案显式写明"这不代表 M3 已失效，MUST NOT
   因为本用例常 skip 就删掉它"。**未改动**任何一条实质性断言（`returncode != 0` /
   `stdout == b""` / `stderr` 非空且 ≥10 字节 / 变异体 `stderr == b""`）。

## 本机验证

`_run_disk_full_scenario` 与差异化断言逻辑单独用 Python 直跑一次（不经 pytest 断言，只看
产出）：

```
REAL   rc=1 stderr=b'outside-voice: render_prompt \xe9\x9d\x9e\xe9\x9b\xb6\xe9\x80\x80\xe5\x87\xba(rc=1)——诊断文件为空（疑似 workdir 所在磁盘写满/写入失败），无法给出更详细原因\n'
MUTANT rc=1 stderr=b''
```

真实版命中 M3 兜底诊断，变异版 stderr 全空——差异化验证成立。

`pytest -k disk_full` 单测连续压测 **100 次**：91 次真实通过（走完整差异化验证）、9 次因窄口径
`_shell_level_enospc_noise` 命中而 `skip`（均带清晰理由）、**0 次失败**。此前（仅做块级校准、
未加窄口径 skip 兜底）40 次压测中出现过 2 次真失败（均是"shell 层 ENOSPC 噪声污染差异化断言"
这一类）。

全套件：

```
/usr/bin/python3 -m pytest -q
1753 passed, 3 skipped in 110.39s
```

3 个 skip 均为套件既有的、与本次改动无关的 skip（非本次改动引入）。

## 未改动

- `sdflow-init/assets/hack/outside-voice.sh`（M3 产品代码本身正确，本轮未碰）。
- 本用例的实质性断言强度——只加了"建前提失败即 skip"的判定，未放松任何一条既有断言。

## 状态

`DONE`。改动仅限 `sdflow-init/tests/test_outside_voice_utf8.py`（`_make_tiny_full_ramdisk` /
新增 `_fill_leaving_blocks` + `_calibrate_min_free_blocks` / `_run_disk_full_scenario` /
`test_exec_disk_full_render_meta_gets_unconditional_stderr_diagnostic`），均标 `[impl-review-fix]`。
