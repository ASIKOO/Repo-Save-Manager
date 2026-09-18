import tempfile
import unittest
from pathlib import Path
from lib.save_paths import game_saves, copy_to_directory, game_destination, restore_save


class SaveLayoutTests(unittest.TestCase):
    def test_loose_and_legacy_saves_round_trip(self):
        for loose in (True, False):
            with self.subTest(loose=loose), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                game = root / 'game'
                game.mkdir()
                name = 'REPO_SAVE_2026_03_27_14_05_47'
                source = game / (name + '.es3' if loose else name)
                if loose:
                    source.write_bytes(b'original')
                else:
                    source.mkdir()
                    (source / (name + '.es3')).write_bytes(b'original')
                (game / 'Player.log').write_text('not a save')
                self.assertEqual(game_saves(game), [source])
                backup = root / name
                copy_to_directory(source, backup)
                self.assertEqual((backup / (name + '.es3')).read_bytes(), b'original')
                self.assertEqual(game_destination(game, name), source)
                destination = game_destination(game, 'REPO_SAVE_new')
                restore_save(backup, destination)
                restored = destination if loose else destination / (name + '.es3')
                self.assertEqual(restored.read_bytes(), b'original')
                original = source if loose else source / (name + '.es3')
                self.assertEqual(original.read_bytes(), b'original')
