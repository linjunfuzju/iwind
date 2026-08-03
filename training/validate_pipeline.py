"""Run static and local unit validation for the complete Iwind pipeline."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parent
MODULES = (
    "data_engineering",
    "domain_pretraining",
    "instruction_tuning",
    "reward_modeling",
    "policy_optimization",
    "evaluation_and_integration",
)


def validate_files() -> tuple[int, int]:
    python_files = sorted(ROOT.glob("**/*.py"))
    json_files = sorted(ROOT.glob("**/*.json"))
    for path in python_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for path in json_files:
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)
    for module in MODULES:
        directory = ROOT / module
        for required in ("README.md", "requirements.txt", "__init__.py"):
            if not (directory / required).is_file():
                raise FileNotFoundError(f"Missing {module}/{required}")
    return len(python_files), len(json_files)


def run_tests() -> None:
    for module in MODULES:
        test_directory = ROOT / module / "tests"
        if not test_directory.is_dir():
            raise FileNotFoundError(f"Missing test directory: {test_directory}")
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(test_directory), "-v"],
            cwd=REPOSITORY,
            check=True,
            env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )


def main() -> None:
    python_count, json_count = validate_files()
    run_tests()
    print(f"Validated {python_count} Python files and {json_count} JSON files across {len(MODULES)} modules.")


if __name__ == "__main__":
    main()
