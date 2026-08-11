"""sdflow-upstream-watch 机械层——四源上游追踪的 collect/advance 双子命令。

Task 1（脚手架阶段）范围：cwd 守卫（proposal A4）+ anchors.yaml 三态读写层
（mikefarah-flavor yq idiom，同 `sdflow-retro/scripts/retro_report.py` 的 `_yq` 各自实现、
不跨目录 import）+ 外部子进程统一超时常量 + collect/advance 子命令骨架。

Task 2（本阶段）范围：四源采集器（gstack / matt / superpowers / openspec）+ facts JSON 输出 +
`advance` 报告+facts 双参数绑定门。零解析上游内容——delta 事实全部由 git / npm / sha256
自己回答（design.md 基准 5）；采集失败按源降级、fail-loud、不互相传染。

本脚本 MUST 从 sdflow-skills 仓内某处运行（cwd 守卫据此判定，不限定必须是仓根——
`guard_cwd()` 用 `git rev-parse --show-toplevel` 解析真实仓根，供调用方定位
`openspec/upstream/` 等数据路径，避免子目录 cwd 下的相对路径踩空）。
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

# 【外部子进程统一超时常量】单点定义（design.md TD1）：全部子进程调用（git / yq / npm）
# 共用同一超时值，超时按该源 degraded 处置。
SUBPROCESS_TIMEOUT_SECONDS = 60

# 【cwd 守卫锚定值】proposal A4：本 skill 语义单仓专用，硬编码指向本仓 remote。
EXPECTED_REMOTE_SUBSTR = "laodao-ai/sdflow-skills"

# 【anchors.yaml 数据模型常量】design.md「数据模型」段。
SCHEMA_VERSION = 1
DEFAULT_REMIND_AFTER_DAYS = 30

# 【四源上游 URL】design.md 数据模型段实查坐实（decision-memo C1/C3）。gstack 不需要独立
# 常量——它复用本地 checkout 既有的 `origin` remote，不在此处硬编码。
MATT_UPSTREAM_URL = "https://github.com/mattpocock/skills.git"
SUPERPOWERS_MARKETPLACE_URL = "https://github.com/anthropics/claude-plugins-official.git"
OPENSPEC_NPM_PACKAGE = "@fission-ai/openspec"
MARKETPLACE_JSON_PATH = ".claude-plugin/marketplace.json"


class CwdGuardError(Exception):
    """cwd 非 sdflow-skills 仓（proposal A4）——fail-loud，调用方 MUST NOT 写任何文件。"""


class AnchorsError(Exception):
    """anchors.yaml 不可解析 / yq 不可用 / yq 非 mikefarah 家族——fail-loud 硬停，
    MUST NOT 按"无锚"猜测续跑（区别于"文件缺失=首轮初始化"这一正常状态）。"""


class CollectError(Exception):
    """单源采集失败（上游不可达 / 本地锚源缺失 / 格式漂移 / 锚失效）——调用方捕获后
    转为该源 degraded 记录，MUST NOT 向上传染到其余源（design.md 失败模式表）。"""


class AdvanceGateError(Exception):
    """advance 报告+facts 双参数前置校验失败——拒绝推进，anchors.yaml 内容不变
    （spec Requirement「锚文件由脚本独占维护，锚推进与本轮报告 + facts 绑定」）。"""


def _tildify(path):
    """[impl-review-fix] 错误消息路径脱敏：把 home 目录前缀替换为 `~`，避免报告/日志文本
    中泄露包含用户名的本机绝对路径。纯字符串替换，不做存在性校验、不影响实际路径解析。"""
    return str(path).replace(str(Path.home()), "~", 1)


def _run(cmd, *, input=None):
    """全仓外部子进程统一入口：带 `SUBPROCESS_TIMEOUT_SECONDS` 超时。
    调用方按返回值 `returncode` 自行判定，超时以 `subprocess.TimeoutExpired` 抛出
    （由调用方按"该源 degraded"处置，Task 2 消费）。"""
    return subprocess.run(
        cmd, input=input, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )


def guard_cwd():
    """cwd 守卫（proposal A4）：确认调用者的 cwd 位于 sdflow-skills 仓（git remote 判定），
    非本仓时 fail-loud（抛 `CwdGuardError`），调用方 MUST NOT 在守卫失败后写任何文件。

    返回解析出的仓根绝对路径（`git rev-parse --show-toplevel`），供调用方定位
    `openspec/upstream/` 等数据路径——不假定 cwd 本身就是仓根，只要求 cwd 位于该仓内
    （标准 git 行为：命令向上查找 .git）。
    """
    try:
        toplevel = _run(["git", "rev-parse", "--show-toplevel"])
    except (OSError, subprocess.TimeoutExpired) as e:
        raise CwdGuardError(
            f"cwd 不在任何可探测的 git 仓库内（cwd={Path.cwd()}）：{e}。"
            f"本 skill 仅服务 {EXPECTED_REMOTE_SUBSTR} 工具链自身。"
        ) from e
    if toplevel.returncode != 0:
        raise CwdGuardError(
            f"cwd 不在任何 git 仓库内（cwd={Path.cwd()}）。"
            f"本 skill 仅服务 {EXPECTED_REMOTE_SUBSTR} 工具链自身。"
        )
    root = Path(toplevel.stdout.strip())

    try:
        remote = _run(["git", "-C", str(root), "remote", "get-url", "origin"])
    except (OSError, subprocess.TimeoutExpired) as e:
        raise CwdGuardError(
            f"读取 {root} 的 git remote 失败：{e}。"
            f"本 skill 仅服务 {EXPECTED_REMOTE_SUBSTR} 工具链自身。"
        ) from e
    if remote.returncode != 0 or EXPECTED_REMOTE_SUBSTR not in remote.stdout:
        raise CwdGuardError(
            f"本 skill 仅服务 {EXPECTED_REMOTE_SUBSTR} 工具链自身"
            f"（cwd={Path.cwd()} 所在仓 {root} 的 origin remote 非该仓）。"
        )
    return root


def _resolve_yq():
    """探测 mikefarah/yq 二进制。同 `retro_report._yq` idiom 各自实现（不跨目录 import）。
    非 mikefarah 家族（如 kislyuk/yq）直接报错阻止误用。

    不做进程内缓存（与 retro_report 的模块级缓存不同）：本工具每轮调用次数是个位数
    （≤4 源 × 1-2 次 anchors 读写），缓存收益可忽略，无缓存换来测试可独立控制每次探测结果，
    不需要在测试间手动重置模块私有状态（基准 4：不为低概率/低收益的优化增加耦合）。
    """
    yq = shutil.which("yq")
    if not yq:
        raise AnchorsError(
            "yq 未安装。安装方式：\n"
            "  macOS:   brew install yq\n"
            "  Windows: winget install --id MikeFarah.yq\n"
            "  Linux:   snap install yq"
        )
    vr = _run([yq, "--version"])
    if "mikefarah" not in vr.stdout:
        raise AnchorsError(
            "检测到的 yq 不是 mikefarah/yq（可能是 kislyuk/yq）。请卸载后安装正确版本："
            "macOS: brew install yq / Windows: winget install --id MikeFarah.yq / "
            "Linux: snap install yq"
        )
    return yq


def _yq_read(expression, file, *, default=None):
    """yq(mikefarah) 读取子进程薄封装（同 retro_report._yq idiom）。
    exit≠0（文件不可读/解析失败）MUST raise AnchorsError，不吞；
    「键不存在」（exit 0 + stdout=null）走 default，两条分支不可混同。"""
    yq = _resolve_yq()
    r = _run([yq, "-o", "json", expression, str(file)])
    if r.returncode != 0:
        raise AnchorsError(f"yq failed on {file}: {r.stderr.strip()}")
    raw = r.stdout.strip()
    if not raw or raw == "null":
        return default
    return json.loads(raw)


def load_anchors(path):
    """anchors.yaml 三态读取（R1 / TD4）：
    ①文件缺失 → 返回默认骨架（首轮初始化语义，非错误，不触发 yq）；
    ②文件存在但 yq 解析失败（含非 mikefarah / 未安装）→ `AnchorsError` fail-loud 硬停；
    ③文件存在且可解析 → 返回结构化 dict；某源字段缺失由 `get_source_anchor` 判"该源无锚"。
    """
    path = Path(path)
    if not path.is_file():
        return {
            "schema_version": SCHEMA_VERSION,
            "last_run": None,
            "remind_after_days": DEFAULT_REMIND_AFTER_DAYS,
            "sources": {},
        }
    data = _yq_read(".", path, default=None)
    if not isinstance(data, dict):
        raise AnchorsError(f"anchors.yaml 解析结果非法（须为映射）：{path}")
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("remind_after_days", DEFAULT_REMIND_AFTER_DAYS)
    data.setdefault("sources", {})
    return data


def get_source_anchor(anchors, source):
    """取某源的锚记录；该源不存在或记录为空 → None（"值缺失=该源视为无锚首轮"，R1）。"""
    sources = anchors.get("sources") or {}
    return sources.get(source) or None


def write_anchors(path, anchors):
    """整份覆盖写 anchors.yaml（脚本独占维护，R1）。走 yq：JSON（Python dict 天然产出）是
    合法 YAML 1.2 子集，mikefarah yq 可直接把它当 YAML 输入重新格式化输出——机械转换，
    不手写 YAML 序列化字符串（基准 5 同款零解析/零手搓纪律）。"""
    yq = _resolve_yq()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    r = _run([yq, "-o=yaml", "-P", ".", "-"], input=json.dumps(anchors))
    if r.returncode != 0:
        raise AnchorsError(f"yq 写 anchors.yaml 失败：{r.stderr.strip()}")
    path.write_text(r.stdout, encoding="utf-8")


# ============================ 通用 git 子进程小工具 ============================

def _rev_parse(repo_dir, ref):
    """解析 `ref` 为完整 sha；失败（ref 不存在 / repo 不可读）→ CollectError。"""
    r = _run(["git", "-C", str(repo_dir), "rev-parse", ref])
    if r.returncode != 0:
        raise CollectError(f"无法解析 {ref}（{repo_dir}）: {r.stderr.strip()}")
    return r.stdout.strip()


def _assert_is_ancestor(repo_dir, anchor_sha, head_sha):
    """`merge-base --is-ancestor`：锚非 head 祖先（上游历史被重写）→ CollectError
    「锚失效」（design.md TD2 + 失败模式表，防 exit 0 假成功）。"""
    r = _run(["git", "-C", str(repo_dir), "merge-base", "--is-ancestor", anchor_sha, head_sha])
    if r.returncode != 0:
        raise CollectError("上游历史疑似被重写，锚失效")


def _git_log_delta(repo_dir, anchor_sha, head_sha, *, path_filter=None, reverse=False):
    """`git log <anchor>..<head>` 的零解析结构化提取：commits（sha+subject，用可控的
    `--pretty` 格式串，非手搓上游内容解析）+ changed_paths（`--name-only` 全路径去重）。
    `path_filter` 给定时只返回 commits（changed_paths 恒为空，调用方不需要）。"""
    range_arg = f"{anchor_sha}..{head_sha}"
    cmd = ["git", "-C", str(repo_dir), "log", "--pretty=format:%H%x09%s"]
    if reverse:
        cmd.append("--reverse")
    cmd.append(range_arg)
    if path_filter:
        cmd += ["--", path_filter]
    r = _run(cmd)
    if r.returncode != 0:
        raise CollectError(f"git log 失败（{repo_dir}）: {r.stderr.strip()}")
    commits = []
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\t")
        commits.append({"sha": sha, "subject": subject})

    if path_filter:
        return commits, []

    cmd2 = ["git", "-C", str(repo_dir), "log", "--name-only", "--pretty=format:", range_arg]
    r2 = _run(cmd2)
    if r2.returncode != 0:
        raise CollectError(f"git log --name-only 失败（{repo_dir}）: {r2.stderr.strip()}")
    paths = {line.strip() for line in r2.stdout.splitlines() if line.strip()}
    return commits, sorted(paths)


def _ensure_bare_cache(cache_dir, upstream_url):
    """matt / superpowers 共用的 blobless bare 缓存层（design.md TD2）：已存在则 fetch
    （显式 refspec 更新本地 `refs/heads/*`，使裸仓 HEAD 语义可用——plain `fetch` 只落
    FETCH_HEAD、不会前移本地分支引用，验证见本票 impl-report 附实测）；fetch 失败 →
    删缓存重 clone 一次自愈，再失败才 CollectError（degraded，原因文案带缓存路径）。"""
    cache_dir = Path(cache_dir)
    if cache_dir.is_dir():
        r = _run(["git", "-C", str(cache_dir), "fetch", "origin", "+refs/heads/*:refs/heads/*"])
        if r.returncode == 0:
            return cache_dir
        shutil.rmtree(cache_dir, ignore_errors=True)
    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    r = _run(["git", "clone", "--filter=blob:none", "--bare", upstream_url, str(cache_dir)])
    if r.returncode != 0:
        # [impl-review-fix] 路径脱敏
        raise CollectError(f"bare 缓存 clone 失败（缓存路径 {_tildify(cache_dir)}）: {r.stderr.strip()}")
    return cache_dir


# ============================ gstack 采集器 ============================

def collect_gstack(anchor, *, checkout_dir):
    """既有本地 checkout：`fetch origin` + `merge-base --is-ancestor` 锚祖先守卫 +
    `log --name-only 锚..FETCH_HEAD`。checkout 缺失 → degraded。首轮（无持久锚）以本地
    checkout 现有 HEAD 为天然锚，出真 delta（design.md 失败模式表「首轮初始化」的 gstack 分支）。
    """
    checkout_dir = Path(checkout_dir)
    if not (checkout_dir / ".git").exists():
        raise CollectError(f"本地 checkout 不存在: {_tildify(checkout_dir)}")  # [impl-review-fix]

    fr = _run(["git", "-C", str(checkout_dir), "fetch", "origin"])
    if fr.returncode != 0:
        raise CollectError(f"fetch 失败（{checkout_dir}）: {fr.stderr.strip()}")

    head_sha = _rev_parse(checkout_dir, "FETCH_HEAD")
    anchor_sha = (anchor or {}).get("anchor_sha")
    if anchor_sha is None:
        anchor_sha = _rev_parse(checkout_dir, "HEAD")

    _assert_is_ancestor(checkout_dir, anchor_sha, head_sha)
    commits, changed_paths = _git_log_delta(checkout_dir, anchor_sha, head_sha)
    return {"status": "ok", "head_sha": head_sha, "commits": commits, "changed_paths": changed_paths}


# ============================ matt 采集器（bare 缓存 + .skill-lock.json 辅助）========

def _read_matt_installed_skills(skill_lock_path):
    """`.skill-lock.json` 键路径断言（仅校验 `source == mattpocock/skills` 的条目——
    其余来源的 skill 不是本采集器的断言目标，避免误报格式漂移）。文件缺失 = 无辅助信息，
    非错误（R2「本地锚源缺失」与「格式漂移」是两条不同分支，此处只有后者才 degrade）。"""
    skill_lock_path = Path(skill_lock_path)
    if not skill_lock_path.is_file():
        return {}
    try:
        data = json.loads(skill_lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise CollectError(f"格式漂移: 无法解析 {_tildify(skill_lock_path)}: {e}")  # [impl-review-fix]
    skills = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(skills, dict):
        raise CollectError(f"格式漂移: {_tildify(skill_lock_path)} 缺少 skills 映射")  # [impl-review-fix]
    result = {}
    for name, entry in skills.items():
        if not isinstance(entry, dict):
            raise CollectError(f"格式漂移: {_tildify(skill_lock_path)} 的 {name} 条目非法")  # [impl-review-fix]
        if entry.get("source") != "mattpocock/skills":
            continue
        if "skillFolderHash" not in entry:
            # [impl-review-fix] 路径脱敏
            raise CollectError(f"格式漂移: {_tildify(skill_lock_path)} 的 {name} 缺少 skillFolderHash 键")
        result[name] = entry["skillFolderHash"]
    return result


def collect_matt(anchor, *, cache_dir, skill_lock_path, upstream_url=MATT_UPSTREAM_URL):
    """bare 缓存（`log --name-only 锚..HEAD`）+ `.skill-lock.json` 辅助信息。无持久锚
    （首轮）→ 「无锚 ⇒ 当前上游态即基线」零 delta（design.md 失败模式表）。"""
    installed_skills = _read_matt_installed_skills(skill_lock_path)  # 键路径断言失败即抛出

    cache_dir = _ensure_bare_cache(cache_dir, upstream_url)
    head_sha = _rev_parse(cache_dir, "HEAD")
    anchor_sha = (anchor or {}).get("anchor_sha")
    if anchor_sha is not None:
        _assert_is_ancestor(cache_dir, anchor_sha, head_sha)
        commits, changed_paths = _git_log_delta(cache_dir, anchor_sha, head_sha)
    else:
        commits, changed_paths = [], []

    result = {"status": "ok", "head_sha": head_sha, "commits": commits, "changed_paths": changed_paths}
    if installed_skills:
        result["installed_skills"] = installed_skills
    return result


# ============================ superpowers 采集器（marketplace source.sha 追踪）======

def _version_sort_key(version):
    """宽松版本排序键（基准 4：不为「无 scope=user 记录时的次要 tie-break」手搓完整
    semver）——数字段按数值比较，非数字段按字符串比较，对本仓实查到的 `X.Y.Z` 与
    短 sha 两种版本形状均可确定性排序。"""
    parts = []
    for token in str(version).replace("-", ".").split("."):
        parts.append((0, int(token)) if token.isdigit() else (1, token))
    return parts


def _read_superpowers_installed_version(installed_plugins_path):
    """`installed_plugins.json`（per-plugin 多记录数组）键路径断言 + 取值策略：
    优先 `scope=user` 记录，无则取版本最大者（design.md 数据模型段 + spec 多 scope Scenario）。
    """
    installed_plugins_path = Path(installed_plugins_path)
    if not installed_plugins_path.is_file():
        raise CollectError(f"本地锚源缺失: {_tildify(installed_plugins_path)}")  # [impl-review-fix]
    try:
        data = json.loads(installed_plugins_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        # [impl-review-fix] 路径脱敏
        raise CollectError(f"格式漂移: 无法解析 {_tildify(installed_plugins_path)}: {e}")

    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        # [impl-review-fix] 路径脱敏
        raise CollectError(f"格式漂移: {_tildify(installed_plugins_path)} 缺少 plugins 映射")

    records = None
    for key, val in plugins.items():
        if key.split("@", 1)[0] == "superpowers":
            records = val
            break
    if records is None:
        raise CollectError(f"本地锚源缺失: installed_plugins.json 中无 superpowers 记录")
    if not isinstance(records, list) or not records:
        raise CollectError(f"格式漂移: superpowers 记录不是非空数组")

    user_records = [r for r in records if isinstance(r, dict) and r.get("scope") == "user"]
    chosen = user_records[0] if user_records else max(
        records, key=lambda r: _version_sort_key(r.get("version", "")) if isinstance(r, dict) else []
    )
    if not isinstance(chosen, dict) or "version" not in chosen:
        raise CollectError(f"格式漂移: superpowers 记录缺少 version 键")
    version = chosen["version"]
    if not isinstance(version, str) or not version:
        raise CollectError("格式漂移: superpowers version 字段非法")
    return version


def _extract_superpowers_source_sha(marketplace_json_text):
    """从某一版本的 `marketplace.json` 全文中零解析式提取 superpowers 条目的
    `source.sha` 字段（有界 JSON 字段读取，非手搓上游格式解析——基准 5）。"""
    try:
        data = json.loads(marketplace_json_text)
    except json.JSONDecodeError as e:
        raise CollectError(f"marketplace.json 解析失败: {e}")
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, list):
        raise CollectError("marketplace.json 缺少 plugins 数组")
    for entry in plugins:
        if isinstance(entry, dict) and entry.get("name") == "superpowers":
            source = entry.get("source")
            if isinstance(source, dict) and "sha" in source:
                return source["sha"]
            raise CollectError("marketplace.json superpowers 条目缺少 source.sha 字段")
    raise CollectError("marketplace.json 中未找到 superpowers 条目")


def collect_superpowers(anchor, *, cache_dir, installed_plugins_path,
                         upstream_url=SUPERPOWERS_MARKETPLACE_URL):
    """marketplace 仓不 vendor 插件内容（`plugins/superpowers` 路径不存在，双对抗镜实查
    坐实）⇒ MUST NOT 路径过滤；改追踪 `.claude-plugin/marketplace.json` 中 superpowers
    条目 `source.sha` 字段的变化序列（design.md TD2）。"""
    installed_version = _read_superpowers_installed_version(installed_plugins_path)

    cache_dir = _ensure_bare_cache(cache_dir, upstream_url)
    head_sha = _rev_parse(cache_dir, "HEAD")
    anchor_sha = (anchor or {}).get("anchor_sha")

    commits = []
    source_sha_sequence = []
    if anchor_sha is not None:
        _assert_is_ancestor(cache_dir, anchor_sha, head_sha)
        commits, _ = _git_log_delta(
            cache_dir, anchor_sha, head_sha, path_filter=MARKETPLACE_JSON_PATH, reverse=True
        )
        for c in commits:
            show = _run(["git", "-C", str(cache_dir), "show", f"{c['sha']}:{MARKETPLACE_JSON_PATH}"])
            if show.returncode != 0:
                raise CollectError(
                    f"读取 {MARKETPLACE_JSON_PATH}@{c['sha']} 失败: {show.stderr.strip()}"
                )
            source_sha_sequence.append(_extract_superpowers_source_sha(show.stdout))

    return {
        "status": "ok",
        "head_sha": head_sha,
        "commits": commits,
        "source_sha_sequence": source_sha_sequence,
        "installed_version": installed_version,
    }


# ============================ OpenSpec 采集器（npm 版本对照 + schema fork drift）====

def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _diff_dirs_sha256(fork_dir, upstream_dir):
    """fork 目录 vs 上游安装目录逐文件整字节 sha256 对比（T264 机械实现，design.md TD3）。
    零解析——只比对字节，不解析文件内容语义。`added` = 上游有 fork 没有；
    `removed` = fork 有上游没有（spec Scenario「双侧新增与删除文件分类」明定方向）。"""
    fork_dir, upstream_dir = Path(fork_dir), Path(upstream_dir)
    files_fork = {p.relative_to(fork_dir).as_posix(): _sha256_file(p)
                  for p in fork_dir.rglob("*") if p.is_file()}
    files_upstream = {p.relative_to(upstream_dir).as_posix(): _sha256_file(p)
                       for p in upstream_dir.rglob("*") if p.is_file()}
    common = files_fork.keys() & files_upstream.keys()
    changed = sorted(k for k in common if files_fork[k] != files_upstream[k])
    added = sorted(files_upstream.keys() - files_fork.keys())
    removed = sorted(files_fork.keys() - files_upstream.keys())
    return {"changed": changed, "added": added, "removed": removed}


def collect_openspec(*, repo_root, fork_dir=None, npm_root_g=None):
    """`openspec --version` vs `npm view` 版本对照 + schema fork 双侧逐文件 sha256 对比。
    上游 schema 目录定位失败时只降级 schema_drift 子项，版本对照子项不受影响（spec Scenario）。
    """
    openspec_bin = shutil.which("openspec")
    if not openspec_bin:
        raise CollectError("本地锚源缺失: openspec CLI 未安装 / 不在 PATH")
    vr = _run([openspec_bin, "--version"])
    if vr.returncode != 0:
        raise CollectError(f"openspec --version 失败: {vr.stderr.strip()}")
    installed_version = vr.stdout.strip()

    nr = _run(["npm", "view", OPENSPEC_NPM_PACKAGE, "version"])
    if nr.returncode != 0:
        raise CollectError(f"npm view 失败: {nr.stderr.strip()}")
    latest_version = nr.stdout.strip()

    result = {"status": "ok", "installed_version": installed_version, "latest_version": latest_version}

    fork_dir = Path(fork_dir) if fork_dir else (
        Path(repo_root) / "sdflow-init" / "assets" / "schemas" / "sdflow-spec-driven"
    )
    try:
        if npm_root_g is not None:
            root_g = npm_root_g
        else:
            rr = _run(["npm", "root", "-g"])
            if rr.returncode != 0:
                raise CollectError(f"npm root -g 失败: {rr.stderr.strip()}")
            root_g = rr.stdout.strip()
        upstream_dir = Path(root_g) / "@fission-ai" / "openspec" / "schemas" / "spec-driven"
        if not upstream_dir.is_dir():
            raise CollectError(f"上游 schema 目录不存在: {upstream_dir}")
        drift = _diff_dirs_sha256(fork_dir, upstream_dir)
        result["schema_drift"] = {"status": "ok", **drift}
    except (CollectError, OSError) as e:
        # [impl-review-fix] _diff_dirs_sha256 内部 open() 可抛 OSError（如权限不足）；
        # 原来只捕 CollectError 会让它穿透到 _collect_source_safe，丢掉本函数已采集到的
        # installed_version/latest_version（版本对照子项不应被 schema_drift 子项的失败连累）。
        result["schema_drift"] = {"status": "degraded", "reason": str(e)}

    return result


# ============================ facts 采集编排 + collect 子命令 ============================

def _degraded(reason):
    return {"status": "degraded", "reason": reason}


def _collect_source_safe(fn):
    """单源采集失败隔离：CollectError / 超时 / 未预期 OSError 均转 degraded，
    MUST NOT 向上传染阻塞其余源（design.md「采集失败按源降级、fail-loud、不互相传染」）。"""
    try:
        return fn()
    except CollectError as e:
        return _degraded(str(e))
    except subprocess.TimeoutExpired:
        return _degraded(f"超时（>{SUBPROCESS_TIMEOUT_SECONDS}s）")
    except OSError as e:
        return _degraded(f"意外错误: {e}")


def collect_all(anchors, *, repo_root, home=None):
    """四源采集编排：默认锚源路径均从 `home`（默认 `Path.home()`，可注入供测试）派生。"""
    home = Path(home) if home is not None else Path.home()
    cache_root = home / ".cache" / "sdflow-upstream"

    sources = {}
    sources["gstack"] = _collect_source_safe(lambda: collect_gstack(
        get_source_anchor(anchors, "gstack"), checkout_dir=home / ".skills" / "gstack",
    ))
    sources["matt"] = _collect_source_safe(lambda: collect_matt(
        get_source_anchor(anchors, "matt"),
        cache_dir=cache_root / "matt.git",
        skill_lock_path=home / ".agents" / ".skill-lock.json",
    ))
    sources["superpowers"] = _collect_source_safe(lambda: collect_superpowers(
        get_source_anchor(anchors, "superpowers"),
        cache_dir=cache_root / "superpowers-marketplace.git",
        installed_plugins_path=home / ".claude" / "plugins" / "installed_plugins.json",
    ))
    sources["openspec"] = _collect_source_safe(lambda: collect_openspec(repo_root=repo_root))
    return sources


def _utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_timestamp_for_filename():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def cmd_collect(args):
    """`collect`：cwd 守卫 → 读锚 → 四源采集 → facts JSON 落
    `openspec/upstream/.facts/<UTC时间戳>.json`（不 git 跟踪）。"""
    root = guard_cwd()
    anchors_path = root / "openspec" / "upstream" / "anchors.yaml"
    anchors = load_anchors(anchors_path)

    sources = collect_all(anchors, repo_root=root)
    facts = {
        "schema_version": SCHEMA_VERSION,
        "collected_at": _utc_now_iso(),
        "sources": sources,
    }

    facts_dir = root / "openspec" / "upstream" / ".facts"
    facts_dir.mkdir(parents=True, exist_ok=True)
    facts_path = facts_dir / f"{_utc_timestamp_for_filename()}.json"
    facts_path.write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"facts 已写入: {facts_path}")
    return 0


# ============================ advance 子命令（报告+facts 双参数门）============================

def _observed_anchor(source_name, entry):
    """facts 某源 `status=ok` 记录 → anchors.yaml 该源应推进到的观测值
    （design.md 数据模型段：git 三源用 anchor_sha；openspec 用 anchor_version；
    superpowers 额外携带 installed_version 辅助信息）。"""
    if source_name == "openspec":
        return {"anchor_version": entry.get("installed_version")}
    rec = {"anchor_sha": entry.get("head_sha")}
    if source_name == "superpowers" and "installed_version" in entry:
        rec["installed_version"] = entry["installed_version"]
    return rec


def cmd_advance(args):
    """`advance <report-path> <facts-path>`：cwd 守卫 → 报告+facts 双参数前置校验
    （报告存在 + 报告文本包含 facts 全部 commit sha，零解析子串校验）→ 仅推进
    `status=ok` 源的锚（degraded 源逐字保留）→ 更新 `last_run`。
    advance 自身 MUST NOT 发起任何网络/git 查询——观测值只读 facts 文件。"""
    root = guard_cwd()

    if not args.report:
        raise AdvanceGateError("缺少报告路径参数：advance <report-path> <facts-path>")
    if not args.facts:
        raise AdvanceGateError("缺少 facts 路径参数：advance <report-path> <facts-path>")

    report_path = Path(args.report)
    facts_path = Path(args.facts)
    if not report_path.is_file():
        raise AdvanceGateError(f"报告文件不存在: {report_path}")
    if not facts_path.is_file():
        raise AdvanceGateError(f"facts 文件不存在: {facts_path}")

    try:
        facts = json.loads(facts_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise AdvanceGateError(f"facts 文件不可解析: {facts_path}: {e}")
    if not isinstance(facts, dict):
        raise AdvanceGateError(f"facts 文件形状非法（须为映射）: {facts_path}")

    try:
        report_text = report_path.read_text(encoding="utf-8")
    except (OSError, ValueError) as e:
        # [impl-review-fix] 报告存在性已在上面 is_file() 判过，但读取仍可能因权限/编码等
        # 原因失败；未保护会让原始异常穿透，不符合 advance 全程 fail-loud 走 AdvanceGateError
        # 的既有约定。
        raise AdvanceGateError(f"报告文件不可读: {report_path}: {e}")
    sources = facts.get("sources") or {}

    missing_shas = []
    for source_name, entry in sources.items():
        if not isinstance(entry, dict):
            continue
        for c in entry.get("commits") or []:
            sha = c.get("sha") if isinstance(c, dict) else None
            if sha and sha not in report_text:
                missing_shas.append(f"{source_name}:{sha}")
    if missing_shas:
        raise AdvanceGateError(
            "报告缺少 facts 中的 commit sha 转录（防漏转录后锚照推）: " + ", ".join(missing_shas)
        )

    anchors_path = root / "openspec" / "upstream" / "anchors.yaml"
    anchors = load_anchors(anchors_path)
    anchors.setdefault("sources", {})

    for source_name, entry in sources.items():
        if not isinstance(entry, dict) or entry.get("status") != "ok":
            continue  # degraded 源锚不推进，逐字保留
        observed = _observed_anchor(source_name, entry)
        # [impl-review-fix] status=ok 但观测值字段为空（None）时拒绝推进——
        # 空锚一旦写入 anchors.yaml，下一轮采集会把它当"无锚首轮"重新走一遍全量 delta，
        # 静默丢失本应记录的推进点，且不会在当轮报出任何错误。
        anchor_key = "anchor_version" if source_name == "openspec" else "anchor_sha"
        if not observed.get(anchor_key):
            raise AdvanceGateError(
                f"{source_name} 源 status=ok 但观测值 {anchor_key} 为空，拒绝推进锚"
                f"（facts 文件: {facts_path}）"
            )
        anchors["sources"][source_name] = observed

    anchors["last_run"] = _utc_now_iso()
    write_anchors(anchors_path, anchors)

    print(f"advance: 锚已推进（{anchors_path}）")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="upstream_watch.py",
        description="四源上游追踪（gstack/superpowers/matt/OpenSpec）——collect 采集事实，"
                     "advance 校验报告后推进锚。仅服务 sdflow-skills 仓自身。",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("collect", help="采集四源 delta 事实，落 facts JSON")
    advance_parser = sub.add_parser("advance", help="校验报告+facts 双参数后推进锚")
    # nargs="?" + 默认 None：缺参不在 argparse 层报错，而是在 cmd_advance 内部
    # guard_cwd() 之后才判定——保持"cwd 守卫永远最先检查"的既有 CLI 行为不变
    # （Task 1 既有测试：非本仓 cwd 下裸 `advance`（零参）仍须落到 CwdGuardError 分支）。
    advance_parser.add_argument("report", nargs="?", default=None, help="本轮分诊报告路径")
    advance_parser.add_argument("facts", nargs="?", default=None, help="本轮 facts JSON 路径")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            return cmd_collect(args)
        if args.command == "advance":
            return cmd_advance(args)
    except CwdGuardError as e:
        print(f"fail-loud: {e}", file=sys.stderr)
        return 1
    except AdvanceGateError as e:
        print(f"advance 拒绝推进: {e}", file=sys.stderr)
        return 3
    except AnchorsError as e:
        print(f"fail-loud: {e}", file=sys.stderr)
        return 1
    return 1  # pragma: no cover — argparse required=True 已排除未知子命令


if __name__ == "__main__":
    sys.exit(main())
