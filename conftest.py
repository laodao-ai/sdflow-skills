"""仓根唯一一份 pytest conftest —— 只承载全仓通用的 cwd 副作用回归断言。

范围声明（ADR-3 / D6，改动前先读）：

- 本文件的**唯一职责**是「禁止测试用例在当前工作目录新增顶层条目」。
  MUST NOT 往这里塞任何其他共享 fixture / 插件 / 配置——各 skill 的共享 fixture
  归各自 `<skill>/tests/conftest.py`（如 `sdflow-issues/tests/conftest.py` 的
  argv 分派工厂）。本文件一旦变成公共杂物间，就会成为一个无人守护的耦合点。
- 本文件是**单一份**。MUST NOT 在各 skill 的 `tests/` 下复制同款副本：
  重复副本不在 `determinism-guards` 的 AST 镜像 roster 内，无守护即会漂移，
  而「镜像 + 漂移」正是 harden-repo-root-fail-closed 这个 change 要铲除的类别。
  pytest 沿测试文件的祖先目录收集 conftest ⇒ 仓根一份天然覆盖全部 skill + hack，
  无需任何 skill 自行注册。**该覆盖依赖仓根 `pytest.ini` 把 rootdir 钉在仓根**
  （confcutdir 默认 = rootdir；无 ini 时从仓外跑 rootdir 会塌缩到 `<skill>/tests`，
  本文件根本不会被收集）——两个文件是一套，别只留其一。

契约边界（守得住什么 / 守不住什么，诚实声明）：

- ✅ 守得住：用例的 setup / call / teardown 三阶段中，快照目录的**顶层条目集**
  不得新增条目；新增即失败并报出条目名与所在目录。
- ❌ 守不住：既存文件**内容**被改写；条目被**删除**；快照目录**子目录内部**的新增
  （只要顶层没冒出新名字）。这些面无确定性的通用判据，不在本断言的口径内。
- ❌ 守不住：用例内部 fork 出的**非阻塞**子进程在阶段边界之后才落盘。
  （实测前提：仓内子进程调用均为阻塞式 `subprocess.run`，且 `pytest-xdist` 未安装。）
- ⚠️ 用例**自身已失败**时本断言主动让路，不覆盖真正的失败原因（此时泄漏不另行报告）。

写测试时的配套纪律：用例内改工作目录 MUST 用 `monkeypatch.chdir(...)`，
禁裸 `os.chdir(...)` —— 后者不会在用例结束时自动还原，会把泄漏记到下一个用例头上。
"""

import os

import pytest

# 环境噪声豁免清单 —— MUST 保持**显式枚举**，不靠「碰巧没生成」蒙混。
# 这些条目由 pytest / 解释器 / 操作系统自己产出，与被测代码的落盘行为无关。
_CWD_LEAK_EXEMPT = frozenset(
    {
        ".pytest_cache",  # pytest 自身的缓存目录
        "__pycache__",  # CPython 字节码缓存
        ".DS_Store",  # macOS Finder
        "Thumbs.db",  # Windows 资源管理器
        "desktop.ini",  # Windows 资源管理器
    }
)

_BASELINE_ATTR = "_sdflow_cwd_leak_baseline"


def _cwd_entries(path):
    """返回 path 下的顶层条目集；path 已不可读（如被用例删除）时返回 None。"""
    try:
        return {name for name in os.listdir(path) if name not in _CWD_LEAK_EXEMPT}
    except OSError:
        return None


def _snapshot(item):
    """记录基线：(工作目录, 顶层条目集)。取不到 cwd 时记 None，后续检查一律放行。"""
    try:
        origin = os.getcwd()
    except OSError:
        setattr(item, _BASELINE_ATTR, None)
        return
    setattr(item, _BASELINE_ATTR, (origin, _cwd_entries(origin)))


def _check(item):
    """与基线比对；有新增条目则抛 AssertionError。比对后把基线推进到当前状态，

    使同一用例的后续阶段不再重复报告同一批条目。
    """
    baseline = getattr(item, _BASELINE_ATTR, None)
    if baseline is None:
        return
    origin, before = baseline
    if before is None:
        return

    after = _cwd_entries(origin)
    if after is None:
        # 用例把工作目录本身删了（repo_root 的 "cwd 被删除" 负例就是这么造的）——
        # 没有新增条目可言，不是本断言要拦的形状。
        setattr(item, _BASELINE_ATTR, None)
        return

    setattr(item, _BASELINE_ATTR, (origin, after))
    leaked = sorted(after - before)
    if leaked:
        raise AssertionError(
            "测试用例在工作目录留下了新增顶层条目（一切落盘物应位于 tmp_path 等 "
            "pytest 托管路径下）:\n"
            "  工作目录: {}\n"
            "  新增条目: {}".format(origin, ", ".join(leaked))
        )


# 基线在 setup **之前**取、在 call 与 teardown 之后各查一次：
# 前者让 fixture setup 阶段的泄漏也落进口径，后者覆盖 fixture teardown 阶段。
# 之所以在 call 阶段查（而不是只在 teardown 查完事）：teardown 里抛异常，pytest 会把
# 用例记成「passed + teardown error」，摘要行赫然写着 `1 passed`——泄漏被降级成脚注。
# 包 call 阶段则是货真价实的 `1 failed`，归属就是那个用例。


@pytest.hookimpl(wrapper=True)
def pytest_runtest_setup(item):
    _snapshot(item)
    return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    result = yield  # 用例自身失败时异常在此抛出 —— 不拦，让真正的原因浮上去
    _check(item)
    return result


@pytest.hookimpl(wrapper=True)
def pytest_runtest_teardown(item, nextitem):
    result = yield
    _check(item)
    return result
