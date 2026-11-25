"""Command line interface for SkillSmith.

Exit codes:
    0  success
    1  validation failed / runtime error
    2  usage error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skillsmith import __version__
from skillsmith.installer import SkillInstaller
from skillsmith.packager import SkillPackager
from skillsmith.scaffold import Scaffold
from skillsmith.validator import SkillValidator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillsmith",
        description="Scaffold, validate, pack and install agent skill packages.",
    )
    parser.add_argument("--version", action="version", version=f"skillsmith {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_new = sub.add_parser("new", help="create a new skill skeleton")
    p_new.add_argument("name", help="skill name in kebab-case")
    p_new.add_argument("-d", "--dir", default=".", help="base directory (default: .)")
    p_new.add_argument("--description", default="", help="short description")

    p_val = sub.add_parser("validate", help="validate a skill directory")
    p_val.add_argument("path", help="skill directory")
    p_val.add_argument("--strict", action="store_true", help="treat warnings as errors")

    p_pack = sub.add_parser("pack", help="pack a skill directory into a .skill archive")
    p_pack.add_argument("path", help="skill directory")
    p_pack.add_argument("-o", "--out", default="dist", help="output directory (default: dist)")

    p_install = sub.add_parser("install", help="install a .skill package")
    p_install.add_argument("package", help="path to the .skill file")
    p_install.add_argument("-t", "--target", default="~/.agents/skills", help="target skills directory")
    p_install.add_argument("-f", "--force", action="store_true", help="replace an installed version")

    p_list = sub.add_parser("list", help="list installed skills")
    p_list.add_argument("-t", "--target", default="~/.agents/skills", help="target skills directory")

    p_un = sub.add_parser("uninstall", help="remove an installed skill")
    p_un.add_argument("name", help="installed skill name")
    p_un.add_argument("-t", "--target", default="~/.agents/skills", help="target skills directory")
    return parser


def _print_report(report) -> int:
    for issue in report.issues:
        print(f"  [{issue.severity.upper():7}] {issue.code}: {issue.message}")
    if report.ok:
        w = len(report.warnings)
        suffix = f" ({w} warning{'s' if w != 1 else ''})" if w else ""
        print(f"OK: {report.path} passed validation{suffix}")
        return 0
    print(f"FAILED: {report.path} has {len(report.errors)} error(s)")
    return 1


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2

    try:
        if args.command == "new":
            path = Scaffold().new_skill(Path(args.dir), args.name, description=args.description)
            print(f"Created skill skeleton at {path}")
            print("Next: skillsmith validate " + str(path))
            return 0

        if args.command == "validate":
            return _print_report(SkillValidator(Path(args.path), strict=args.strict).validate())

        if args.command == "pack":
            # validate first: never pack a broken skill
            report = SkillValidator(Path(args.path)).validate()
            if not report.ok:
                print("Refusing to pack an invalid skill:")
                return _print_report(report)
            target = SkillPackager(Path(args.path)).pack(Path(args.out))
            print(f"Packed: {target}")
            return 0

        if args.command == "install":
            installer = SkillInstaller(Path(args.target).expanduser())
            installed = installer.install(Path(args.package), force=args.force)
            print(f"Installed {installed.name} {installed.version} -> {args.target}")
            return 0

        if args.command == "list":
            installer = SkillInstaller(Path(args.target).expanduser())
            rows = installer.list_installed()
            if not rows:
                print("No skills installed.")
                return 0
            print(f"{'NAME':24} {'VERSION':10} INSTALLED AT")
            for row in rows:
                print(f"{row.name:24} {row.version:10} {row.installed_at}")
            return 0

        if args.command == "uninstall":
            installer = SkillInstaller(Path(args.target).expanduser())
            installer.uninstall(args.name)
            print(f"Uninstalled {args.name}")
            return 0
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


def run() -> None:
    """Console-script entry point that maps the return code to exit status."""
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())
