"""Import standalone encrypted R.E.P.O. saves without touching the source."""
import json
import shutil
from datetime import datetime
from pathlib import Path

from lib.decrypt import decrypt_es3

SAVE_PASSWORD = "Why would you want to cheat?... :o It's no fun. :') :'D"


def import_es3(source, backup_root):
    source = Path(source)
    if not source.is_file() or source.suffix.lower() != '.es3':
        raise ValueError('Choose a local .es3 save file.')
    data = source.read_bytes()
    try:
        decoded = json.loads(decrypt_es3(data, SAVE_PASSWORD))
        if not isinstance(decoded, dict) or not isinstance(
            decoded.get('dictionaryOfDictionaries', {}).get('value'), dict
        ):
            raise ValueError('Missing game data')
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError('Cannot read this R.E.P.O. save; it may be corrupt or incompatible.') from error

    root = Path(backup_root)
    name = 'REPO_SAVE_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    # Reserve a new directory atomically, even for repeated or simultaneous drops.
    number = 0
    while True:
        destination = root / (name if number == 0 else f'{name}_{number}')
        try:
            destination.mkdir()
            break
        except FileExistsError:
            number += 1
    try:
        (destination / f'{destination.name}.es3').write_bytes(data)
    except OSError:
        shutil.rmtree(destination)
        raise
    return destination
