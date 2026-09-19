"""Linux storage and Steam/Proton save discovery (no GUI dependency)."""
import os
import re
from pathlib import Path
from lib.save_paths import game_saves

SAVE_SUFFIX = Path('steamapps/compatdata/3241660/pfx/drive_c/users/steamuser/AppData/LocalLow/semiwork/Repo/saves')


def xdg_path(variable, fallback):
    value = Path(os.environ.get(variable) or fallback).expanduser()
    return value if value.is_absolute() else Path(fallback).expanduser()


def steam_save_candidates():
    home = Path.home()
    roots = [
        xdg_path('XDG_DATA_HOME', home / '.local/share') / 'Steam',
        home / '.steam/steam', home / '.steam/root',
        home / '.steam/debian-installation',
        home / '.var/app/com.valvesoftware.Steam/.local/share/Steam',
        home / 'snap/steam/common/.local/share/Steam',
    ]
    libraries = list(roots)
    for root in roots:
        try:
            content = (root / 'steamapps/libraryfolders.vdf').read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
        # Modern Steam entries use "path"; older entries use numeric keys.
        for value in re.findall(r'"(?:path|\d+)"\s*"([^"\n]+)"', content):
            library = Path(value.replace('\\\\', '\\'))
            if library.is_absolute():
                libraries.append(library)
    return list(dict.fromkeys(root.resolve() / SAVE_SUFFIX for root in libraries))


def find_linux_saves():
    candidates = steam_save_candidates()
    # Prefer a library that actually contains saves over an empty prefix.
    for path in candidates:
        try:
            if game_saves(path):
                return path
        except OSError:
            continue
    return next((path for path in candidates if path.is_dir()), candidates[0])
