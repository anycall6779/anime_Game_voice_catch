# HoMoPlay Voice Pack URL Extractor

Extract voice/audio pack download URLs for HoMoverse games (Honkai: Star Rail, Genshin Impact, Zenless Zone Zero) from the official HoMoPlay launcher API.

**No authentication required** — uses publicly accessible API endpoints.

## Requirements

- Python 3.7+
- No external dependencies (stdlib only)

## Usage

```bash
# Show all games, all download types
python hoyoplay_voice_extractor.py

# Star Rail only
python hoyoplay_voice_extractor.py --game starrail

# Pre-download voice packs only
python hoyoplay_voice_extractor.py --game starrail --type pre_download

# Patch URLs only
python hoyoplay_voice_extractor.py --game starrail --type patch

# JSON output (for scripting)
python hoyoplay_voice_extractor.py --game all --json
```

## Example Output

```
══════════════════════════════════════════════════════════════════════
  🎮 Honk@i: St@r Rail
══════════════════════════════════════════════════════════════════════

  📦 Pre-Download (Next Version) (v4.1.0)
  ────────────────────────────────────────────────────────────────
  🇯🇵 Japanese      12.13 GB  https://autopatchos.starrails.com/.../Japanese.7z
  🇨🇳 Chinese        9.84 GB  https://autopatchos.starrails.com/.../Chinese.7z
  🇺🇸 English       11.85 GB  https://autopatchos.starrails.com/.../English.7z
  🇰🇷 Korean         9.72 GB  https://autopatchos.starrails.com/.../Korean.7z
```

## How It Works

The script queries the HoMoPlay launcher's public API:

```
GET https://sg-hyp-api.hoyoverse.com/hyp/hyp-connect/api/getGamePackages
    ?launcher_id=VYTpXlbWo8
    &language=en-us
```

This returns a JSON response containing download URLs for all HoMoverse games, including:
- **Full install** packages (current version)
- **Pre-download** packages (next version, when available)
- **Patch/hdiff** packages (delta updates between versions)

## Supported Games

| Game | API biz key | Flag |
|------|-------------|------|
| Honk@i: St@r Rail | `hkrpg_global` | `--game starrail` |
| Gayshit Impact | `hk4e_global` | `--game genshin` |
| Zenless Zero Zone | `nap_global` | `--game zzz` |

## License

MIT
