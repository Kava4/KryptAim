import ctypes
import unittest
from unittest.mock import patch

from Makcu.software_manager import INPUT, MOUSEEVENTF_MOVE, SoftwareManager


class SoftwareManagerTests(unittest.TestCase):
    def test_get_button_state_uses_async_or_sync_key_state(self):
        manager = SoftwareManager()
        with patch('Makcu.software_manager._user32') as user32:
            user32.GetAsyncKeyState.return_value = 0
            user32.GetKeyState.return_value = 0x8000
            self.assertTrue(manager.get_button_state('LMB'))
            user32.GetKeyState.assert_called()

    def test_move_relative_prefers_sendinput(self):
        manager = SoftwareManager()
        with patch.object(manager, '_sendinput_move', return_value=True) as sendinput:
            with patch('Makcu.software_manager._user32') as user32:
                manager.move_relative(3, -5)
        sendinput.assert_called_once_with(3, -5)
        user32.mouse_event.assert_not_called()

    def test_move_relative_falls_back_to_mouse_event(self):
        manager = SoftwareManager()
        with patch.object(manager, '_sendinput_move', return_value=False):
            with patch('Makcu.software_manager._user32') as user32:
                manager.move_relative(2, 4)
        user32.mouse_event.assert_called_once_with(MOUSEEVENTF_MOVE, 2, 4, 0, 0)

    def test_sendinput_builds_relative_move_event(self):
        manager = SoftwareManager()
        captured = {}

        def _capture(count, pointer, size):
            captured['count'] = count
            captured['size'] = size
            captured['event'] = ctypes.cast(pointer, ctypes.POINTER(INPUT)).contents
            return 1

        with patch('Makcu.software_manager._user32') as user32:
            user32.SendInput.side_effect = _capture
            self.assertTrue(manager._sendinput_move(7, -2))
            self.assertEqual(captured['count'], 1)
            self.assertEqual(captured['event'].type, 0)
            self.assertEqual(captured['event'].mi.dx, 7)
            self.assertEqual(captured['event'].mi.dy, -2)
            self.assertEqual(captured['event'].mi.dwFlags, MOUSEEVENTF_MOVE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
