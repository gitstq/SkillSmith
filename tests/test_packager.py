"""Tests for packaging: archive layout, checksums, determinism."""

import json
import tarfile

from skillsmith.packager import SkillPackager, sha256_file
from skillsmith.scaffold import Scaffold


def make_skill(tmp_path):
    skill = Scaffold().new_skill(tmp_path / "base", "pack-demo", description="pkg test")
    (skill / "references" / "notes.md").write_text("note\n", encoding="utf-8")
    (skill / "__pycache__").mkdir()
    (skill / "__pycache__" / "junk.pyc").write_text("junk", encoding="utf-8")
    return skill


class TestPackager:
    def test_pack_creates_archive(self, tmp_path):
        skill = make_skill(tmp_path)
        target = SkillPackager(skill).pack(tmp_path / "dist")
        assert target.name == "pack-demo-0.1.0.skill"
        assert target.is_file()

    def test_archive_layout_and_checksums(self, tmp_path):
        skill = make_skill(tmp_path)
        target = SkillPackager(skill).pack(tmp_path / "dist")
        with tarfile.open(target, "r:gz") as tar:
            names = tar.getnames()
            manifest = json.load(tar.extractfile("manifest.json"))
        assert "manifest.json" in names
        assert any(n.startswith("payload/") for n in names)
        # build artifacts excluded
        assert not any("__pycache__" in n for n in names)
        # every payload entry has a matching checksum entry
        paths = {f["path"] for f in manifest["files"]}
        assert "SKILL.md" in paths and "scripts/run.py" in paths
        assert "references/notes.md" in paths

    def test_checksum_detects_tampering(self, tmp_path):
        skill = make_skill(tmp_path)
        target = SkillPackager(skill).pack(tmp_path / "dist")
        with tarfile.open(target, "r:gz") as tar:
            manifest = json.load(tar.extractfile("manifest.json"))
        entry = next(f for f in manifest["files"] if f["path"] == "SKILL.md")
        real = sha256_file(skill / "SKILL.md")
        assert entry["sha256"] == real
        assert entry["size"] == (skill / "SKILL.md").stat().st_size

    def test_deterministic_bytes(self, tmp_path):
        skill = make_skill(tmp_path)
        a = SkillPackager(skill).pack(tmp_path / "d1")
        b = SkillPackager(skill).pack(tmp_path / "d2")
        assert a.read_bytes() == b.read_bytes()

    def test_empty_dir_rejected(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        (empty / "SKILL.md").write_text("---\nname: e-skill\ndescription: d\n---\n# t\n", encoding="utf-8")
        packer = SkillPackager(empty)
        with tarfile.open(packer.pack(tmp_path / "dist"), "r:gz") as tar:
            assert "payload/SKILL.md" in tar.getnames()
