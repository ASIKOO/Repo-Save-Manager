"""Support both standalone ES3 files and legacy save directories."""
from pathlib import Path
import shutil


def game_saves(root):
    root = Path(root)
    if not root.is_dir():
        return []
    return [p for p in root.iterdir() if p.name.startswith('REPO_SAVE_') and
            (p.is_dir() or (p.is_file() and p.suffix.lower() == '.es3'))]


def save_files(path):
    path = Path(path)
    return [path] if path.is_file() else [p for p in path.iterdir()
                                        if p.is_file() and p.suffix.lower() == '.es3']


def copy_to_directory(source, destination):
    source, destination = Path(source), Path(destination)
    if source.is_file():
        destination.mkdir(parents=True)
        shutil.copy2(source, destination / source.name)
    else:
        shutil.copytree(source, destination)


def game_destination(root, name):
    root = Path(root)
    directory = root / name
    # Preserve the existing layout, including case-sensitive file extensions.
    entries = game_saves(root)
    matching = next((p for p in entries if p.is_file() and p.stem == name), None)
    if matching:
        return matching
    if directory.is_dir():
        return directory
    if any(p.is_file() for p in entries):
        return root / (name + '.es3')
    return directory


def remove_save(path):
    path = Path(path)
    if path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def restore_save(source, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.suffix.lower() == '.es3':
        files = save_files(source)
        if len(files) != 1:
            raise ValueError('Expected one .es3 file to restore as a standalone save.')
        shutil.copy2(files[0], destination)
    else:
        copy_to_directory(source, destination)
