import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from lib.linux_paths import SAVE_SUFFIX, find_linux_saves, xdg_path


class LinuxPathsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        home_patch = patch('pathlib.Path.home', return_value=self.home)
        env_patch = patch.dict(os.environ, {}, clear=True)
        home_patch.start()
        env_patch.start()
        self.addCleanup(home_patch.stop)
        self.addCleanup(env_patch.stop)

    def test_external_library_preferred_over_empty_default(self):
        root = self.home / '.local/share/Steam'
        (root / SAVE_SUFFIX).mkdir(parents=True)
        external = self.home / 'Games Disk'
        saves = external / SAVE_SUFFIX
        saves.mkdir(parents=True)
        (saves / 'REPO_test').mkdir()
        (root / 'steamapps/libraryfolders.vdf').write_text(
            '"libraryfolders" { "0" { "path" "' + str(external) + '" } }')
        self.assertEqual(find_linux_saves(), saves)

    def test_flatpak(self):
        saves = self.home / '.var/app/com.valvesoftware.Steam/.local/share/Steam' / SAVE_SUFFIX
        saves.mkdir(parents=True)
        self.assertEqual(find_linux_saves(), saves)

    def test_missing_steam_does_not_create_prefix(self):
        self.assertFalse(find_linux_saves().exists())

    def test_xdg_override_and_relative_fallback(self):
        fallback = self.home / '.cache'
        with patch.dict(os.environ, {'XDG_CACHE_HOME': str(self.home / 'cache')}):
            self.assertEqual(xdg_path('XDG_CACHE_HOME', fallback), self.home / 'cache')
        with patch.dict(os.environ, {'XDG_CACHE_HOME': 'relative'}):
            self.assertEqual(xdg_path('XDG_CACHE_HOME', fallback), fallback)


if __name__ == '__main__':
    unittest.main()
