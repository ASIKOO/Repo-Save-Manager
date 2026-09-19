"""Run explicitly with the project's Python: python tests/smoke_gui.py."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

with tempfile.TemporaryDirectory() as temporary:
    os.environ['XDG_DATA_HOME'] = str(Path(temporary) / 'data')
    os.environ['XDG_CACHE_HOME'] = str(Path(temporary) / 'cache')
    from PyQt6.QtWidgets import QApplication
    from repo_save_manager import RepoSaveManager, SettingsDialog

    app = QApplication([])
    window = RepoSaveManager()
    assert window.app_data_dir == Path(temporary) / 'data/RepoSaveManager'
    dialog = SettingsDialog(window.settings, window)
    custom = Path(temporary) / 'custom saves'
    custom.mkdir()
    dialog.save_folder.setText(str(custom))
    window.settings = dialog.get_settings()
    window.apply_save_path()
    window.save_settings()
    assert window.repo_saves_path == custom
    with patch('repo_save_manager.QDesktopServices.openUrl', return_value=True) as opener:
        window.open_save_folder()
        assert opener.call_args.args[0].toLocalFile() == str(window.backup_path)
    restored = RepoSaveManager()
    assert restored.repo_saves_path == custom
    restored.settings['game_saves_path'] = ''
    restored.apply_save_path()
    assert restored.repo_saves_path == restored.detected_saves_path
    window.close()
    restored.close()
    print('GUI startup, settings persistence, folder opening: OK')
