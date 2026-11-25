"""Data models and frontmatter parsing for skill packages."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# A skill name must be lowercase, start with a letter or digit, and use
# hyphens as word separators (kebab-case, length limited for FS safety).
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")

# Maximum size of a SKILL.md we are willing to parse/validate.
MAX_SKILL_MD_BYTES = 512 * 1024


@dataclass
class SkillManifest:
    """Parsed frontmatter of a SKILL.md file."""

    name: str
    description: str
    version: str = "0.1.0"
    license: str = ""
    tags: List[str] = field(default_factory=list)
    source_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "license": self.license,
        }
        if self.tags:
            data["tags"] = list(self.tags)
        return data


@dataclass
class ValidationIssue:
    """A single problem found while validating a skill."""

    severity: str  # "error" or "warning"
    code: str      # stable machine-readable code, e.g. "missing-field"
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"[{self.severity}] {self.code}: {self.message}"


@dataclass
class ValidationReport:
    """Aggregated result of a validation run."""

    path: Path
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class InstalledSkill:
    """Metadata recorded after installing a package."""

    name: str
    version: str
    installed_at: str
    files: List[str] = field(default_factory=list)
    package_sha256: str = ""


def parse_frontmatter(text: str) -> Dict[str, Any]:
    """Parse a minimal YAML frontmatter block from SKILL.md content.

    Supported subset (deliberately small, zero dependencies):

        ---
        name: my-skill
        description: "Quoted or plain one-line description"
        version: 1.2.0
        tags:
          - linting
          - docs
        ---

    Returns a dict of scalar values and lists. Raises ValueError when the
    block is missing or malformed.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing frontmatter: file must start with '---'")

    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break
    if end is None:
        raise ValueError("unterminated frontmatter: closing '---' not found")

    data: Dict[str, Any] = {}
    current_list: Optional[List[str]] = None
    for line in lines[1:end]:
        raw = line.rstrip()
        if not raw or raw.lstrip().startswith("#"):
            continue
        # list item under the most recent key
        if re.match(r"^\s+-\s+\S", raw):
            item = raw.split("-", 1)[1].strip().strip("'\"")
            if current_list is None:
                raise ValueError(f"list item without a parent key: {raw.strip()}")
            current_list.append(item)
            continue
        if raw != line.rstrip().strip() and raw.startswith(" "):
            raise ValueError(f"nested mappings are not supported: {raw.strip()}")
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", raw)
        if not m:
            raise ValueError(f"cannot parse frontmatter line: {raw.strip()}")
        key, value = m.group(1), m.group(2).strip()
        value = value.strip("'\"")
        if value == "":
            data[key] = []
            current_list = data[key]
        else:
            data[key] = value
            current_list = None
    return data
