"""setup.sh 的 ~/.sdflow 建链测试。HOME/SDFLOW_HOME 全部重定向 tmp_path。"""
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path

if os.name == "nt":
    pytest.skip(
        "these setup assertions require POSIX symlink and executable-bit semantics",
        allow_module_level=True,
    )

REPO = Path(__file__).parent.parent.parent


def run_setup(tmp_path):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = dict(os.environ, HOME=bash_path(home), SDFLOW_HOME=bash_path(home / ".sdflow"))
    r = subprocess.run([bash_executable(), bash_path(REPO / "setup.sh")],
                       env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r, home / ".sdflow"


class TestInstallSdflow:
    def test_creates_canonical_symlink_and_hack_scripts(self, tmp_path):
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        link = sdflow / "workflow"
        assert link.is_symlink()
        assert link.resolve() == (REPO / "sdflow-init" / "assets" / "workflow").resolve()
        for name in ("checkpoint-commit.sh", "resolve-workflow.sh", "resolve-models.sh"):
            f = sdflow / "hack" / name
            assert f.is_file() and not f.is_symlink()      # 拷贝，非软链
            assert f.stat().st_mode & stat.S_IXUSR          # exec 位一次设好

    def test_idempotent_rerun(self, tmp_path):
        run_setup(tmp_path)
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        link = sdflow / "workflow"
        assert link.is_symlink()
        assert link.resolve() == (REPO / "sdflow-init" / "assets" / "workflow").resolve()  # T13: 重跑后链目标不漂移
        for name in ("checkpoint-commit.sh", "resolve-workflow.sh", "resolve-models.sh"):   # T13: 重跑后 hack 脚本仍在
            f = sdflow / "hack" / name
            assert f.is_file() and not f.is_symlink()

    def test_foreign_real_dir_not_clobbered(self, tmp_path):
        home = tmp_path / "home"
        (home / ".sdflow" / "workflow").mkdir(parents=True)   # 异物：真实目录
        (home / ".sdflow" / "workflow" / "alien.txt").write_text("x", encoding="utf-8")
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        assert not (sdflow / "workflow").is_symlink()          # 未接管
        assert (sdflow / "workflow" / "alien.txt").exists()    # 数据未破坏
        assert "未接管" in (r.stdout + r.stderr)               # 停手告警显形

    def test_takeover_of_stale_symlink_is_visible(self, tmp_path):
        """B2-F1：既有软链目标与新目标不同时，接管须在摘要中显形（一行提示，非交互不阻断）。"""
        home = tmp_path / "home"
        (home / ".sdflow").mkdir(parents=True)
        elsewhere = tmp_path / "elsewhere-bundle"
        elsewhere.mkdir()
        (home / ".sdflow" / "workflow").symlink_to(elsewhere)
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        assert "接管：" in (r.stdout + r.stderr)
        link = sdflow / "workflow"
        assert link.is_symlink()
        assert link.resolve() == (REPO / "sdflow-init" / "assets" / "workflow").resolve()


class TestCleanupOrphansDangling:
    """0.1：尾斜杠 glob 看不见 dangling 链（POSIX 语义）——修为 find 枚举后必须能清。"""

    def test_dangling_own_link_is_cleaned(self, tmp_path):
        home = tmp_path / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        # 自属 dangling：目标路径含本仓名（basename REPO）但已不存在——模拟改名后的旧链。
        # 注意：entry_name 必须不撞真实现存 skill 名（如 "spec-review"）——否则
        # install_into（pipeline 中先于 cleanup_orphans 跑）会把它当同名活 skill 无条件
        # ln -snf 自愈修复，导致 cleanup_orphans 永远等不到它变成 "gone"，
        # 测试会因无关原因红/绿都失败，测不到本任务要修的枚举逻辑。
        (skills / "spec-review-legacy").symlink_to(REPO / "spec-review-legacy-GONE")
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        r = subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0
        assert not (skills / "spec-review-legacy").is_symlink()   # dangling 自属链被清
        assert "spec-review-legacy" in (r.stdout + r.stderr)       # cleaned orphans 榜上有名

    def test_foreign_dangling_link_is_kept(self, tmp_path):
        home = tmp_path / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "alien-skill").symlink_to("/nonexistent/other-tool/alien-skill")
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert (skills / "alien-skill").is_symlink()               # 非自属不动（红线）


