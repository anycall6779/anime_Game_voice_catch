"""
HoYoPlay Voice Pack URL Extractor
==================================
Extracts pre-download voice pack URLs for HoYoverse games from the official HoYoPlay API.
No authentication required - uses publicly accessible launcher API endpoints.

Supported Games:
  - Honkai: Star Rail (hkrpg_global)
  - Genshin Impact (hk4e_global)
  - Zenless Zone Zero (nap_global)

Usage:
  python hoyoplay_voice_extractor.py
  python hoyoplay_voice_extractor.py --game starrail
  python hoyoplay_voice_extractor.py --game starrail --type pre_download
  python hoyoplay_voice_extractor.py --game all --json

Author: Generated via HoYoPlay API reverse engineering
API Endpoint: https://sg-hyp-api.hoyoverse.com/hyp/hyp-connect/api/getGamePackages
"""

import json
import sys
import os
import io
import argparse
import urllib.request
import ssl
from datetime import datetime


# ─────────────────────── Output Tee ──────────────────────────────

class TeeOutput:
    """Write to both console and file simultaneously."""

    def __init__(self, filepath):
        self.console = sys.stdout
        self.file = open(filepath, "w", encoding="utf-8")

    def write(self, text):
        self.console.write(text)
        self.file.write(text)

    def flush(self):
        self.console.flush()
        self.file.flush()

    def close(self):
        self.file.close()


# ─────────────────────── API Configuration ───────────────────────

API_URL = "https://sg-hyp-api.hoyoverse.com/hyp/hyp-connect/api/getGamePackages"
LAUNCHER_ID = "VYTpXlbWo8"  # HoYoPlay Global launcher ID

GAME_BIZ_MAP = {
    "starrail": "hkrpg_global",
    "genshin":  "hk4e_global",
    "zzz":      "nap_global",
}

GAME_NAMES = {
    "hkrpg_global": "Honkai: Star Rail",
    "hk4e_global":  "Genshin Impact",
    "nap_global":   "Zenless Zone Zero",
}

LANG_NAMES = {
    "ja-jp": "🇯🇵 Japanese",
    "zh-cn": "🇨🇳 Chinese",
    "en-us": "🇺🇸 English",
    "ko-kr": "🇰🇷 Korean",
}


# ─────────────────────── API Functions ───────────────────────────

def fetch_game_packages():
    """Fetch all game packages from HoYoPlay API."""
    url = f"{API_URL}?launcher_id={LAUNCHER_ID}&language=en-us"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })

    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("retcode") != 0:
        raise RuntimeError(f"API error: {data.get('message', 'Unknown error')}")

    return data["data"]["game_packages"]


def find_game(packages, biz_key):
    """Find a specific game in the packages list by biz key."""
    for pkg in packages:
        if pkg.get("game", {}).get("biz") == biz_key:
            return pkg
    return None


def format_size(size_bytes):
    """Format byte size to human readable string."""
    size = int(size_bytes) if isinstance(size_bytes, str) else size_bytes
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 ** 3:
        return f"{size / 1024**2:.1f} MB"
    else:
        return f"{size / 1024**3:.2f} GB"


# ─────────────────────── Extraction Logic ────────────────────────

def extract_audio_info(game_data):
    """Extract all audio package info from a game's data."""
    result = {
        "game": GAME_NAMES.get(game_data["game"]["biz"], game_data["game"]["biz"]),
        "biz": game_data["game"]["biz"],
        "current": None,
        "pre_download": None,
        "patches": [],
    }

    # Current version (full install)
    main = game_data.get("main", {})
    major = main.get("major", {})
    if major:
        version = major.get("version", "?")
        audio_pkgs = major.get("audio_pkgs", [])
        result["current"] = {
            "version": version,
            "audio_pkgs": audio_pkgs,
        }

    # Patches
    for patch in main.get("patches", []):
        patch_version = patch.get("version", "?")
        target_version = major.get("version", "?") if major else "?"
        result["patches"].append({
            "from_version": patch_version,
            "to_version": target_version,
            "audio_pkgs": patch.get("audio_pkgs", []),
        })

    # Pre-download (next version)
    pre = game_data.get("pre_download", {})
    pre_major = pre.get("major") if pre else None
    if pre_major:
        pre_version = pre_major.get("version", "?")
        pre_audio = pre_major.get("audio_pkgs", [])
        result["pre_download"] = {
            "version": pre_version,
            "audio_pkgs": pre_audio,
        }

        # Pre-download patches
        for patch in pre.get("patches", []):
            patch_version = patch.get("version", "?")
            result["patches"].append({
                "from_version": patch_version,
                "to_version": pre_version,
                "audio_pkgs": patch.get("audio_pkgs", []),
                "is_pre_download": True,
            })

    return result


# ─────────────────────── Output Formatters ───────────────────────

def print_section(title, version, audio_pkgs):
    """Print a formatted section of audio packages."""
    if not audio_pkgs:
        return

    print(f"\n  📦 {title} (v{version})")
    print(f"  {'─' * 60}")

    for pkg in audio_pkgs:
        lang = pkg.get("language", "?")
        url = pkg.get("url", "?")
        size = format_size(pkg.get("size", 0))
        lang_name = LANG_NAMES.get(lang, lang)
        print(f"  {lang_name:<16s}  {size:>10s}  {url}")


