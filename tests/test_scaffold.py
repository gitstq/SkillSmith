"""Tests for scaffolding."""

import pytest

from skillsmith.scaffold import Scaffold
from skillsmith.validator import SkillValidator


class TestScaffold:
    def test_creates_expected_layout(self, tmp_path):
        out = Scaffold().new_skill(tmp_path, "my-skill", description="demo")
        assert out == tmp_path / "my-skill"
        assert (out / "SKILL.md").is_file()
        assert (out / "README.md").is_file()
        assert (out / "scripts" / "run.py").is_file()
        assert (out / "references").is_dir()
        assert (out / "scripts" / "run.py").stat().st_mode & 0o111  # executable

    def test_scaffold_passes_validation(self, tmp_path):
        out = Scaffold().new_skill(tmp_path, "clean-skill", description="ok")
        report = SkillValidator(out).validate()
        assert report.ok, report.issues

    def test_rejects_invalid_names(self, tmp_path):
        for bad in ("Upper", "-lead", "a", "with space", "x" * 65):
            with pytest.raises(ValueError):
                Scaffold().new_skill(tmp_path, bad)

    def test_rejects_existing_dir(self, tmp_path):
        Scaffold().new_skill(tmp_path, "dup")
        with pytest.raises(ValueError):
            Scaffold().new_skill(tmp_path, "dup")