def _farm_repo(tmp_path, extra_dirs):
    """可写的 REPO_DIR 替身：顶层条目全部软链回真仓，另加 `extra_dirs` 指定的真目录。
    需要它是因为 REPO_DIR 由 `dirname $0` 决定 —— 本用例要造「源目录还在、但已不是 skill」
    这个形态，不造替身就得往真仓里塞目录。"""
    farm = tmp_path / "farm-repo"
    farm.mkdir()
    for entry in REPO.iterdir():
        os.symlink(str(entry), str(farm / entry.name))
    for name, files in extra_dirs.items():
        for rel, content in files.items():
            p = farm / name / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content)
    return farm


class TestCleanupOrphansNonSkillSource:
    """清理判据 MUST 与安装判据同源（「目录含 SKILL.md」）。

    判据不对称的后果：安装看 SKILL.md、清理看目录是否存在 ⇒ **源还在、但已不是 skill** 的
    目录既不被安装、也不被清理，软链永久留在全局名册里。实例：sdflow-buglist /
    sdflow-todolist 三合一进 sdflow-issues 后 SKILL.md 已删，但残留的
    `scripts/__pycache__/*.pyc` 把目录撑着（git pull 删不掉未跟踪文件）⇒ `-d` 判「源还在」
    ⇒ 两条链在 ~/.claude/skills 与 ~/.codex/skills 各活一条。

    定点删门法：把 `cleanup_orphans` 里的 `[ ! -f "$dest/$entry_name/SKILL.md" ]` 分支删掉
    ⇒ 本用例必须红。"""

    def test_link_to_existing_but_no_longer_skill_source_is_cleaned(self, tmp_path):
        farm = _farm_repo(tmp_path, {
            # 只剩 scripts/__pycache__，无 SKILL.md —— 正是 buglist/todolist 的现场形态
            "sdflow-legacylist": {"scripts/__pycache__/legacylist.cpython-314.pyc": b"\x00compiled"},
        })
        home = tmp_path / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "sdflow-legacylist").symlink_to(farm / "sdflow-legacylist")
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))

        r = subprocess.run([bash_executable(), bash_path(farm / "setup.sh")], cwd=str(farm),
                           env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")

        assert r.returncode == 0, r.stdout + r.stderr
        assert (farm / "sdflow-legacylist").is_dir(), "源目录 MUST NOT 被碰（只清链，不删源）"
        # lexists：不跟随软链 —— 链被清才算过，链还在（哪怕悬空）就算没清。
        # 别用 Path.exists(follow_symlinks=False)：那是 3.12+ 的签名，本机系统 python 是 3.9。
        assert not os.path.lexists(str(skills / "sdflow-legacylist")), \
            "源已不是 skill（无 SKILL.md）⇒ 自属链 MUST 被清"
        assert "sdflow-legacylist" in (r.stdout + r.stderr)        # cleaned orphans 榜上有名

    def test_valid_skill_link_is_kept(self, tmp_path):
        """反向：源仍是 skill（有 SKILL.md）⇒ 一条都不许清 —— 防新判据把活链误伤。"""
        farm = _farm_repo(tmp_path, {})
        home = tmp_path / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))

        r = subprocess.run([bash_executable(), bash_path(farm / "setup.sh")], cwd=str(farm),
                           env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0, r.stdout + r.stderr
        assert (skills / "sdflow-init" / "SKILL.md").is_file()     # 真 skill 铺好了

        again = subprocess.run([bash_executable(), bash_path(farm / "setup.sh")], cwd=str(farm),
                               env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert again.returncode == 0, again.stdout + again.stderr
        assert (skills / "sdflow-init").is_symlink()               # 重跑不自伤


class TestRenameEndToEnd:
    def test_rename_scenario_old_links_cleaned_new_links_made(self, tmp_path):
        """跨改名端到端：预置 9 个指向本仓已不存在旧目录的自属链 → setup → 旧清新立。"""
        home = tmp_path / "home"; skills = home / ".claude" / "skills"; skills.mkdir(parents=True)
        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
            (skills / old).symlink_to(REPO / old)      # 改名后这些源目录已不存在 → dangling
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        r = subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
            assert not (skills / old).exists(), old     # 旧链清零
        for new in ["sdflow-init","sdflow-done","sdflow-spec-review","sdflow-code-review","sdflow-issues"]:
            assert (skills / new).is_symlink(), new     # 新链建立
        for gone in ["sdflow-buglist","sdflow-todolist"]:   # 三合一后旧目录删除：不再建链（orphan 清理）
            assert not (skills / gone).exists(), gone

    def test_layout_smoke(self, tmp_path):
        """布局冒烟：canonical 软链指向改名后的 sdflow-init/assets/workflow；hack 三脚本可执行。"""
        r, sdflow = run_setup(tmp_path)
        assert (sdflow / "workflow").resolve() == (REPO / "sdflow-init" / "assets" / "workflow").resolve()
        for s in ("checkpoint-commit.sh", "resolve-workflow.sh", "resolve-models.sh"):
            assert (sdflow / "hack" / s).stat().st_mode & stat.S_IXUSR


class TestSetEDoesNotKillTheWholeInstall:
    """🔴 `set -e` 面治（代码审 F5）：外部命令**裸调用**失败 = 整个 setup.sh 当场中止。

    后果不是「少装一个 skill」，而是**这一趟什么都没装完**：stdout 只剩一行裸 `ln:` 错误，
    没有汇总、`~/.sdflow/` 的 canonical 与 hack 脚本（resolve-models.sh / outside-voice.sh /
    checkpoint-commit.sh）全不在位 —— 而所有 sdflow skill 的第零步都依赖它们。
    `install_agents()` 早已按「失败降级为 skipped[] + 汇总」处理过同一形态，
    本类把同片的另两处（`install_into` / `install_sdflow`）钉在同一取向上。
    """

    @staticmethod
    def _skip_if_root():
        if os.geteuid() == 0:
            pytest.skip("root 无视目录写权限位 —— 这条只在非 root 下有区分力")

    def test_readonly_skills_dest_degrades_to_skip(self, tmp_path):
        """`install_into` 的 `ln` 失败 ⇒ skip + 汇总，且后续步骤照常跑完。"""
        self._skip_if_root()
        home = tmp_path / "home"
        dest = home / ".claude" / "skills"
        dest.mkdir(parents=True)
        os.chmod(dest, 0o555)
        try:
            r, sdflow = run_setup(tmp_path)
        finally:
            os.chmod(dest, 0o755)

        assert r.returncode == 0, "skills 落点只读竟中止了整个 setup.sh：\n" + r.stdout + r.stderr
        assert "skipped (" in r.stdout, "失败没进汇总 —— 只剩一行裸 ln 错误"
        assert "建不出来" in r.stdout
        assert (sdflow / "hack").is_dir(), \
            "install_sdflow 没跑到 —— 一个建不出来的软链把整条安装链带崩了"

    def test_readonly_sdflow_home_degrades_to_skip(self, tmp_path):
        """`install_sdflow` 的 `ln`/`cp`/`rm` 失败 ⇒ 同样 skip + 汇总，不中止。"""
        self._skip_if_root()
        home = tmp_path / "home"
        sdflow = home / ".sdflow"
        (sdflow / "hack").mkdir(parents=True)
        os.chmod(sdflow, 0o555)
        try:
            r, _ = run_setup(tmp_path)
        finally:
            os.chmod(sdflow, 0o755)

        assert r.returncode == 0, "~/.sdflow 只读竟中止了整个 setup.sh：\n" + r.stdout + r.stderr
        assert "skipped (" in r.stdout, "失败没进汇总 —— 只剩一行裸 ln/cp 错误"
        assert "sdflow-skills v" in r.stdout, "汇总段根本没打出来"

    def test_two_concurrent_runs_both_finish(self, tmp_path):
        """⭐ 复现（代码审 F5）：两个 setup.sh 并发铺同一个全新 HOME。

        `ln -sf` **不是单一系统调用**（内部 unlink → symlink 两步）⇒ 并发下后者 `EEXIST`。
        实测旧实现 4 轮里 2 轮命中：一个进程 `EXIT:1`，stdout 只有一行
        `ln: …: File exists`，无汇总。并发是真实场景（`/sdflow-upgrade` 与手敲 setup 撞上、
        两个 checkout 同时装）。判据：**两边都必须跑完**（失败一格 ⇒ 顶多进 skipped）。
        """
        home = tmp_path / "home"
        home.mkdir(exist_ok=True)
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        procs = [subprocess.Popen(["bash", str(REPO / "setup.sh")], env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, encoding="utf-8", errors="replace") for _ in range(2)]
        outs = [p.communicate(timeout=300)[0] for p in procs]
        for i, (p, out) in enumerate(zip(procs, outs)):
            assert p.returncode == 0, f"并发第 {i} 个进程被 set -e 打断：\n{out}"
            assert "sdflow-skills v" in out, f"并发第 {i} 个进程没走到汇总：\n{out}"


class TestResolveModelsInstallPath:
    """add-codex-host-support Task 6，dogfood 盲区守（memory dogfood-blind-spot-source-config）：
    仓内 `sdflow-init/assets/hack/resolve-models.sh` 绿 ≠ 消费仓 `~/.sdflow/hack/resolve-models.sh`
    装对——本测试跑真实 setup.sh 安装管线，再调**安装后的路径**（非仓内源路径）验证端到端可用。"""

    def test_installed_copy_at_sdflow_hack_path_resolves_correctly(self, tmp_path):
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0, r.stderr
        installed = sdflow / "hack" / "resolve-models.sh"
        assert installed.is_file() and not installed.is_symlink()   # 拷贝安装，非仓内直跑
        assert installed != (REPO / "sdflow-init" / "assets" / "hack" / "resolve-models.sh")

        # 用 --root 指向一个独立空仓（不是本仓自己）——强制走「全局 canonical」分支读
        # model-tiers.md（sdflow/workflow 软链 → 本仓 sdflow-init/assets/workflow），
        # 端到端验证安装后的 resolve-models.sh + 安装后的 sibling resolve-workflow.sh 配合可用。
        consumer_repo = tmp_path / "consumer-repo"
        (consumer_repo / "openspec").mkdir(parents=True)
        env = dict(os.environ, SDFLOW_HOME=str(sdflow))
        env.pop("CLAUDECODE", None)
        env["CODEX_THREAD_ID"] = "11111111-2222-3333-4444-555555555555"
        proc = subprocess.run(
            ["bash", str(installed), "--root", str(consumer_repo)],
            capture_output=True, text=True, env=env, timeout=15,

            encoding="utf-8",
            errors="replace",)
        assert proc.returncode == 0, proc.stderr
        assert "export SDFLOW_HOST=codex" in proc.stdout
        assert "export SDFLOW_TIER_STRONG=gpt-5.6-sol" in proc.stdout
        assert "export SDFLOW_VOICE_RUNNER=claude" in proc.stdout


OUR_NAMES = {  # RENAME-MAP 旧名∪新名∪保留名单（marker 兼容边界，D5）
    "opsx-project-init","opsx-done","opsx-maintain","opsx-roadmap-planner",
    "spec-review","impl-review","buglist-recorder","todolist-recorder","issues-recorder",
    "sdflow-init","sdflow-done","sdflow-maintain","sdflow-roadmap","sdflow-spec-review",
    "sdflow-code-review","sdflow-buglist","sdflow-todolist","sdflow-issues",
    "embedded-test-sop","openspec-upgrade","sdflow-upgrade",
}

class TestBrandAndMarkerNarrowing:
    def test_version_line_branded(self, tmp_path):
        r, _ = run_setup(tmp_path)          # 复用本文件既有 helper
        # 版号真相源 = git 自报（本仓无 VERSION 文件——手工版号必然过期）。
        # 期望值在这里独立算一遍，守两件事：品牌前缀不变、版本确实来自 git describe。
        ver = subprocess.run(
            ["git", "-C", str(REPO), "describe", "--tags", "--always", "--dirty"],
            capture_output=True, text=True,

            encoding="utf-8",
            errors="replace",).stdout.strip()
        assert ver, "git describe 无输出——测试环境不是 git checkout？"
        assert f"sdflow-skills {ver} ready" in r.stdout

    # OUR_NAMES 三分：旧名（源目录已不存在，需从仓内动态判）/ 现存名（源目录仍在仓内）。
    # 别硬编码两份清单——用 (REPO/name/"SKILL.md").is_file() 派生，避免与仓内实际布局漂移。
    _EXISTING_NAMES = sorted(n for n in OUR_NAMES if (REPO / n / "SKILL.md").is_file())
    _GONE_NAMES = sorted(OUR_NAMES - set(_EXISTING_NAMES))

    def test_legacy_marker_recognized_only_for_our_names(self, tmp_path):
        """21 名单全量接线 + 1 个名单外对照，跑一次 setup，分三类断言。"""
        home = tmp_path / "home"; skills = home / ".claude" / "skills"; skills.mkdir(parents=True)
        all_names = list(OUR_NAMES) + ["bilibili-research"]
        for name in all_names:
            d = skills / name; d.mkdir(); (d / "SKILL.md").write_text("x", encoding="utf-8")
            (d / ".laodao-skills").write_text("legacyhash", encoding="utf-8")
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        r = subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0

        # 旧名（源目录已不存在）：is_our_marker_copy 识别自属 → install_into 因无同名源
        # 不会重建软链，交由 cleanup_orphans 按孤儿清理规则移除（旧链消失，符合 spec.md
        # 「跨改名孤儿链真实可清」场景与 design.md no-stub 拍板；MUST NOT 因不在名单而被
        # 当异物保留/误删判定错向）
        for name in self._GONE_NAMES:
            assert not (skills / name).exists(), name

        # 现存名（9 新名 + openspec-upgrade/sdflow-upgrade，源仍在仓内；embedded-test-sop
        # 已随 simplify-workflow 删除仓内源目录，落入上面的 _GONE_NAMES 桶）：
        # 识别自属 → 刷新换链为指向仓内源目录的软链
        for name in self._EXISTING_NAMES:
            assert (skills / name).is_symlink(), name

        # 名单外（bilibili-research 是 laodao misc 财产）：skip 不动，仍是带旧 marker 的真实目录
        alien = skills / "bilibili-research"
        assert alien.is_dir() and not alien.is_symlink()
        assert (alien / ".laodao-skills").exists()


# ══════════════════════════════════════════════════════════════════════════════
# 同代 capability 安装快照（enable-codex-background-outside-voice Task 5）
#
# 【为什么必须在这一层测】memory「dogfood 盲区：源仓 config 掩盖消费仓默认态」——
# 仓内 `sdflow-init/tests/` 用 `JOB.write_manifest(tmp)` 造出来的「已安装形态」永远绿，
# 而真实消费者读的是 `~/.sdflow/hack/`：setup.sh 若不装 `*.py`、不写 manifest，
# **真实安装态的 preflight 必红**（helper 缺失 / manifest 缺失都 fail-closed）。
# ∴ 锚必须打在「真跑一次 setup.sh 之后的那个目录」上。
# ══════════════════════════════════════════════════════════════════════════════

import importlib.util  # noqa: E402

_JOB_PY = REPO / "sdflow-init" / "assets" / "hack" / "outside-voice-job.py"
_SPEC = importlib.util.spec_from_file_location("sdflow_ov_job_for_setup_tests", _JOB_PY)
JOB = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(JOB)


class TestCapabilitySnapshot:
    def test_installs_job_helper_with_exec_bit_and_python3_interpreter(self, tmp_path):
        """job helper 是 `claude --bg --exec` 之外的**另一个执行面**：装漏 = 整条后台通道死。"""
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0, r.stderr
        installed = sdflow / "hack" / "outside-voice-job.py"
        assert installed.is_file() and not installed.is_symlink()      # 拷贝安装，非仓内直跑
        assert installed.stat().st_mode & stat.S_IXUSR                 # exec 位一次设好
        first = installed.read_text(encoding="utf-8").splitlines()[0]
        assert first.startswith("#!") and "python3" in first           # 解释器正确

    def test_writes_a_capability_manifest_that_verifies_against_installed_bytes(self, tmp_path):
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0, r.stderr
        hack = sdflow / "hack"
        manifest = hack / JOB.MANIFEST_NAME
        assert manifest.is_file(), "setup.sh 未写 capability manifest ⇒ 安装态 preflight 必红"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert sorted(data["entries"]) == sorted(JOB.MANIFEST_ENTRIES)
        for name, digest in data["entries"].items():
            assert digest == JOB.sha256_file(str(hack / name)), name
        assert JOB.verify_manifest(hack)["ok"] is True

    def test_rerun_keeps_the_snapshot_consistent(self, tmp_path):
        run_setup(tmp_path)
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0, r.stderr
        assert JOB.verify_manifest(sdflow / "hack")["ok"] is True

    def test_hand_mutated_install_is_skew_and_fails_closed(self, tmp_path):
        """新旧混配 / stale copy：任一成员与快照不符即红（正是 preflight 的 fail-closed 判据）。"""
        r, sdflow = run_setup(tmp_path)
        hack = sdflow / "hack"
        (hack / "outside-voice.sh").write_text("# stale copy\n", encoding="utf-8")
        verdict = JOB.verify_manifest(hack)
        assert verdict["ok"] is False
        assert "outside-voice.sh" in verdict["detail"]
        assert "setup.sh" in verdict["hint"]                   # 刷新指引可执行

    def test_rerun_heals_a_stale_copy(self, tmp_path):
        """对照组：上一条的红确实来自 skew —— 重跑 setup.sh 即恢复绿。"""
        r, sdflow = run_setup(tmp_path)
        (sdflow / "hack" / "outside-voice.sh").write_text("# stale copy\n", encoding="utf-8")
        assert JOB.verify_manifest(sdflow / "hack")["ok"] is False
        r2, _ = run_setup(tmp_path)
        assert r2.returncode == 0, r2.stderr
        assert JOB.verify_manifest(sdflow / "hack")["ok"] is True

    def test_interrupted_install_leaves_no_consistent_snapshot(self, tmp_path):
        """成员没装上 ⇒ MUST NOT 留下 / 写出一份「自洽但陈旧」的 manifest。

        制造真实失败：把已安装的 shell helper 置为只读 ⇒ 下一次 `cp` 失败。
        此时 manifest MUST 不在场（安装步先删后写、且**本趟不补写**），于是 preflight
        fail-closed，而不是拿着一份给「新旧混装现场」签的名声称快照一致。

        ⚠️ **判据是「manifest 不在场」，不是「setup 非零退出」**〔F5 · impl-review-fix〕：
        cp 失败已按全文取向降级为 skipped + 汇总（裸调用会把整条安装链带崩，
        连 canonical 与其余 hack 脚本都装不上）。若只把「中止」当判据，这条门在降级后
        就变成了**恒红**；真正承重的不变量是下面两条 —— manifest 不在 + verify 判红。
        补一条正向断言：失败必须**可见**（进 skipped 汇总），MUST NOT 静默跳过。
        """
        r, sdflow = run_setup(tmp_path)
        assert JOB.verify_manifest(sdflow / "hack")["ok"] is True
        victim = sdflow / "hack" / "outside-voice.sh"
        victim.chmod(0o444)
        try:
            r2, _ = run_setup(tmp_path)
            assert "outside-voice.sh" in r2.stdout and "未安装" in r2.stdout, \
                "cp 到只读目标未失败、或失败没进汇总 ⇒ 本用例未制造出中断：\n" + r2.stdout
            assert not (sdflow / "hack" / JOB.MANIFEST_NAME).exists(), \
                "成员没装上却仍写/留了 manifest ⇒ 新旧混装的现场被签成一致"
            assert JOB.verify_manifest(sdflow / "hack")["ok"] is False
        finally:
            victim.chmod(0o755)
