import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKILLS = {"ghost-audit", "ghost-capture", "ghost-recall", "ghost-remember"}


@pytest.fixture
def install_env(tmp_path):
    home = tmp_path / "home"
    workspace = home / ".openclaw" / "workspace"
    workspace.mkdir(parents=True)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "unexpected-calls"
    for tool in ("openclaw", "python3", "pip", "pip3", "crontab", "curl"):
        stub = bin_dir / tool
        stub.write_text('#!/bin/sh\nprintf "%s\n" "$0 $*" >> "$CALLS"\nexit 99\n')
        stub.chmod(0o755)
    env = {
        "HOME": str(home),
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "OPENCLAW_WORKSPACE": str(workspace),
        "CALLS": str(calls),
    }
    yield env, workspace, calls
    assert not calls.exists(), "Default setup must not call runtime, package or network tools"


def run_script(name, env, *args, input_text=""):
    return subprocess.run(
        ["bash", str(ROOT / name), *args], env=env, input=input_text,
        capture_output=True, text=True, timeout=20,
    )


@pytest.mark.parametrize("entrypoint", ["install.sh", "starter/install.sh"])
def test_default_install_is_small_and_offline(install_env, entrypoint):
    env, workspace, _ = install_env
    result = run_script(entrypoint, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert {p.name for p in (workspace / "skills").iterdir()} == DEFAULT_SKILLS
    assert {p.name for p in workspace.iterdir()} == {"skills", "memory", "AGENTS.md", "BOOTSTRAP.md"}
    assert {p.name for p in (workspace / "memory").iterdir()} == {"reference"}
    assert run_script("test.sh", env).returncode == 0


def test_rerun_and_force_preserve_user_data_without_nesting(install_env):
    env, workspace, _ = install_env
    assert run_script("install.sh", env).returncode == 0
    agents = workspace / "AGENTS.md"
    agents.write_text("Existing user instructions\n")
    bootstrap = workspace / "BOOTSTRAP.md"
    bootstrap.write_text("Existing setup\n")
    note = workspace / "memory" / "decisions.md"
    note.write_text("Keep this note\n")
    skill = workspace / "skills" / "ghost-audit"
    (skill / "SKILL.md").write_text("Customized audit\n")
    (skill / "user-note.txt").write_text("Keep this customization\n")
    assert run_script("install.sh", env).returncode == 0
    assert (skill / "SKILL.md").read_text() == "Customized audit\n"
    assert run_script("install.sh", env, "--force").returncode == 0
    assert (skill / "SKILL.md").read_text() == (ROOT / "skills/ghost-audit/SKILL.md").read_text()
    assert not (skill / "ghost-audit").exists()
    assert (skill / "user-note.txt").read_text() == "Keep this customization\n"
    assert agents.read_text() == "Existing user instructions\n"
    assert bootstrap.read_text() == "Existing setup\n"
    assert note.read_text() == "Keep this note\n"


def test_home_default_and_workspace_with_spaces(install_env):
    env, workspace, _ = install_env
    env.pop("OPENCLAW_WORKSPACE")
    assert run_script("install.sh", env).returncode == 0
    target = workspace.parent / "space and ' quote"
    target.mkdir()
    env["OPENCLAW_WORKSPACE"] = str(target)
    assert run_script("install.sh", env).returncode == 0
    assert run_script("test.sh", env).returncode == 0


def test_missing_workspace_and_unknown_option_fail_before_writes(install_env):
    env, workspace, _ = install_env
    env["OPENCLAW_WORKSPACE"] = str(workspace / "missing")
    result = run_script("install.sh", env)
    assert result.returncode == 1
    assert "Workspace not found" in result.stdout
    assert run_script("install.sh", env, "--unknown").returncode == 2
    assert run_script("install.sh", env, "--help").returncode == 0
    assert not list(workspace.iterdir())


def test_smoke_reports_missing_files_without_runtime_calls(install_env):
    env, _, _ = install_env
    result = run_script("test.sh", env)
    assert result.returncode != 0
    assert "Missing or empty" in result.stderr
    assert run_script("test.sh", env, "--unknown").returncode == 2


def test_cron_requires_opt_in_and_confirmation_defaults_to_no(install_env):
    env, _, _ = install_env
    assert run_script("setup-crons.sh", env).returncode == 2
    assert run_script("setup-crons.sh", env, "--unknown").returncode == 2
    result = run_script("setup-crons.sh", env, "--legacy", input_text="\n\n\n\n")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Aborted" in result.stdout


def test_legacy_cron_uses_fake_runtime_only(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls"
    stub = bin_dir / "openclaw"
    stub.write_text('#!/bin/sh\nprintf "%s\n" "$1 $2" >> "$CALLS"\n')
    stub.chmod(0o755)
    env = {"HOME": str(tmp_path), "PATH": f"{bin_dir}:/usr/bin:/bin",
           "OPENCLAW_WORKSPACE": str(workspace), "CALLS": str(calls)}
    result = run_script("setup-crons.sh", env, "--legacy", input_text="UTC\nfixture/model\nn\ny\n")
    assert result.returncode == 0, result.stdout + result.stderr
    assert calls.read_text().splitlines() == ["cron add"] * 9
