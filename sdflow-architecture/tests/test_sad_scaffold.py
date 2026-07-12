import subprocess, sys, pathlib
SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "sad_scaffold.py"

def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT)] + args,
                          capture_output=True, text=True, cwd=cwd)

def make_repo(tmp_path, with_openspec=True):
    if with_openspec:
        (tmp_path / "openspec" / "changes").mkdir(parents=True)
        (tmp_path / "openspec" / "specs").mkdir(parents=True)
    return tmp_path

def test_preflight_no_openspec_fail_closed(tmp_path):
    r = run(["init", "--root", str(make_repo(tmp_path, with_openspec=False))], tmp_path)
    assert r.returncode == 3 and "sdflow-init" in r.stderr   # 指引含完整入口，不自造布局
    assert not (tmp_path / "openspec").exists()

def test_preflight_level2_first_create(tmp_path):
    repo = make_repo(tmp_path)
    r = run(["init", "--root", str(repo)], tmp_path)
    assert r.returncode == 0 and "首次创建" in (r.stdout + r.stderr)
    assert (repo / "openspec" / "adr").is_dir()
    assert "## Language" in (repo / "openspec" / "CONTEXT.md").read_text(encoding="utf-8")
    sad = (repo / "openspec" / "architecture" / "sad.md").read_text(encoding="utf-8")
    assert "sad_status: draft" in sad
    log = (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")
    assert "init" in log

def test_singleton_no_silent_overwrite(tmp_path):
    repo = make_repo(tmp_path)
    run(["init", "--root", str(repo)], tmp_path)
    marked = repo / "openspec" / "architecture" / "sad.md"
    marked.write_text(marked.read_text(encoding="utf-8") + "\n定制内容\n", encoding="utf-8")
    r = run(["init", "--root", str(repo)], tmp_path)
    assert r.returncode == 4 and "continue" in r.stderr and "replan" in r.stderr
    assert "定制内容" in marked.read_text(encoding="utf-8")      # 未被覆盖
    r2 = run(["init", "--root", str(repo), "--on-exists", "continue"], tmp_path)
    assert r2.returncode == 0 and "定制内容" in marked.read_text(encoding="utf-8")
    r3 = run(["init", "--root", str(repo), "--on-exists", "replan", "--reason", "方向推翻"], tmp_path)
    assert r3.returncode == 0 and "定制内容" not in marked.read_text(encoding="utf-8")
    assert "replan" in (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")

def test_log_append_only_bytes(tmp_path):
    repo = make_repo(tmp_path)
    run(["init", "--root", str(repo)], tmp_path)
    logp = repo / "openspec" / "architecture" / "sad-log.md"
    before = logp.read_bytes()
    r = run(["log", "--root", str(repo), "--line", "step=2 reached"], tmp_path)
    assert r.returncode == 0
    after = logp.read_bytes()
    assert after[:len(before)] == before and b"step=2 reached" in after

def test_atomic_no_temp_residue(tmp_path):
    repo = make_repo(tmp_path)
    run(["init", "--root", str(repo)], tmp_path)
    assert not list((repo / "openspec" / "architecture").glob("*.tmp*"))
