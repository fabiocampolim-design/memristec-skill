# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Weekly upstream watch for the MemrisTec Model Library (playbook S8 / rule 23).

The library lives on RWTH Aachen's GitLab behind a proof-of-work bot wall, so its web
pages and API are not reachable from a script -- `git` is. The watch therefore works on
a *local clone* (the one `MEMRISTEC_MODEL_LIBRARY` points at; a partial clone with
`--filter=blob:none` is enough): it fetches, records every remote branch head, the tags
and the tree hash of every `models/<folder>` on every branch, compares with the previous
snapshot and writes `<outdir>/YYYY-WW.md`. Only tree-level git commands are used, so a
partial clone never downloads blobs.

--snapshot   record the current state (JSON) in --state-dir
--weekly     fetch, compare with the previous snapshot, write the report, then snapshot
--no-fetch   compare the clone as it is (offline)

Usage:
    MEMRISTEC_MODEL_LIBRARY=<clone> python scripts/watch_upstream.py --weekly
    python scripts/watch_upstream.py --weekly --clone <clone> --outdir docs/watch
Exit 0 ok, 1 git failed (fetch or read), 2 usage error, 3 no clone available.
"""

import argparse
import datetime
import json
import os
import platform
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
STUDY_ROOT = os.path.normpath(os.path.join(ROOT, ".."))
sys.path.insert(0, HERE)
from memristec_tools import __version__  # noqa: E402

REMOTE = "origin"


def find_clone(explicit=None):
    p = explicit or os.environ.get("MEMRISTEC_MODEL_LIBRARY")
    return p if p and os.path.isdir(os.path.join(p, ".git")) else None


def _git(cwd, *args, timeout=600):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, check=True, encoding="utf-8", errors="replace").stdout


def branches(clone):
    """{branch: {"sha", "date"}} for every remote branch (HEAD pointer excluded)."""
    out = {}
    # full ref names: %(refname:short) turns the symbolic refs/remotes/origin/HEAD into
    # the bare "origin" and a real clone tripped on it on the first run (2026-09-04)
    prefix = f"refs/remotes/{REMOTE}/"
    text = _git(clone, "for-each-ref", prefix.rstrip("/"),
                "--format=%(refname)%09%(objectname)%09%(committerdate:iso-strict)")
    for line in text.splitlines():
        ref, sha, date = line.split("\t")
        if not ref.startswith(prefix):
            continue
        name = ref[len(prefix):]
        if name == "HEAD" or not sha:
            continue
        out[name] = {"sha": sha, "date": date}
    return out


def folders(clone, ref):
    """{model folder: tree hash} under models/ of `ref` (tree-only: no blob fetch)."""
    out = {}
    try:
        text = _git(clone, "ls-tree", ref, "models/")
    except subprocess.CalledProcessError:
        return out
    for line in text.splitlines():
        meta, path = line.split("\t")
        mode, kind, sha = meta.split()
        if kind == "tree":
            out[path.split("/", 1)[1]] = sha
    return out


def tags(clone):
    return sorted(t for t in _git(clone, "tag").splitlines() if t.strip())


def snapshot(clone, state_dir, fetch=True):
    if fetch:
        _git(clone, "fetch", "--all", "--prune", "-q")
    data = {"taken": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "remote": _git(clone, "remote", "get-url", REMOTE).strip(),
            "branches": branches(clone), "tags": tags(clone), "folders": {}}
    for name in data["branches"]:
        data["folders"][name] = folders(clone, f"{REMOTE}/{name}")
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, "state.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    return data


def load_previous(state_dir):
    p = os.path.join(state_dir, "state.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def folder_delta(old, new):
    """(added, removed, changed) model folders between two {folder: tree} maps."""
    added = sorted(k for k in new if k not in old)
    removed = sorted(k for k in old if k not in new)
    changed = sorted(k for k in new if k in old and old[k] != new[k])
    return added, removed, changed


def new_commits(clone, old_sha, new_sha, limit=50):
    """One-line subjects of old..new (no -p: safe in a partial clone)."""
    if not old_sha or old_sha == new_sha:
        return []
    try:
        text = _git(clone, "log", "--no-merges", "--format=%h %ad %an: %s", "--date=short",
                    f"--max-count={limit}", f"{old_sha}..{new_sha}")
    except subprocess.CalledProcessError:
        return [f"(history between {old_sha[:7]} and {new_sha[:7]} not linear)"]
    return text.splitlines()


def render_weekly(week, prev, new, commits):
    """Markdown report; `commits` = {branch: [lines]}."""
    lines = [f"# Upstream watch {week}", "", f"Source: {new.get('remote', '?')} (local clone, fetched {new.get('taken', '')[:16]}Z)", ""]
    prev_b = (prev or {}).get("branches", {})
    prev_f = (prev or {}).get("folders", {})
    for name, head in sorted(new["branches"].items()):
        before = prev_b.get(name, {}).get("sha", "")
        state = "new branch" if name not in prev_b else ("moved" if before != head["sha"] else "unchanged")
        lines.append(f"## {name}: {state} ({before[:7] or '-'} → {head['sha'][:7]}, {head['date'][:10]})")
        added, removed, changed = folder_delta(prev_f.get(name, {}), new["folders"].get(name, {}))
        if added or removed or changed:
            lines.append(f"- model folders: {len(new['folders'].get(name, {}))} "
                         f"(+{len(added)} −{len(removed)} ~{len(changed)})")
            lines += [f"  - added `{k}`" for k in added] + [f"  - removed `{k}`" for k in removed] + [f"  - changed `{k}`" for k in changed]
        for c in commits.get(name, []):
            lines.append(f"- {c}")
        lines.append("")
    gone = sorted(set(prev_b) - set(new["branches"]))
    if gone:
        lines += ["## branches removed: " + ", ".join(gone), ""]
    new_tags = sorted(set(new.get("tags", [])) - set((prev or {}).get("tags", [])))
    lines.append(f"## tags: {len(new.get('tags', []))} total, {len(new_tags)} new" + (" — " + ", ".join(new_tags) if new_tags else ""))
    lines.append("")
    return "\n".join(lines)


def audit(log_dir, argv, extra):
    os.makedirs(log_dir, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rec = {"tool": "watch_upstream", "version": __version__, "argv": list(argv), "utc": stamp,
           "python": platform.python_version(), "platform": platform.platform()}
    rec.update(extra)
    path = os.path.join(log_dir, f"watch_upstream_{stamp}_{os.getpid()}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, default=str)
    return path


def build_parser():
    ap = argparse.ArgumentParser(prog="watch_upstream", description=__doc__.splitlines()[0])
    ap.add_argument("--weekly", action="store_true", help="fetch, compare with the previous snapshot, write the report")
    ap.add_argument("--snapshot", action="store_true", help="record the current state only")
    ap.add_argument("--no-fetch", action="store_true", help="do not git fetch; compare the clone as it is")
    ap.add_argument("--clone", default=None, help="local clone of the library (default: $MEMRISTEC_MODEL_LIBRARY)")
    ap.add_argument("--state-dir", default=os.path.join(STUDY_ROOT, "forum", "upstream-watch"),
                    help="where the snapshot and logs live (default <study>/forum/upstream-watch)")
    ap.add_argument("--outdir", default=os.path.join(STUDY_ROOT, "docs", "watch"),
                    help="where weekly reports go (default <study>/docs/watch)")
    ap.add_argument("--log-dir", default=None, help="audit-log directory (default <state-dir>/logs)")
    ap.add_argument("-q", "--quiet", action="store_true", help="print only the verdict")
    ap.add_argument("--version", action="version", version=f"memristec-skill {__version__}")
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    if not (args.weekly or args.snapshot):
        build_parser().print_help()
        return 2
    clone = find_clone(args.clone)
    if not clone:
        print("no clone: set MEMRISTEC_MODEL_LIBRARY or pass --clone")
        return 3
    log_dir = args.log_dir or os.path.join(args.state_dir, "logs")
    week = datetime.date.today().strftime("%G-W%V")
    extra = {"clone": clone, "week": week}
    try:
        prev = load_previous(args.state_dir)
        new = snapshot(clone, args.state_dir, fetch=not args.no_fetch)
        extra["branches"] = {k: v["sha"][:7] for k, v in new["branches"].items()}
        if args.weekly:
            commits = {}
            for name, head in new["branches"].items():
                commits[name] = new_commits(clone, (prev or {}).get("branches", {}).get(name, {}).get("sha", ""), head["sha"])
            md = render_weekly(week, prev, new, commits)
            os.makedirs(args.outdir, exist_ok=True)
            path = os.path.join(args.outdir, f"{week}.md")
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(md)
            extra["written"] = path
            extra["moved"] = sorted(n for n, c in commits.items() if c)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        extra["error"] = str(exc)
        audit(log_dir, argv, extra)
        print(f"watch_upstream: git failed: {exc}", file=sys.stderr)
        return 1
    log = audit(log_dir, argv, extra)
    if not args.quiet:
        print(json.dumps({k: v for k, v in extra.items() if k != "clone"}, default=str))
    print(f"watch_upstream OK (log {log})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
