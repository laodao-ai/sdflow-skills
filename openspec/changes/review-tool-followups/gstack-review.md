<!-- sdflow:step1-broad-review v1 mode="native" -->
# gstack-review.md — review-tool-followups 广审层（Step1）

> **native 声明**：本层由主 session 原生执行（非子代理转述模拟）。双声均真实调用：
> - **codex 外声**：`~/.sdflow/hack/outside-voice.sh exec`（真实 codex，exit 0，`OV_TRUNCATED=false`，产物 `.outside-voice/design-voice-out.txt`）。
> - **独立 Claude 广审镜**：fresh-context 子代理（无 grill 偏置，69728 tokens / 7 tool_uses / 192s），读四件套 + 对码核验 engine.js/init.py/setup.sh。
> 侧信道佐证：codex 输出文件时间戳 + 子代理 usage 运行痕迹。改动标 `[gstack-amendment]`。

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->

## 一、codex 跨模型外声（4 findings，runner=codex）

| ID | 严重度 | 问题 | 证据 |
|----|--------|------|------|
| OV-1 | high | T45 陈旧 404 回落缺防递归：bootstrap 起手读 hash，回落又走 bootstrap，坏 hash 被重复读循环失败 | tasks.md:17 / engine.js:265 |
| OV-2 | medium | 初始深链未进 history.state，浏览器 Back 丢回根而非回深链 | engine.js:250/100 |
| OV-3 | medium | 同源守卫只比 origin、未归一化 url.pathname，`#http://localhost:8000/changes/X/` 同源但非 `/path` 形态 | engine.js:240/246 vs tasks.md:15 |
| OV-4 | medium | T44 setup.sh 集成缺自动化覆盖；`set -e` 下 fail-safe 易写成硬失败 | setup.sh:6 / tasks.md:8-10 |

## 二、独立 Claude 广审镜（9 findings + 6 认可，CEO/Eng/DX/Design）

| ID | 角度 | 严重度 | 问题 |
|----|------|--------|------|
| BR-1 | Eng | high | `set -e` + retire 步在 python3 present-but-nonzero 时仍中止 setup（尤其 pull→setup 窗口：新 setup.sh 调旧 init.py→argparse 拒 retire-hooks→非零→set -e 中止）；`if`-guard 不够，then-body 仍受 set -e。修：`{ … ; } \|\| echo` 吞非零 |
| BR-2 | Eng | high | navigate 吞 fetch 错、成功/失败都返 undefined → bootstrap 收不到 404 信号。Q3 需 navigate 返 success bool（契约变更，牵连 onLinkClick@246 + popstate@252 须复审）或 probe-fetch——均不止"一支"，"增量最小"低估 |
| BR-3 | Eng | medium | 首载 404 卡死属实：loadSidebar 先设 pathBar 再 throw，侧栏清空/🏠 仅在 fetch 成功后。回落须调根 bootstrap（loadSidebar('/')）非仅换 contentBody |
| BR-4 | Design/DX | medium | 404 提示无 DOM 落点：navigate 的"加载失败"先写 contentBody，根回落 loadDoc('/INDEX.md') 又覆盖→用户先闪"加载失败"再见 INDEX 无解释。需专用 notice 元素 |
| BR-5 | Eng | low | "复用既有同源守卫244"措辞误导：244 是内联检查非可复用函数。改"re-apply 同一 origin 检查"，bootstrap 内硬写一行表达式 |
| BR-6 | Eng | low | initialDir 是 const、喂 popstate 默认路径；折入 hash 改变 state-less popstate 导向，const 须改 computed/let，需刻意 |
| BR-7 | Eng | low | run() 早返位置载重：retire-hooks 分支须在 osroot 守卫（init.py:360 die）前，route 在 main() 或 run() 顶 |
| BR-8 | DX | low | clean 机 /sdflow-upgrade 现打印 retire 噪音；no-op 路径该静默 |
| BR-9 | CEO | medium | 最险实现活在 P3 半边：T45（P3、无 pytest）扛 navigate 契约变更（BR-2）+ 提示 UX 歧义（BR-4），T44（P2）反更安全；"最小增量"框架掩盖了低优先级功能最易静默回归 |

**认可（examined & sound）**：_home_claude CLAUDE_CONFIG_DIR 同源、write-only-if-changed 真 no-op、协议相对 `#//evil.com` 被 origin 比较正确拒、server-root 兜遍历、copy_bundle 未触无部署回归、ADR-0 + eager-retire/opt-in-ensure 不对称自洽。

## 三、跨模型收敛（高置信信号，两声独立命中同一处）

1. **set -e fail-safe**（OV-4 ∩ BR-1）→ **HIGH·必修**，Claude 补 pull→setup 窗口杀手场景。
2. **404 回落缺信号/递归**（OV-1 ∩ BR-2）→ **HIGH·必修**，navigate 错误契约须变。
3. **同源守卫归一化 pathname**（OV-3 ∩ BR-5）→ 改措辞 + 补 url.pathname 提取。
4. **history.state/popstate**（OV-2 ∩ BR-6）→ 刻意处理初始深链的 state。

## 四、进 Step3 合并池

上述 OV-1..4 + BR-1..9 全部纳入 Step3 对抗裁决与去重；4 条收敛项标高置信直采信、其余按置信分流。
