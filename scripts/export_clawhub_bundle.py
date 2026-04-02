#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT_FILES = [
    "SKILL.md",
    "README.md",
    "README_zh.md",
]

SCRIPT_FILES = [
    "scripts/__init__.py",
    "scripts/codex_history.py",
    "scripts/codex_history_manager.py",
]

REFERENCE_DIR = "references"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a clean ClawHub upload bundle without .git or repo-only files."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1].parent / "codex-history-manager-clawhub",
        help="Output directory for the clean bundle.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace the output directory if it already exists.",
    )
    return parser.parse_args()


def copy_file(source_root: Path, target_root: Path, relative_path: str) -> None:
    source = source_root / relative_path
    target = target_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> int:
    args = parse_args()
    source_root = Path(__file__).resolve().parents[1]
    output_root = args.output.expanduser().resolve()

    if output_root.exists():
        if not args.force:
            raise SystemExit(f"Output already exists: {output_root}. Re-run with --force to replace it.")
        shutil.rmtree(output_root)

    output_root.mkdir(parents=True, exist_ok=True)

    for relative_path in ROOT_FILES:
        copy_file(source_root, output_root, relative_path)

    for relative_path in SCRIPT_FILES:
        copy_file(source_root, output_root, relative_path)

    shutil.copytree(source_root / REFERENCE_DIR, output_root / REFERENCE_DIR)

    print(f"Created clean ClawHub bundle at: {output_root}")
    print("Included:")
    for relative_path in ROOT_FILES:
        print(f"  - {relative_path}")
    print(f"  - {REFERENCE_DIR}/")
    for relative_path in SCRIPT_FILES:
        print(f"  - {relative_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
