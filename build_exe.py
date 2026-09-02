#!/usr/bin/env python3
"""
Builds the standalone MyPeopleDoc export executable.

Works on Windows, macOS and Linux, and is used as-is
by the GitHub Actions workflow (.github/workflows/build-exe.yml).

Usage:
    python build_exe.py
"""

import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent

REQUIREMENTS = [
    "requirements.txt",
    "requirements-build.txt",
]

APP_NAME = "mypeopledoc-export"


def run(command, env=None):
    print()
    print(f"$ {' '.join(command)}")
    print()

    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)

    subprocess.check_call(command, env=merged_env, cwd=PROJECT_ROOT)


def main():
    python = sys.executable

    for requirement in REQUIREMENTS:
        run([python, "-m", "pip", "install", "-r", requirement])

    # Download Firefox INTO the playwright package (PLAYWRIGHT_BROWSERS_PATH=0)
    # so it can be bundled in the executable.
    run(
        [python, "-m", "playwright", "install", "firefox"],
        env={"PLAYWRIGHT_BROWSERS_PATH": "0"},
    )

    # Clean previous builds.
    for directory in ["build", "dist"]:
        target = (
            PROJECT_ROOT
            / directory
        )

        if target.exists():
            shutil.rmtree(target)

    run([python, "-m", "PyInstaller", "--clean", "--noconfirm", APP_NAME + ".spec"])

    print()
    print("Executable generated:")
    for path in sorted((PROJECT_ROOT / "dist").glob(f"{APP_NAME}*")):
        print(f"  {path}")


if __name__ == "__main__":
    main()
