"""Tests for frontmatter parsing and validation rules."""

import pytest

from skillsmith.models import parse_frontmatter
from skillsmith.validator import SkillValidator, load_manifest


def write_skill_md(path, text):
    (path / "SKILL.md").write_text(text, encoding="utf-8")
    (path / "README.md").write_text("# demo\n", encoding="utf-8")


VALID = """\
---
name: demo-skill
description: A demo skill for tests
version: 1.0.0
license: MIT
tags:
  - demo
  - test
---

# Demo Skill

Body with a heading.
"""


class TestFrontmatter:
    def test_parses_scalars_and_lists(self):
        data = parse_frontmatter(VALID)
        assert data["name"] == "demo-skill"
        assert data["version"] == "1.0.0"
        assert data["tags"] == ["demo", "test"]

    def test_missing_start_marker(self):
        with pytest.raises(ValueError):
            parse_frontmatter("name: x\n")

    def test_unterminated_block(self):
        with pytest.raises(ValueError):
            parse_frontmatter("---\nname: x\n")

    def test_list_item_without_parent(self):
        with pytest.raises(ValueError):
            parse_frontmatter("---\n- item\n---\n")

    def test_nested_mapping_rejected(self):
        with pytest.raises(ValueError):
            parse_frontmatter("---\na:\n  b: 1\n---\n")

    def test_quoted_values(self):
        data = parse_frontmatter('---\ndescription: "hello: world"\n---\n')
        assert data["description"] == "hello: world"


class TestValidator:
    def test_valid_skill_passes(self, tmp_path):
        write_skill_md(tmp_path, VALID)
        report = SkillValidator(tmp_path).validate()
        assert report.ok, report.issues
        assert report.warnings == []

    def test_missing_skill_md(self, tmp_path):
        report = SkillValidator(tmp_path).validate()
        assert not report.ok
        assert any(i.code == "missing-file" for i in report.errors)

    def test_missing_readme_warns(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(VALID, encoding="utf-8")
        report = SkillValidator(tmp_path).validate()
        assert report.ok  # warning only
        assert any(i.code == "missing-readme" for i in report.warnings)

    def test_strict_promotes_warnings(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(VALID, encoding="utf-8")
        report = SkillValidator(tmp_path, strict=True).validate()
        assert not report.ok

    def test_invalid_name(self, tmp_path):
        write_skill_md(tmp_path, VALID.replace("name: demo-skill", "name: Bad Name"))
        report = SkillValidator(tmp_path).validate()
        assert any(i.code == "invalid-name" for i in report.errors)

    def test_empty_description(self, tmp_path):
        write_skill_md(tmp_path, VALID.replace("description: A demo skill for tests", "description:"))
        report = SkillValidator(tmp_path).validate()
        assert any(i.code == "empty-description" for i in report.errors)

    def test_bad_version(self, tmp_path):
        write_skill_md(tmp_path, VALID.replace("version: 1.0.0", "version: v1"))
        report = SkillValidator(tmp_path).validate()
        assert any(i.code == "bad-version" for i in report.errors)

    def test_bad_frontmatter(self, tmp_path):
        write_skill_md(tmp_path, "# no frontmatter\n")
        report = SkillValidator(tmp_path).validate()
        assert any(i.code == "bad-frontmatter" for i in report.errors)

    def test_not_a_directory(self, tmp_path):
        target = tmp_path / "file.txt"
        target.write_text("x", encoding="utf-8")
        report = SkillValidator(target).validate()
        assert any(i.code == "not-a-directory" for i in report.errors)

    def test_extra_rules_run(self, tmp_path):
        write_skill_md(tmp_path, VALID)

        def forbid_tags(root):
            return []  # custom rule hook

        report = SkillValidator(tmp_path, extra_rules=[forbid_tags]).validate()
        assert report.ok


class TestLoadManifest:
    def test_loads_manifest(self, tmp_path):
        write_skill_md(tmp_path, VALID)
        m = load_manifest(tmp_path)
        assert m.name == "demo-skill"
        assert m.version == "1.0.0"
        assert m.tags == ["demo", "test"]
        assert m.license == "MIT"

    def test_missing_required_field(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("---\nname: x-skill\n---\n", encoding="utf-8")
        with pytest.raises(ValueError):
            load_manifest(tmp_path)
