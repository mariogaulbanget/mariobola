#!/usr/bin/env python3
"""
MARIOBOLA
Generate:

1. data/team-files.json
   Daftar seluruh file logo di assets/teams/

2. data/team-logos.json
   Pemetaan nama tim/alias -> file logo berdasarkan
   data/team-aliases.json dan nama file logo.

Generator dijalankan oleh GitHub Actions.
"""

from pathlib import Path
import json
import re
import sys
import unicodedata


ROOT = Path(__file__).resolve().parents[1]

TEAMS_DIR = ROOT / "assets" / "teams"
DATA_DIR = ROOT / "data"

TEAM_FILES_OUTPUT = DATA_DIR / "team-files.json"
TEAM_ALIASES_INPUT = DATA_DIR / "team-aliases.json"
TEAM_LOGOS_OUTPUT = DATA_DIR / "team-logos.json"


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
}


def normalize_name(value: str) -> str:
    """
    Normalisasi nama untuk proses pencarian.

    Contoh:

    "RSC Anderlecht"
        ->
    "rsc anderlecht"

    "Kairat-Almaty"
        ->
    "kairat almaty"

    "Inter_Milan.png"
        ->
    "inter milan"
    """

    value = str(value or "")

    # Hilangkan extension gambar.
    value = re.sub(
        r"\.(png|jpg|jpeg|webp|gif|svg)$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # Hilangkan aksen/diacritics.
    value = unicodedata.normalize("NFD", value)
    value = "".join(
        char
        for char in value
        if unicodedata.category(char) != "Mn"
    )

    value = value.casefold()

    # Separator menjadi spasi.
    value = re.sub(r"[_\-]+", " ", value)

    # Karakter selain huruf/angka menjadi spasi.
    value = re.sub(r"[^a-z0-9]+", " ", value)

    # Rapikan spasi.
    value = re.sub(r"\s+", " ", value).strip()

    return value


def tokens(value: str) -> set[str]:
    return set(normalize_name(value).split())


def load_json(path: Path, default):
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        print(
            f"ERROR: JSON tidak valid: {path}\n"
            f"       {exc}",
            file=sys.stderr,
        )
        raise


def save_json_if_changed(path: Path, data) -> bool:
    """
    Menulis JSON hanya jika isinya berubah.

    Return:
        True  = file berubah
        False = tidak berubah
    """

    new_content = (
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )

    old_content = (
        path.read_text(encoding="utf-8")
        if path.exists()
        else ""
    )

    if old_content == new_content:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        new_content,
        encoding="utf-8",
    )

    return True


def collect_team_files() -> list[str]:
    """
    Membaca seluruh file logo langsung dari assets/teams/.
    """

    TEAMS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = [
        path.name
        for path in TEAMS_DIR.iterdir()
        if (
            path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
            and not path.name.startswith(".")
        )
    ]

    files.sort(
        key=lambda value: (
            value.casefold(),
            value,
        )
    )

    return files


def normalize_alias_data(raw):
    """
    Mendukung beberapa bentuk team-aliases.json.

    Bentuk sederhana yang direkomendasikan:

    {
      "Kairat Almaty": [
        "Kairat",
        "FC Kairat Almaty"
      ],
      "RSC Anderlecht": [
        "Anderlecht"
      ]
    }

    Juga menerima:

    {
      "Kairat Almaty": {
        "aliases": [
          "Kairat",
          "FC Kairat Almaty"
        ]
      }
    }
    """

    if not isinstance(raw, dict):
        raise ValueError(
            "data/team-aliases.json harus berupa object JSON."
        )

    result = {}

    for canonical, value in raw.items():
        canonical = str(canonical).strip()

        if not canonical:
            continue

        aliases = []

        if isinstance(value, list):
            aliases = value

        elif isinstance(value, dict):
            aliases = value.get("aliases", [])

        elif isinstance(value, str):
            aliases = [value]

        if not isinstance(aliases, list):
            aliases = []

        clean_aliases = []

        for alias in aliases:
            alias = str(alias).strip()

            if alias:
                clean_aliases.append(alias)

        result[canonical] = clean_aliases

    return result


