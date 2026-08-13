from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".pack", ".save", ".replay", ".exe", ".dll", ".key"}
FORBIDDEN_NAMES = {".env"}
IGNORED_PARTS = {".git", "__pycache__", ".cache", "build", "dist", "out", "tmp"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json_file(path: Path) -> object:
    # Windows PowerShell 5.1 writes UTF-8 with a BOM. Canonical public-safe
    # evidence may preserve those exact bytes, so validation must decode both
    # BOM and non-BOM UTF-8 without rewriting the artifact.
    return json.loads(path.read_text(encoding="utf-8-sig"))


def tracked_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if relative.as_posix() == "SHA256SUMS.txt":
            continue
        if relative.parts and relative.parts[0] == "local_inputs" and relative.as_posix() != "local_inputs/.gitkeep":
            continue
        files.append(path)
    return sorted(files)


def validate_manifest(files: list[Path]) -> list[str]:
    errors: list[str] = []
    manifest_path = ROOT / "SHA256SUMS.txt"
    if not manifest_path.exists():
        return ["SHA256SUMS.txt is missing"]
    expected: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        expected[relative] = digest
    actual_paths = {path.relative_to(ROOT).as_posix() for path in files}
    if actual_paths != set(expected):
        missing = sorted(set(expected) - actual_paths)
        extra = sorted(actual_paths - set(expected))
        if missing:
            errors.append(f"manifest paths missing from repository: {missing}")
        if extra:
            errors.append(f"repository paths missing from manifest: {extra}")
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if expected.get(relative) != sha256(path):
            errors.append(f"hash mismatch: {relative}")
    return errors


def main() -> int:
    files = tracked_files()
    errors: list[str] = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name.lower() in FORBIDDEN_NAMES:
            errors.append(f"forbidden repository artifact: {relative}")
        if path.suffix.lower() == ".json":
            try:
                load_json_file(path)
            except Exception as error:
                errors.append(f"invalid JSON {relative}: {error}")
    errors.extend(validate_manifest(files))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = str(ROOT / "synthetic_lab")
    completed = subprocess.run(
        [sys.executable, "-m", "transcendence_lab.cli", "test"],
        cwd=ROOT,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        return completed.returncode

    runtime_tests = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(ROOT / "runtime_probe" / "tests"),
            "-p",
            "test_*.py",
            "-v",
        ],
        cwd=ROOT,
        env=env,
        check=False,
    )
    if runtime_tests.returncode != 0:
        return runtime_tests.returncode

    print(f"PASS repository validation ({len(files)} hashed files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
