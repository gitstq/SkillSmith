"""Validation: structural and policy checks for skill directories.

Rules are grouped by code and can be extended via ``extra_rules`` so
teams can enforce house policies without forking the library.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

from skillsmith.models import (
    MAX_SKILL_MD_BYTES,
    NAME_PATTERN,
    ValidationIssue,
    ValidationReport,
    SkillManifest,
    parse_frontmatter,
)

RuleFn = Callable[[Path], List[ValidationIssue]]

# Files that must exist for a skill to be considered complete.
REQUIRED_FILES = ("SKILL.md",)
RECOMMENDED_FILES = ("README.md",)

RESERVED_DIR_NAMES = {"node_modules", "__pycache__", ".git"}


class SkillValidator:
    """Validate a skill directory and return a :class:`ValidationReport`."""

    def __init__(self, path: Path, strict: bool = False, extra_rules: Optional[List[RuleFn]] = None):
        self.path = Path(path)
        self.strict = strict  # treat warnings as failures
        self.extra_rules = list(extra_rules or [])

    def validate(self) -> ValidationReport:
        report = ValidationReport(path=self.path)
        if not self.path.is_dir():
            report.issues.append(
                ValidationIssue("error", "not-a-directory", f"{self.path} is not a directory")
            )
            return report

        for rule in (self._check_required_files, self._check_skill_md,
                     self._check_recommended_files, self._check_reserved_dirs):
            report.issues.extend(rule(self.path))
        for rule in self.extra_rules:
            report.issues.extend(rule(self.path))

        if self.strict:
            for issue in report.warnings:
                issue.severity = "error"
        return report

    # -- individual rules ------------------------------------------------

    def _check_required_files(self, root: Path) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for rel in REQUIRED_FILES:
            if not (root / rel).is_file():
                issues.append(ValidationIssue("error", "missing-file", f"required file missing: {rel}"))
        return issues

    def _check_recommended_files(self, root: Path) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for rel in RECOMMENDED_FILES:
            if not (root / rel).is_file():
                issues.append(
                    ValidationIssue("warning", "missing-readme", f"recommended file missing: {rel}")
                )
        return issues

    def _check_reserved_dirs(self, root: Path) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for child in root.rglob("*"):
            if child.is_dir() and child.name in RESERVED_DIR_NAMES:
                issues.append(
                    ValidationIssue(
                        "warning",
                        "reserved-dir",
                        f"exclude build artifacts from packages: {child.relative_to(root)}",
                    )
                )
        return issues

    def _check_skill_md(self, root: Path) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        skill_md = root / "SKILL.md"
        if not skill_md.is_file():
            return issues  # already reported by _check_required_files

        raw = skill_md.read_bytes()
        if len(raw) > MAX_SKILL_MD_BYTES:
            issues.append(
                ValidationIssue("error", "oversized", f"SKILL.md is {len(raw)} bytes, limit is {MAX_SKILL_MD_BYTES}")
            )
            return issues
        text = raw.decode("utf-8", errors="replace")

        try:
            data = parse_frontmatter(text)
        except ValueError as exc:
            issues.append(ValidationIssue("error", "bad-frontmatter", str(exc)))
            return issues

        name = data.get("name")
        if not isinstance(name, str) or not NAME_PATTERN.match(name or ""):
            issues.append(
                ValidationIssue(
                    "error",
                    "invalid-name",
                    f"frontmatter 'name' {name!r} must match {NAME_PATTERN.pattern}",
                )
            )
        description = data.get("description")
        if not isinstance(description, str) or not description.strip():
            issues.append(ValidationIssue("error", "empty-description", "frontmatter 'description' must not be empty"))
        elif len(description) > 1024:
            issues.append(
                ValidationIssue("warning", "long-description", "description exceeds 1024 chars; keep it concise")
            )
        version = data.get("version")
        if version is not None and not re.match(r"^\d+\.\d+\.\d+$", str(version)):
            issues.append(
                ValidationIssue("error", "bad-version", f"version {version!r} must be semantic (MAJOR.MINOR.PATCH)")
            )

        # body sanity: at least one heading after the frontmatter
        body = text.split("---", 2)[-1]
        if not re.search(r"^#{1,6}\s+\S", body, re.MULTILINE):
            issues.append(
                ValidationIssue("warning", "no-heading", "SKILL.md body has no markdown heading")
            )
        return issues


def load_manifest(root: Path) -> SkillManifest:
    """Convenience helper: parse SKILL.md into a :class:`SkillManifest`.

    Raises ValueError if frontmatter is missing or the required fields
    (name, description) are absent.
    """
    skill_md = Path(root) / "SKILL.md"
    data = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    name = data.get("name")
    description = data.get("description")
    if not isinstance(name, str) or not name:
        raise ValueError("frontmatter 'name' is required")
    if not isinstance(description, str) or not description:
        raise ValueError("frontmatter 'description' is required")
    return SkillManifest(
        name=name,
        description=description,
        version=str(data.get("version", "0.1.0")),
        license=str(data.get("license", "")),
        tags=list(data.get("tags") or []),
        source_path=Path(root),
    )
