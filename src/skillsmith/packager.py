"""Packaging: bundle a validated skill directory into a .skill archive.

A ``.skill`` file is a gzipped tar with a deterministic layout:

    manifest.json     - metadata + SHA-256 checksum of every payload file
    payload/...       - the skill files themselves

Checksums make installs tamper-evident and reproducible.
"""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path
from typing import List

from skillsmith.models import SkillManifest
from skillsmith.validator import load_manifest

EXCLUDED_NAMES = {".git", "node_modules", "__pycache__", ".DS_Store"}
SKILL_EXT = ".skill"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root: Path) -> List[Path]:
    """All regular files under root, excluding build artifacts."""
    files: List[Path] = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(part in EXCLUDED_NAMES for part in p.parts):
            files.append(p)
    return files


class SkillPackager:
    """Pack a skill directory into a versioned ``.skill`` archive."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def pack(self, out_dir: Path) -> Path:
        """Create ``<out_dir>/<name>-<version>.skill`` and return its path."""
        manifest: SkillManifest = load_manifest(self.path)
        payload_files = collect_files(self.path)
        if not payload_files:
            raise ValueError(f"skill directory is empty: {self.path}")

        file_entries = [
            {
                "path": p.relative_to(self.path).as_posix(),
                "size": p.stat().st_size,
                "sha256": sha256_file(p),
            }
            for p in payload_files
        ]
        manifest_json = {
            **manifest.to_dict(),
            "packaged_at_manifest_version": 1,
            "files": file_entries,
        }

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"{manifest.name}-{manifest.version}{SKILL_EXT}"

        with tarfile.open(target, "w:gz") as tar:
            mjson = json.dumps(manifest_json, indent=2, sort_keys=True).encode("utf-8")
            import io

            info = tarfile.TarInfo("manifest.json")
            info.size = len(mjson)
            tar.addfile(info, io.BytesIO(mjson))
            for p in payload_files:
                tar.add(
                    p,
                    arcname=f"payload/{p.relative_to(self.path).as_posix()}",
                    filter=lambda ti: self._clean(ti),
                )
        return target

    @staticmethod
    def _clean(info: tarfile.TarInfo) -> tarfile.TarInfo:
        """Normalize tar entries for reproducible archives."""
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        info.mtime = 0
        return info
