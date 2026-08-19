#!/usr/bin/env python3
"""
MARIOBOLA - Generate data/team-files.json from assets/teams/
"""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
TEAMS_DIR = ROOT / "assets" / "teams"
OUTPUT = ROOT / "data" / "team-files.json"

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
}

def main() -> int:
    TEAMS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    files = [
        p.name
        for p in TEAMS_DIR.iterdir()
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
        and not p.name.startswith(".")
    ]

    files.sort(key=lambda value: (value.casefold(), value))

    new_content = json.dumps(
        files,
        ensure_ascii=False,
        indent=2
    ) + "\n"

    old_content = (
        OUTPUT.read_text(encoding="utf-8")
        if OUTPUT.exists()
        else ""
    )

    if old_content == new_content:
        print(f"team-files.json sudah terbaru: {len(files)} logo")
        return 0

    OUTPUT.write_text(
        new_content,
        encoding="utf-8"
    )

    print(f"team-files.json diperbarui: {len(files)} logo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
