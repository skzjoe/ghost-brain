"""Tests for ghost_auto_skill.py"""

import json
import os
import sys
import shutil
import tempfile
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import ghost_auto_skill as gas


@pytest.fixture(autouse=True)
def isolated_workspace(tmp_path, monkeypatch):
    """Each test gets a clean workspace."""
    monkeypatch.setattr(gas, "WORKSPACE", tmp_path)
    monkeypatch.setattr(gas, "STATE_FILE", tmp_path / ".local" / "auto_skills.json")
    monkeypatch.setattr(gas, "SKILLS_AUTO_DIR", tmp_path / "skills" / ".auto")
    monkeypatch.setattr(gas, "SKILLS_DIR", tmp_path / "skills")
    (tmp_path / "skills" / ".auto").mkdir(parents=True)
    (tmp_path / ".local").mkdir(parents=True)
    yield tmp_path


# ─── detect ──────────────────────────────────────────────────────────

class TestDetect:
    def test_simple_task_not_worthy(self):
        result = gas.cmd_detect("fix a typo")
        assert result["worthy"] is False

    def test_complex_task_worthy(self):
        task = """Step 1: Read the config file with read tool
Step 2: Parse the JSON and extract API keys
Step 3: Execute curl to test each endpoint
Step 4: Write results to output.json
Step 5: Then send summary via exec python script"""
        result = gas.cmd_detect(task)
        assert result["worthy"] is True
        assert result["score"] >= 0.5

    def test_returns_keywords(self):
        task = "Use browser to navigate to Meta Ads Manager, create campaign, set budget"
        result = gas.cmd_detect(task)
        assert "keywords" in result
        assert len(result["keywords"]) > 0


# ─── create ──────────────────────────────────────────────────────────

class TestCreate:
    def test_create_skill(self, isolated_workspace):
        task = "Step 1: fetch URL\nStep 2: parse content\nStep 3: write summary"
        sid = gas.cmd_create("URL Summarizer", task, "Summarize any URL")
        assert sid == "url-summarizer"

        # Check state
        state = gas._load_state()
        assert "url-summarizer" in state["skills"]
        assert state["skills"]["url-summarizer"]["status"] == "draft"
        assert state["skills"]["url-summarizer"]["usage"]["count"] == 0

        # Check file
        skill_path = isolated_workspace / "skills" / ".auto" / "url-summarizer" / "SKILL.md"
        assert skill_path.exists()
        content = skill_path.read_text()
        assert "URL Summarizer" in content
        assert "Step 1: fetch URL" in content

    def test_create_duplicate_blocked(self, isolated_workspace):
        gas.cmd_create("Test Skill", "step 1\nstep 2\nstep 3")
        result = gas.cmd_create("Test Skill", "different steps")
        assert result is None

    def test_create_allows_retired_overwrite(self, isolated_workspace):
        gas.cmd_create("Test Skill", "step 1\nstep 2\nstep 3")
        state = gas._load_state()
        state["skills"]["test-skill"]["status"] = "retired"
        gas._save_state(state)
        sid = gas.cmd_create("Test Skill", "new steps")
        assert sid == "test-skill"


# ─── match ───────────────────────────────────────────────────────────

class TestMatch:
    def test_match_finds_skill(self, isolated_workspace):
        gas.cmd_create(
            "Meta Campaign Creator",
            "browser navigate meta ads manager create campaign set budget audience",
            "Create Meta ad campaigns",
        )
        matches = gas.cmd_match("create a meta ads campaign with budget")
        assert len(matches) >= 1
        assert matches[0]["skill_id"] == "meta-campaign-creator"
        assert matches[0]["confidence"] in {"medium", "high"}
        assert matches[0]["task_coverage"] > 0

    def test_match_no_result(self, isolated_workspace):
        gas.cmd_create(
            "URL Summarizer",
            "fetch url parse content write summary",
        )
        matches = gas.cmd_match("deploy kubernetes cluster")
        assert len(matches) == 0

    def test_match_skips_retired(self, isolated_workspace):
        gas.cmd_create("Test Skill", "browser navigate fetch parse write")
        state = gas._load_state()
        state["skills"]["test-skill"]["status"] = "retired"
        gas._save_state(state)
        matches = gas.cmd_match("browser navigate fetch parse")
        assert len(matches) == 0


# ─── record ──────────────────────────────────────────────────────────

