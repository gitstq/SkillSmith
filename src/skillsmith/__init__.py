"""SkillSmith - manage agent skill packages end to end.

Public API surface:

    from skillsmith import Scaffold, SkillValidator, SkillPackager, SkillInstaller

    Scaffold.new_skill(path, name=..., description=...)
    SkillValidator(path).validate()  -> ValidationReport
    SkillPackager(path).pack(out_dir) -> Path
    SkillInstaller().install(pkg_path, target_dir) -> InstalledSkill

Everything is implemented with the Python standard library only, so the
library and the CLI can run in any Python >= 3.9 environment.
"""

from skillsmith.models import (
    InstalledSkill,
    SkillManifest,
    ValidationIssue,
    ValidationReport,
    parse_frontmatter,
)
from skillsmith.scaffold import Scaffold
from skillsmith.validator import SkillValidator
from skillsmith.packager import SkillPackager
from skillsmith.installer import SkillInstaller

__version__ = "1.0.0"

__all__ = [
    "InstalledSkill",
    "SkillInstaller",
    "SkillManifest",
    "SkillPackager",
    "SkillValidator",
    "Scaffold",
    "ValidationIssue",
    "ValidationReport",
    "parse_frontmatter",
    "__version__",
]