def score_logo_match(team_name: str, candidate: str) -> int:
    """
    Menghitung tingkat kecocokan nama tim dengan filename logo.

    Semakin tinggi skor, semakin spesifik kecocokannya.

    PENTING:
    Kita tidak memberi skor hanya karena satu kata pendek
    seperti "inter" muncul di filename.
    """

    team = normalize_name(team_name)
    file_name = normalize_name(candidate)

    if not team or not file_name:
        return 0

    if team == file_name:
        return 10000

    team_tokens = tokens(team)
    file_tokens = tokens(file_name)

    if not team_tokens or not file_tokens:
        return 0

    # Nama tim lengkap terdapat sebagai rangkaian token lengkap.
    if team in file_name:
        score = 7000

        # Semakin mirip jumlah token, semakin tinggi.
        score += min(
            len(team_tokens) * 250,
            1500,
        )

        return score

    # Filename terdapat penuh di dalam nama tim.
    if file_name in team:
        score = 6500
        score += min(
            len(file_tokens) * 200,
            1200,
        )
        return score

    # Cocokkan token lengkap.
    common = team_tokens & file_tokens

    if not common:
        return 0

    # Jangan mempercayai satu token pendek.
    if len(common) == 1:
        only = next(iter(common))

        if len(only) < 5:
            return 0

    coverage = len(common) / max(
        len(team_tokens),
        1,
    )

    score = int(
        coverage * 4500
        + len(common) * 500
    )

    # Penalti jika ada banyak token filename yang
    # tidak berhubungan.
    extra_tokens = file_tokens - team_tokens

    score -= min(
        len(extra_tokens) * 80,
        500,
    )

    return max(score, 0)


def find_best_logo(team_name: str, files: list[str]) -> str | None:
    """
    Cari logo paling cocok.

    Return None apabila tidak ditemukan kecocokan
    yang cukup aman.
    """

    if not team_name:
        return None

    candidates = []

    for file_name in files:
        score = score_logo_match(
            team_name,
            file_name,
        )

        if score > 0:
            candidates.append(
                (
                    score,
                    file_name,
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1].casefold(),
        )
    )

    best_score, best_file = candidates[0]

    # Ambang keamanan.
    #
    # Kita sengaja tidak memaksakan logo kalau
    # kecocokannya terlalu lemah.
    if best_score < 2500:
        return None

    return best_file


def build_team_logo_map(
    aliases: dict,
    files: list[str],
) -> dict:
    """
    Membuat:

    {
      "Kairat Almaty": "assets/teams/....png",
      "Anderlecht": "assets/teams/....png"
    }
    """

    result = {}

    for canonical, alias_list in aliases.items():

        names_to_check = [
            canonical,
            *alias_list,
        ]

        best_match = None
        best_score = 0

        for name in names_to_check:

            for file_name in files:

                score = score_logo_match(
                    name,
                    file_name,
                )

                if score > best_score:
                    best_score = score
                    best_match = file_name

        if best_match and best_score >= 2500:

            result[canonical] = (
                f"assets/teams/{best_match}"
            )

    return dict(
        sorted(
            result.items(),
            key=lambda item: item[0].casefold(),
        )
    )


def main() -> int:

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # =========================================================
    # 1. TEAM FILES
    # =========================================================

    files = collect_team_files()

    changed_files = save_json_if_changed(
        TEAM_FILES_OUTPUT,
        files,
    )

    if changed_files:
        print(
            f"team-files.json diperbarui: "
            f"{len(files)} logo"
        )
    else:
        print(
            f"team-files.json sudah terbaru: "
            f"{len(files)} logo"
        )

    # =========================================================
    # 2. TEAM ALIASES
    # =========================================================

    raw_aliases = load_json(
        TEAM_ALIASES_INPUT,
        {},
    )

    aliases = normalize_alias_data(
        raw_aliases
    )

    print(
        f"team-aliases.json dibaca: "
        f"{len(aliases)} nama tim"
    )

    # =========================================================
    # 3. TEAM LOGOS
    # =========================================================

    team_logos = build_team_logo_map(
        aliases,
        files,
    )

    changed_logos = save_json_if_changed(
        TEAM_LOGOS_OUTPUT,
        team_logos,
    )

    if changed_logos:
        print(
            f"team-logos.json diperbarui: "
            f"{len(team_logos)} logo cocok"
        )
    else:
        print(
            f"team-logos.json sudah terbaru: "
            f"{len(team_logos)} logo cocok"
        )

    # =========================================================
    # 4. LAPORAN
    # =========================================================

    missing = [
        name
        for name in aliases
        if name not in team_logos
    ]

    if missing:
        print("")
        print(
            "PERINGATAN: beberapa nama tim "
            "belum mendapatkan logo:"
        )

        for name in missing:
            print(
                f"  - {name}"
            )

    print("")
    print("Generator selesai.")

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
