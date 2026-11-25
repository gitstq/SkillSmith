"""Installation: unpack .skill archives into a skills directory and
maintain a small registry (installed.json) for `skillsmith list`.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from skillsmith.models import InstalledSkill
from skillsmith.packager import sha256_file

REGISTRY_NAME = "installed.json"


class SkillInstaller:
    """Install and uninstall ``.skill`` packages under a target directory."""

    def __init__(self, target_dir: Path):
        self.target_dir = Path(target_dir)

    # -- registry ---------------------------------------------------------

    def _registry_path(self) -> Path:
        return self.target_dir / REGISTRY_NAME

    def _read_registry(self) -> dict:
        reg = self._registry_path()
        if reg.is_file():
            try:
                return json.loads(reg.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return {"skills": {}}

    def _write_registry(self, registry: dict) -> None:
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self._registry_path().write_text(
            json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8"
        )

    def list_installed(self) -> List[InstalledSkill]:
        registry = self._read_registry()
        out: List[InstalledSkill] = []
        for name, meta in sorted(registry.get("skills", {}).items()):
            out.append(
                InstalledSkill(
                    name=name,
                    version=str(meta.get("version", "?")),
                    installed_at=str(meta.get("installed_at", "")),
                    files=list(meta.get("files", [])),
                    package_sha256=str(meta.get("package_sha256", "")),
                )
            )
        return out

    # -- install / uninstall ----------------------------------------------

    def install(self, package_path: Path, force: bool = False) -> InstalledSkill:
        """Verify and unpack ``package_path`` into the target directory.

        Raises ValueError on missing checksums, mismatched hashes or when
        a different version of the same skill is already installed and
        ``force`` is False.
        """
        package_path = Path(package_path)
        if not package_path.is_file():
            raise ValueError(f"package not found: {package_path}")

        package_sha = sha256_file(package_path)
        with tarfile.open(package_path, "r:gz") as tar:
            members = {m.name: m for m in tar.getmembers()}
            if "manifest.json" not in members:
                raise ValueError("corrupt package: manifest.json missing")
            manifest = json.load(tar.extractfile(members["manifest.json"]))  # type: ignore[union-attr]

            name = manifest.get("name")
            version = str(manifest.get("version", "0.0.0"))
            files_meta = {f["path"]: f for f in manifest.get("files", [])}
            if not name or not files_meta:
                raise ValueError("corrupt manifest: name/files are required")

            dest = self.target_dir / name
            existing = self._read_registry()["skills"].get(name)
            if existing and not force:
                if existing.get("package_sha256") == package_sha:
                    # identical package already installed - idempotent
                    return InstalledSkill(
                        name=name,
                        version=str(existing.get("version")),
                        installed_at=str(existing.get("installed_at")),
                        files=list(existing.get("files", [])),
                        package_sha256=package_sha,
                    )
                raise ValueError(
                    f"{name} {existing.get('version')} already installed; use force to replace"
                )

            if dest.exists():
                shutil.rmtree(dest)
            installed_files: List[str] = []
            for rel, meta in sorted(files_meta.items()):
                member_name = f"payload/{rel}"
                member = members.get(member_name)
                if member is None:
                    raise ValueError(f"corrupt package: payload file missing: {rel}")
                fh = tar.extractfile(member)
                if fh is None:
                    raise ValueError(f"payload entry is not a regular file: {rel}")
                data = fh.read()
                if hashlib.sha256(data).hexdigest() != meta["sha256"]:
                    raise ValueError(f"checksum mismatch for {rel}: package may be tampered")
                out_file = dest / rel
                out_file.parent.mkdir(parents=True, exist_ok=True)
                out_file.write_bytes(data)
                installed_files.append(rel)

        registry = self._read_registry()
        entry = {
            "version": version,
            "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "files": installed_files,
            "package_sha256": package_sha,
        }
        registry.setdefault("skills", {})[name] = entry
        self._write_registry(registry)
        return InstalledSkill(
            name=name,
            version=version,
            installed_at=entry["installed_at"],
            files=installed_files,
            package_sha256=package_sha,
        )

    def uninstall(self, name: str) -> None:
        """Remove an installed skill and its registry entry."""
        registry = self._read_registry()
        skills = registry.get("skills", {})
        if name not in skills:
            raise ValueError(f"not installed: {name}")
        dest = self.target_dir / name
        if dest.exists():
            shutil.rmtree(dest)
        del skills[name]
        self._write_registry(registry)
