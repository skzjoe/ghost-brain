import subprocess
import shutil
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



def snapshot_tree(root):
    """Record links without following them, plus all regular file bytes/modes."""
    result = {}
    for path in sorted(root.rglob("*")):
        key = str(path.relative_to(root))
        if path.is_symlink():
            result[key] = ("link", str(path.readlink()))
        elif path.is_file():
            result[key] = ("file", path.read_bytes(), path.stat().st_mode)
        else:
            result[key] = ("dir", path.stat().st_mode)
    return result


@pytest.mark.parametrize("relative", [
    "skills", "skills/ghost-audit", "skills/ghost-audit/SKILL.md",
    "skills/ghost-remember/SKILL.md", "memory", "memory/reference",
    "memory/reference/SECOND-BRAIN.md",
])
@pytest.mark.parametrize("dangling", [False, True])
@pytest.mark.parametrize("force", [False, True])
def test_selected_links_rejected_before_any_writes(install_env, relative, dangling, force):
    env, workspace, _ = install_env
    external = workspace.parent / "external"
    external.mkdir()
    victim = external / "victim"
    if not dangling:
        if relative.endswith(".md"):
            victim.write_text("External data must survive\n")
        else:
            victim.mkdir()
            (victim / "SKILL.md").write_text("External data must survive\n")
    link = workspace / relative
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(victim)
    before = snapshot_tree(workspace.parent)
    result = run_script("install.sh", env, *(["--force"] if force else []))
    assert result.returncode != 0
    assert "symbolic link" in result.stderr
    assert "move conflicting links/files aside manually" in result.stderr
    assert snapshot_tree(workspace.parent) == before


@pytest.mark.parametrize("location", ["target", "ancestor"])
@pytest.mark.parametrize("suffix", ["", "/", "/."])
def test_workspace_links_rejected_before_any_writes(install_env, location, suffix):
    env, workspace, _ = install_env
    alias = workspace.parent / "alias"
    alias.symlink_to(workspace if location == "target" else workspace.parent)
    target = alias if location == "target" else alias / workspace.name
    env["OPENCLAW_WORKSPACE"] = str(target) + suffix
    before = snapshot_tree(workspace.parent)
    result = run_script("install.sh", env, "--force")
    assert result.returncode != 0
    assert "symbolic link" in result.stderr
    assert snapshot_tree(workspace.parent) == before


@pytest.mark.parametrize("name", ["AGENTS.md", "BOOTSTRAP.md"])
@pytest.mark.parametrize("dangling", [False, True])
def test_preserved_instruction_links_are_not_followed(install_env, name, dangling):
    env, workspace, _ = install_env
    external = workspace.parent / "external-note"
    if not dangling:
        external.write_text("Preserve user instructions\n")
    link = workspace / name
    link.symlink_to(external)
    result = run_script("install.sh", env, "--force")
    assert result.returncode == 0, result.stdout + result.stderr
    assert link.is_symlink() and link.readlink() == external
    assert (workspace / "skills/ghost-audit/SKILL.md").is_file()
    if dangling:
        assert not external.exists()
    else:
        assert external.read_text() == "Preserve user instructions\n"


@pytest.mark.parametrize("relative", ["skills/ghost-remember", "memory/reference/SECOND-BRAIN.md"])
def test_type_collisions_rejected_without_partial_install(install_env, relative):
    env, workspace, _ = install_env
    target = workspace / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if relative.endswith(".md"):
        target.mkdir()
    else:
        target.write_text("User data\n")
    before = snapshot_tree(workspace.parent)
    assert run_script("install.sh", env, "--force").returncode != 0
    assert snapshot_tree(workspace.parent) == before


@pytest.mark.parametrize("relative", [
    "scripts/ghost_core/__init__.py", "scripts/generate_context_bridge.sh", ".local",
])
def test_legacy_late_link_rejected_before_writes_or_runtime(install_env, relative):
    env, workspace, _ = install_env
    external = workspace.parent / "external"
    external.write_text("Private fixture\n")
    link = workspace / relative
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(external)
    before = snapshot_tree(workspace.parent)
    result = run_script("install.sh", env, "--legacy", "--force")
    assert result.returncode != 0
    assert "symbolic link" in result.stderr
    assert snapshot_tree(workspace.parent) == before



def test_unrelated_destination_link_is_preserved(install_env):
    env, workspace, _ = install_env
    assert run_script("install.sh", env).returncode == 0
    external = workspace.parent / "external-user-note"
    external.write_text("Keep unrelated data\n")
    link = workspace / "skills/ghost-audit/user-note"
    link.symlink_to(external)
    assert run_script("install.sh", env, "--force").returncode == 0
    assert link.is_symlink()
    assert external.read_text() == "Keep unrelated data\n"


@pytest.mark.parametrize("source_link", [False, True])
def test_nested_package_paths_are_preflighted(install_env, source_link):
    env, workspace, _ = install_env
    package = workspace.parent / "package"
    package.mkdir()
    shutil.copy2(ROOT / "install.sh", package / "install.sh")
    for name in DEFAULT_SKILLS:
        shutil.copytree(ROOT / "skills" / name, package / "skills" / name)
    shutil.copytree(ROOT / "starter", package / "starter")
    for name in ("PLAYBOOK.md", "SECOND-BRAIN.md"):
        shutil.copy2(ROOT / name, package / name)
    extra = package / "skills/ghost-remember/.hidden/nested"
    extra.mkdir(parents=True)
    external = workspace.parent / "external-nested"
    external.write_text("Keep external data\n")
    if source_link:
        (extra / "file.md").symlink_to(external)
    else:
        (extra / "file.md").write_text("Packaged fixture\n")
        target = workspace / "skills/ghost-remember/.hidden/nested/file.md"
        target.parent.mkdir(parents=True)
        target.symlink_to(external)
    before = snapshot_tree(workspace.parent)
    result = run_script(str(package / "install.sh"), env, "--force")
    assert result.returncode != 0
    assert "symbolic link" in result.stderr
    assert snapshot_tree(workspace.parent) == before
