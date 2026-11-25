"""End-to-end tests: scaffold -> pack -> install -> list -> uninstall,
plus tamper detection and CLI exit codes.
"""

import hashlib
import subprocess
import sys
import tarfile

import pytest

from skillsmith.cli import main
from skillsmith.installer import SkillInstaller
from skillsmith.packager import SkillPackager
from skillsmith.scaffold import Scaffold


@pytest.fixture()
def skill_pkg(tmp_path):
    skill = Scaffold().new_skill(tmp_path / "base", "e2e-skill", description="e2e test")
    (skill / "SKILL.md").write_text(
        "---\nname: e2e-skill\ndescription: e2e test\nversion: 1.0.0\n---\n\n# E2E\n",
        encoding="utf-8",
    )
    return SkillPackager(skill).pack(tmp_path / "dist")


class TestInstaller:
    def test_install_and_list(self, tmp_path, skill_pkg):
        installer = SkillInstaller(tmp_path / "skills")
        installed = installer.install(skill_pkg)
        assert installed.name == "e2e-skill"
        assert installed.version == "1.0.0"
        assert (tmp_path / "skills" / "e2e-skill" / "SKILL.md").is_file()
        names = [r.name for r in installer.list_installed()]
        assert names == ["e2e-skill"]

    def test_idempotent_reinstall(self, tmp_path, skill_pkg):
        installer = SkillInstaller(tmp_path / "skills")
        first = installer.install(skill_pkg)
        second = installer.install(skill_pkg)
        assert first.package_sha256 == second.package_sha256

    def test_conflict_requires_force(self, tmp_path, skill_pkg):
        installer = SkillInstaller(tmp_path / "skills")
        installer.install(skill_pkg)
        # repack the same skill with different content
        other = tmp_path / "base2" / "e2e-skill"
        Scaffold().new_skill(tmp_path / "base2", "e2e-skill", description="other")
        (other / "SKILL.md").write_text(
            "---\nname: e2e-skill\ndescription: other\nversion: 1.0.0\n---\n\n# Other\n",
            encoding="utf-8",
        )
        other_pkg = SkillPackager(other).pack(tmp_path / "dist")
        with pytest.raises(ValueError):
            installer.install(other_pkg)
        installer.install(other_pkg, force=True)
        assert installer.list_installed()[0].version == "1.0.0"

    def test_uninstall(self, tmp_path, skill_pkg):
        installer = SkillInstaller(tmp_path / "skills")
        installer.install(skill_pkg)
        installer.uninstall("e2e-skill")
        assert installer.list_installed() == []
        assert not (tmp_path / "skills" / "e2e-skill").exists()

    def test_uninstall_unknown(self, tmp_path):
        with pytest.raises(ValueError):
            SkillInstaller(tmp_path / "skills").uninstall("ghost")

    def test_tampered_package_rejected(self, tmp_path, skill_pkg):
        # rewrite one payload byte inside the archive
        tampered = tmp_path / "tampered.skill"
        with tarfile.open(skill_pkg, "r:gz") as tar:
            members = tar.getmembers()
            extracts = {m.name: tar.extractfile(m).read() for m in members}
        extracts["payload/SKILL.md"] = extracts["payload/SKILL.md"] + b"EVIL\n"
        import io

        with tarfile.open(tampered, "w:gz") as tar:
            for name, data in extracts.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        installer = SkillInstaller(tmp_path / "skills")
        with pytest.raises(ValueError, match="checksum mismatch"):
            installer.install(tampered)


class TestCli:
    def test_full_flow_via_cli(self, tmp_path, capsys):
        base = tmp_path / "proj"
        assert main(["new", "cli-flow", "-d", str(base), "--description", "cli test"]) == 0
        skill = base / "cli-flow"
        assert main(["validate", str(skill)]) == 0
        assert main(["pack", str(skill), "-o", str(tmp_path / "dist")]) == 0
        pkg = tmp_path / "dist" / "cli-flow-0.1.0.skill"
        assert pkg.is_file()
        target = tmp_path / "skills"
        assert main(["install", str(pkg), "-t", str(target)]) == 0
        assert main(["list", "-t", str(target)]) == 0
        assert main(["uninstall", "cli-flow", "-t", str(target)]) == 0

    def test_validate_failure_exit_code(self, tmp_path, capsys):
        bad = tmp_path / "bad"
        bad.mkdir()
        (bad / "SKILL.md").write_text("# broken\n", encoding="utf-8")
        assert main(["validate", str(bad)]) == 1

    def test_no_command_shows_help(self, capsys):
        assert main([]) == 2

    def test_module_invocation(self):
        proc = subprocess.run(
            [sys.executable, "-m", "skillsmith.cli", "--version"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0
        assert "skillsmith" in proc.stdout