def print_patches(patches):
    """Print patch audio info."""
    for patch in patches:
        if not patch["audio_pkgs"]:
            continue

        prefix = "[Pre-DL] " if patch.get("is_pre_download") else ""
        title = f"{prefix}Patch {patch['from_version']} → {patch['to_version']}"
        print(f"\n  🔄 {title}")
        print(f"  {'─' * 60}")

        for pkg in patch["audio_pkgs"]:
            lang = pkg.get("language", "?")
            url = pkg.get("url", "?")
            size = format_size(pkg.get("size", 0))
            lang_name = LANG_NAMES.get(lang, lang)
            print(f"  {lang_name:<16s}  {size:>10s}  {url}")


def print_game_audio(info, show_type="all"):
    """Print all audio info for a game."""
    print(f"\n{'═' * 70}")
    print(f"  🎮 {info['game']}")
    print(f"{'═' * 70}")

    if show_type in ("all", "current") and info["current"]:
        print_section("Full Install", info["current"]["version"],
                      info["current"]["audio_pkgs"])

    if show_type in ("all", "pre_download") and info["pre_download"]:
        print_section("Pre-Download (Next Version)", info["pre_download"]["version"],
                      info["pre_download"]["audio_pkgs"])

    if show_type in ("all", "patch") and info["patches"]:
        print_patches(info["patches"])

    if show_type == "pre_download" and not info["pre_download"]:
        print("\n  ⚠️  No pre-download available at this time.")


def output_json(results):
    """Output results as JSON."""
    output = []
    for info in results:
        entry = {"game": info["game"], "biz": info["biz"]}

        if info["current"]:
            entry["current_version"] = info["current"]["version"]
            entry["current_audio"] = [
                {"language": p["language"], "url": p["url"],
                 "size": int(p.get("size", 0)),
                 "size_human": format_size(p.get("size", 0))}
                for p in info["current"]["audio_pkgs"]
            ]

        if info["pre_download"]:
            entry["pre_download_version"] = info["pre_download"]["version"]
            entry["pre_download_audio"] = [
                {"language": p["language"], "url": p["url"],
                 "size": int(p.get("size", 0)),
                 "size_human": format_size(p.get("size", 0))}
                for p in info["pre_download"]["audio_pkgs"]
            ]

        if info["patches"]:
            entry["patches"] = [
                {
                    "from": p["from_version"], "to": p["to_version"],
                    "audio": [
                        {"language": a["language"], "url": a["url"],
                         "size": int(a.get("size", 0)),
                         "size_human": format_size(a.get("size", 0))}
                        for a in p["audio_pkgs"]
                    ]
                }
                for p in info["patches"] if p["audio_pkgs"]
            ]

        output.append(entry)

    print(json.dumps(output, indent=2, ensure_ascii=False))


# ─────────────────────── Main ────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract voice pack download URLs from HoYoPlay API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                            # Show all games, all types
  %(prog)s --game starrail            # Star Rail only
  %(prog)s --game genshin --type pre_download  # Genshin pre-download only
  %(prog)s --game all --json          # All games, JSON output
  %(prog)s --game starrail --type patch        # Star Rail patches only
        """
    )
    parser.add_argument("--game", choices=["starrail", "genshin", "zzz", "all"],
                        default="all", help="Game to query (default: all)")
    parser.add_argument("--type", choices=["all", "current", "pre_download", "patch"],
                        default="all", help="Type of packages to show (default: all)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON instead of formatted text")
    parser.add_argument("--output", "-o", type=str, default="list.txt",
                        help="Output file path (default: list.txt in script directory)")
    parser.add_argument("--no-file", action="store_true",
                        help="Do not save output to file")

    args = parser.parse_args()

    # Setup output file (Tee: print to both console and file)
    tee = None
    if not args.no_file:
        # Resolve output path relative to script directory
        if not os.path.isabs(args.output):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(script_dir, args.output)
        else:
            output_path = args.output

        tee = TeeOutput(output_path)
        sys.stdout = tee

    print(f"🔍 Querying HoYoPlay API...")
    print(f"   Endpoint: {API_URL}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        packages = fetch_game_packages()
    except Exception as e:
        print(f"\n❌ Failed to fetch API: {e}")
        if tee:
            sys.stdout = tee.console
            tee.close()
        sys.exit(1)

    # Determine which games to process
    if args.game == "all":
        target_bizs = list(GAME_BIZ_MAP.values())
    else:
        target_bizs = [GAME_BIZ_MAP[args.game]]

    results = []
    for biz in target_bizs:
        game_data = find_game(packages, biz)
        if game_data:
            info = extract_audio_info(game_data)
            results.append(info)

    if not results:
        print("\n⚠️  No matching games found.")
        if tee:
            sys.stdout = tee.console
            tee.close()
        sys.exit(1)

    # Output
    if args.json:
        output_json(results)
    else:
        for info in results:
            print_game_audio(info, args.type)

        print(f"\n{'─' * 70}")
        print(f"  ✅ Done. URLs can be downloaded with any browser or download manager.")
        print(f"{'─' * 70}\n")

    # Close file output and notify
    if tee:
        sys.stdout = tee.console
        tee.close()
        print(f"  📄 Output saved to: {output_path}")


if __name__ == "__main__":
    main()
