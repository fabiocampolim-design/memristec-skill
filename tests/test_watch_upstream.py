# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""scripts/watch_upstream.py — pure functions, the parser, and an offline end-to-end run
on a throw-away git repository (no network; git must be on PATH)."""

import os
import shutil
import subprocess
import sys

import pytest

from conftest import ROOT

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import watch_upstream as wu  # noqa: E402

GIT = shutil.which("git")
needs_git = pytest.mark.skipif(GIT is None, reason="git not on PATH")


def _run(cwd, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=env).stdout


def _upstream_with_model(path, folder, content="x = 1\n"):
    os.makedirs(os.path.join(path, "models", folder), exist_ok=True)
    with open(os.path.join(path, "models", folder, "model.py"), "w", encoding="utf-8") as f:
        f.write(content)


def test_folder_delta_added_removed_changed():
    old = {"A": "1", "B": "2", "C": "3"}
    new = {"A": "1", "B": "9", "D": "4"}
    assert wu.folder_delta(old, new) == (["D"], ["C"], ["B"])


def test_render_weekly_first_run_and_moved_branch():
    new = {"remote": "https://example.invalid/lib", "taken": "2026-09-04T10:00:00Z",
           "branches": {"main": {"sha": "b" * 40, "date": "2026-09-01T00:00:00+00:00"}},
           "folders": {"main": {"A": "1", "B": "2"}}, "tags": ["v1"]}
    md = wu.render_weekly("2026-W36", None, new, {"main": []})
    assert md.startswith("# Upstream watch 2026-W36") and "main: new branch" in md and "tags: 1 total, 1 new — v1" in md
    prev = {"branches": {"main": {"sha": "a" * 40}}, "folders": {"main": {"A": "1"}}, "tags": ["v1"]}
    md = wu.render_weekly("2026-W36", prev, new, {"main": ["bbbbbbb 2026-09-01 t: add B"]})
    assert "main: moved (aaaaaaa → bbbbbbb, 2026-09-01)" in md
    assert "model folders: 2 (+1 −0 ~0)" in md and "added `B`" in md and "add B" in md
    assert "tags: 1 total, 0 new" in md


def test_cli_parser_no_mode_exit_2_and_no_clone_exit_3(monkeypatch, tmp_path):
    ns = wu.build_parser().parse_args(["--weekly", "--clone", "c", "--outdir", "o", "--no-fetch"])
    assert ns.weekly and ns.clone == "c" and ns.outdir == "o" and ns.no_fetch
    assert wu.main([]) == 2
    monkeypatch.delenv("MEMRISTEC_MODEL_LIBRARY", raising=False)
    assert wu.main(["--snapshot", "--clone", str(tmp_path / "nowhere"), "--state-dir", str(tmp_path)]) == 3


@needs_git
def test_weekly_end_to_end_on_a_throwaway_clone(tmp_path):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _run(upstream, "init", "-q", "-b", "main")
    _upstream_with_model(str(upstream), "HP_Biolek2009")
    _run(upstream, "add", "."); _run(upstream, "commit", "-q", "-m", "first model")
    clone = tmp_path / "clone"
    _run(tmp_path, "clone", "-q", str(upstream), str(clone))
    state, out = tmp_path / "state", tmp_path / "watch"
    # first run: everything is new, report written, snapshot stored
    rc = wu.main(["--weekly", "--clone", str(clone), "--state-dir", str(state), "--outdir", str(out), "-q"])
    assert rc == 0 and os.path.exists(state / "state.json")
    reports = sorted(os.listdir(out))
    assert len(reports) == 1 and reports[0].endswith(".md")
    md = open(out / reports[0], encoding="utf-8").read()
    assert "main: new branch" in md
    # upstream moves: a folder is added, one changed; the weekly run sees both and the commit
    _upstream_with_model(str(upstream), "VTEAM2015")
    _upstream_with_model(str(upstream), "HP_Biolek2009", "x = 2\n")
    _run(upstream, "add", "."); _run(upstream, "commit", "-q", "-m", "add VTEAM, fix Biolek")
    rc = wu.main(["--weekly", "--clone", str(clone), "--state-dir", str(state), "--outdir", str(out), "-q"])
    assert rc == 0
    md = open(out / reports[0], encoding="utf-8").read()
    assert "main: moved" in md and "added `VTEAM2015`" in md and "changed `HP_Biolek2009`" in md
    assert "add VTEAM, fix Biolek" in md
    logs = [f for f in os.listdir(state / "logs") if f.startswith("watch_upstream_")]
    assert len(logs) == 2


@needs_git
def test_git_failure_is_exit_1_not_a_traceback(tmp_path):
    broken = tmp_path / "broken"
    broken.mkdir(); (broken / ".git").mkdir()          # looks like a clone, is not one
    rc = wu.main(["--snapshot", "--clone", str(broken), "--state-dir", str(tmp_path / "s")])
    assert rc == 1


@pytest.mark.skipif(shutil.which("powershell") is None, reason="PowerShell not available")
def test_scheduler_script_dry_run_and_version():
    script = os.path.join(ROOT, "scripts", "register_watch_task.ps1")
    out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, "-DryRun", "-Clone", "C:/x"],
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0 and "DRY-RUN" in out.stdout and "--weekly" in out.stdout and "C:/x" in out.stdout
    ver = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, "-Version"],
                         capture_output=True, text=True, timeout=120)
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
        assert ver.stdout.strip() == f"memristec-skill {f.read().strip()}"