class TestRecord:
    def test_record_success(self, isolated_workspace):
        gas.cmd_create("Test Skill", "step 1 step 2 step 3")
        gas.cmd_record("test-skill", "success")
        state = gas._load_state()
        assert state["skills"]["test-skill"]["usage"]["successes"] == 1
        assert state["skills"]["test-skill"]["usage"]["count"] == 1

    def test_record_failure(self, isolated_workspace):
        gas.cmd_create("Test Skill", "step 1 step 2 step 3")
        gas.cmd_record("test-skill", "failure")
        state = gas._load_state()
        assert state["skills"]["test-skill"]["usage"]["failures"] == 1

    def test_auto_promote(self, isolated_workspace):
        gas.cmd_create("Good Skill", "step 1 step 2 step 3")
        for _ in range(3):
            gas.cmd_record("good-skill", "success")
        state = gas._load_state()
        assert state["skills"]["good-skill"]["status"] == "active"

    def test_auto_retire(self, isolated_workspace):
        gas.cmd_create("Bad Skill", "step 1 step 2 step 3")
        for _ in range(3):
            gas.cmd_record("bad-skill", "failure")
        state = gas._load_state()
        assert state["skills"]["bad-skill"]["status"] == "retired"

    def test_mixed_no_premature_promote(self, isolated_workspace):
        gas.cmd_create("Mixed Skill", "step 1 step 2 step 3")
        gas.cmd_record("mixed-skill", "success")
        gas.cmd_record("mixed-skill", "success")
        gas.cmd_record("mixed-skill", "failure")  # 66% rate
        state = gas._load_state()
        # Should not promote (rate < 90%)
        assert state["skills"]["mixed-skill"]["status"] == "draft"

    def test_record_unknown_skill(self, isolated_workspace):
        gas.cmd_record("nonexistent", "success")
        # Should not crash


# ─── improve ─────────────────────────────────────────────────────────

class TestImprove:
    def test_improve_appends_note(self, isolated_workspace):
        gas.cmd_create("Test Skill", "step 1\nstep 2")
        gas.cmd_improve("test-skill", "Failed when input has unicode characters")
        state = gas._load_state()
        assert state["skills"]["test-skill"]["improvements"] == 1

        skill_path = Path(state["skills"]["test-skill"]["skill_path"])
        content = skill_path.read_text()
        assert "Improvement Note #1" in content
        assert "unicode characters" in content

    def test_improve_updates_keywords(self, isolated_workspace):
        gas.cmd_create("Test Skill", "step 1 step 2 step 3")
        gas.cmd_improve("test-skill", "Failed with large csv files over 10mb")
        state = gas._load_state()
        kw = state["skills"]["test-skill"]["fingerprint"]["keywords"]
        assert "csv" in kw or "files" in kw


# ─── promote / retire ────────────────────────────────────────────────

class TestManualActions:
    def test_manual_promote(self, isolated_workspace):
        gas.cmd_create("Test Skill", "step 1 step 2 step 3")
        gas.cmd_promote("test-skill")
        state = gas._load_state()
        assert state["skills"]["test-skill"]["status"] == "active"

    def test_manual_retire(self, isolated_workspace):
        gas.cmd_create("Test Skill", "step 1 step 2 step 3")
        gas.cmd_retire("test-skill")
        state = gas._load_state()
        assert state["skills"]["test-skill"]["status"] == "retired"


# ─── status / list ───────────────────────────────────────────────────

class TestDashboard:
    def test_status_empty(self, isolated_workspace, capsys):
        gas.cmd_status()
        out = capsys.readouterr().out
        assert "Empty" in out

    def test_status_with_skills(self, isolated_workspace, capsys):
        gas.cmd_create("Skill A", "step 1 step 2 step 3")
        gas.cmd_create("Skill B", "exec python script parse output")
        gas.cmd_record("skill-a", "success")
        gas.cmd_status()
        out = capsys.readouterr().out
        assert "Total skills: 2" in out

    def test_list_returns_entries(self, isolated_workspace):
        gas.cmd_create("Skill A", "step 1 step 2 step 3")
        result = gas.cmd_list()
        assert len(result) == 1
        assert result[0]["id"] == "skill-a"


# ─── cleanup ─────────────────────────────────────────────────────────

class TestCleanup:
    def test_cleanup_removes_retired(self, isolated_workspace):
        gas.cmd_create("Dead Skill", "step 1 step 2 step 3")
        gas.cmd_retire("dead-skill")
        gas.cmd_cleanup()
        state = gas._load_state()
        assert "dead-skill" not in state["skills"]
        assert not (isolated_workspace / "skills" / ".auto" / "dead-skill").exists()

    def test_cleanup_keeps_active(self, isolated_workspace):
        gas.cmd_create("Good Skill", "step 1 step 2 step 3")
        gas.cmd_promote("good-skill")
        gas.cmd_cleanup()
        state = gas._load_state()
        assert "good-skill" in state["skills"]


# ─── helpers ─────────────────────────────────────────────────────────

class TestHelpers:
    def test_keyword_extraction(self):
        kw = gas._extract_keywords("Create a Meta Ads campaign with browser automation")
        assert "meta" in kw
        assert "campaign" in kw
        assert "browser" in kw
        # Stop words excluded
        assert "a" not in kw
        assert "with" not in kw

    def test_keyword_similarity(self):
        kw1 = ["meta", "ads", "campaign", "browser"]
        kw2 = ["meta", "campaign", "budget", "audience"]
        sim = gas._keyword_similarity(kw1, kw2)
        assert 0.2 < sim < 0.6  # Partial overlap

    def test_keyword_similarity_identical(self):
        kw = ["meta", "ads"]
        assert gas._keyword_similarity(kw, kw) == 1.0

    def test_keyword_similarity_disjoint(self):
        assert gas._keyword_similarity(["a", "b"], ["c", "d"]) == 0.0

    def test_skill_id_generation(self):
        assert gas._skill_id("Meta Campaign Creator") == "meta-campaign-creator"
        assert gas._skill_id("URL Summarizer v2!") == "url-summarizer-v2"
