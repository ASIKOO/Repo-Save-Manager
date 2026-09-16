import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.encrypt import encrypt_es3
from lib.import_save import SAVE_PASSWORD, import_es3


class ImportSaveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.backups = self.root / 'backups'
        self.backups.mkdir()
        self.source = self.root / 'my save.ES3'
        self.data = encrypt_es3(json.dumps({
            'dictionaryOfDictionaries': {'value': {'runStats': {'level': 7}}}
        }).encode(), SAVE_PASSWORD)
        self.source.write_bytes(self.data)

    def test_import_preserves_original_and_uses_matching_names(self):
        target = import_es3(self.source, self.backups)
        self.assertTrue(target.name.startswith('REPO_SAVE_'))
        self.assertEqual((target / (target.name + '.es3')).read_bytes(), self.data)
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_repeated_import_never_overwrites(self):
        first = import_es3(self.source, self.backups)
        second = import_es3(self.source, self.backups)
        self.assertNotEqual(first, second)
        self.assertEqual((first / (first.name + '.es3')).read_bytes(), self.data)

    def test_invalid_save_creates_no_backup(self):
        for data in (b'broken', encrypt_es3(b'{"unrelated": true}', SAVE_PASSWORD)):
            self.source.write_bytes(data)
            with self.assertRaises(ValueError):
                import_es3(self.source, self.backups)
            self.assertEqual(list(self.backups.iterdir()), [])

    def test_failed_write_removes_partial_backup(self):
        with patch.object(Path, 'write_bytes', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                import_es3(self.source, self.backups)
        self.assertEqual(list(self.backups.iterdir()), [])
        self.assertEqual(self.source.read_bytes(), self.data)


class DropIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.env = patch.dict(os.environ, {
            'QT_QPA_PLATFORM': 'offscreen',
            'XDG_DATA_HOME': cls.temp.name + '/data',
            'XDG_CACHE_HOME': cls.temp.name + '/cache',
        })
        cls.env.start()
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        cls.temp.cleanup()

    def test_viewport_drop_imports_and_displays_backup(self):
        from PyQt6.QtCore import QMimeData, QPoint, QPointF, QUrl, Qt
        from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
        from repo_save_manager import RepoSaveManager
        source = Path(self.temp.name) / 'Dropped save.es3'
        data = encrypt_es3(json.dumps({
            'dictionaryOfDictionaries': {'value': {'runStats': {'level': 7}}}
        }).encode(), SAVE_PASSWORD)
        source.write_bytes(data)
        broken = Path(self.temp.name) / 'broken.es3'
        broken.write_bytes(b'invalid save')
        window = RepoSaveManager()
        self.addCleanup(window.close)
        window.settings['show_backup_saves'] = False
        window.show()
        self.app.processEvents()
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(source)), QUrl.fromLocalFile(str(broken))])
        actions = Qt.DropAction.CopyAction | Qt.DropAction.MoveAction
        enter = QDragEnterEvent(QPoint(10, 10), actions, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        move = QDragMoveEvent(QPoint(10, 10), actions, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        drop = QDropEvent(QPointF(10, 10), actions, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        with patch('repo_save_manager.QMessageBox.warning') as warning:
            for event in (enter, move, drop):
                self.app.sendEvent(window.save_table.viewport(), event)
                self.assertTrue(event.isAccepted())
                self.assertEqual(event.dropAction(), Qt.DropAction.CopyAction)
            warning.assert_called_once()
        self.assertEqual(source.read_bytes(), data)
        self.assertEqual(window.save_table.rowCount(), 1)
        self.assertEqual(window.save_table.item(0, 4).text(), '7')
        self.assertTrue(window.get_selected_save_info()['is_backup'])
        self.assertTrue(window.restore_btn.isEnabled())
        self.assertTrue(window.settings['show_backup_saves'])
        self.assertIn('Dropped save.es3', window.save_table.item(0, 3).text())

    def test_non_save_and_remote_urls_rejected(self):
        from PyQt6.QtCore import QMimeData, QPoint, QUrl, Qt
        from PyQt6.QtGui import QDragEnterEvent
        from repo_save_manager import BackupTable
        table = BackupTable()
        self.addCleanup(table.close)
        text = Path(self.temp.name) / 'notes.txt'
        text.write_text('notes')
        for url in (QUrl.fromLocalFile(str(text)), QUrl('https://example.com/save.es3'),
                    QUrl.fromLocalFile(self.temp.name)):
            mime = QMimeData()
            mime.setUrls([url])
            event = QDragEnterEvent(QPoint(10, 10), Qt.DropAction.CopyAction, mime,
                                    Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            self.app.sendEvent(table.viewport(), event)
            self.assertFalse(event.isAccepted())


if __name__ == '__main__':
    unittest.main()
