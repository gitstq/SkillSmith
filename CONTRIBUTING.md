# Contributing to SkillSmith

Thanks for your interest in contributing! 🎉

## Development setup

```bash
git clone https://github.com/gitstq/SkillSmith.git
cd SkillSmith
pip install -e .
pip install pytest
python -m pytest tests/ -v
```

## Ground rules

- Python >= 3.9 compatible code only; **no third-party runtime dependencies** (dev tools like pytest are fine).
- Every feature or fix must come with unit tests; keep coverage complete for `src/skillsmith/`.
- Public API changes require updating all three READMEs (`README.md`, `README.zh-TW.md`, `README.en.md`).
- Keep modules small and focused; document public functions with docstrings.

## Commit convention (Angular style)

```
feat: add signature verification for .skill packages
fix: reject frontmatter with duplicate keys
docs: expand installation guide in README
refactor: extract checksum logic into packager
test: cover strict-mode validation
chore: bump version to 1.0.1
```

## Pull request checklist

1. `python -m pytest tests/ -v` passes locally
2. Commit messages follow the Angular convention
3. New user-facing behavior is documented in all three READMEs
4. The PR description explains the motivation and the change

## Reporting issues

Open an issue with: your Python version, OS, the exact command you ran, and the full output (including exit code).
