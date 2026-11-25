<div align="center">

# 🛠️ SkillSmith

**Zero-dependency CLI toolkit to scaffold, validate, pack and install agent skill packages.**

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

</div>

---

## 🎉 Introduction

Agent skill packages are becoming the standard building blocks of AI workflows, yet there is still no unified toolchain for **creating, validating, distributing and installing** them. SkillSmith looks at the product logic of mainstream agent skills frameworks and ships an original, end-to-end lifecycle manager:

- **Pure Python standard library** — zero third-party runtime dependencies, ready to run on any Python ≥ 3.9 environment
- One command takes you through "scaffold → validate → pack → install → manage"
- A built-in SHA-256 manifest detects tampered packages at install time

## ✨ Features

| Feature | Description |
| --- | --- |
| 🏗️ `new` | Generates a well-formed skill skeleton: `SKILL.md` (YAML frontmatter) + `scripts/` + `references/` |
| ✅ `validate` | Structural and policy checks: naming conventions, required fields, semantic versions, size limits — with `--strict` mode and injectable custom rules |
| 📦 `pack` | Bundles skills into `.skill` archives (gzip tar) with a per-file SHA-256 manifest and byte-reproducible output |
| 🚀 `install` | Verifies the manifest, unpacks, installs idempotently; conflicts require `--force` |
| 📋 `list` / `uninstall` | Registry-based (`installed.json`) lifecycle management |
| 🔌 Library mode | Also usable as a library: `Scaffold` / `SkillValidator` / `SkillPackager` / `SkillInstaller` |

## 🚀 Quick Start

```bash
# Install from source
pip install git+https://github.com/gitstq/SkillSmith.git

# Full flow in 30 seconds
skillsmith new my-skill --description "My first skill package"
skillsmith validate my-skill
skillsmith pack my-skill -o dist
skillsmith install dist/my-skill-0.1.0.skill -t ~/.agents/skills
skillsmith list -t ~/.agents/skills
```

Install from source:

```bash
git clone https://github.com/gitstq/SkillSmith.git
cd SkillSmith && pip install .
```

## 📖 Usage Guide

### Validation rules

- `name`: lowercase kebab-case (letters, digits, hyphens; 2-64 chars)
- `description`: required; warns when it exceeds 1024 characters
- `version`: semantic `MAJOR.MINOR.PATCH`
- Warnings for missing `README.md` or build artifacts such as `__pycache__`
- `--strict` promotes warnings to errors; `extra_rules` lets teams inject custom policies

### Library example

```python
from pathlib import Path
from skillsmith import Scaffold, SkillValidator, SkillPackager, SkillInstaller

skill = Scaffold().new_skill(Path("skills"), "lint-docs", description="Doc linting")
report = SkillValidator(skill).validate()
if report.ok:
    pkg = SkillPackager(skill).pack(Path("dist"))
    SkillInstaller(Path.home() / ".agents/skills").install(pkg)
```

### `.skill` package layout

```
manifest.json          # metadata + size/SHA-256 for every file
payload/...            # the skill files themselves
```

## 💡 Design & Roadmap

- `v1.0.0`: initial release. Full lifecycle management, tamper-evident SHA-256 manifests, and deterministic archives (fixed mtime/uid) so identical content packs to identical bytes
- Planned: signature verification (ed25519), skill dependency resolution, remote registries

## 📦 Build & Deploy

```bash
# Build wheel and sdist
bash build.sh          # artifacts land in dist/

# Run the test suite
python -m pytest tests/ -v
```

## 🤝 Contributing

Issues and PRs are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first; commit messages follow the Angular convention (`feat:` / `fix:` / `docs:` / `refactor:` / `test:`).

## 📄 License

Released under the [MIT License](LICENSE).
