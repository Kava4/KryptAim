import unittest
from unittest.mock import MagicMock, patch

from Makcu.makcu_manager import MakcuManager, makcu_manager


class MakcuFallbackTests(unittest.TestCase):
    def test_connect_returns_manager_object(self):
        manager = makcu_manager.connect()
        self.assertIsNotNone(manager)

    def test_move_mouse_smoothly_does_not_crash(self):
        manager = makcu_manager.connect()
        manager.move_mouse_smoothly(1.5, -2.0)

    def test_get_button_state_returns_bool(self):
        manager = makcu_manager.connect()
        self.assertIsInstance(manager.get_button_state('LMB'), bool)

    def test_hardware_button_uses_transport_not_local_mouse(self):
        manager = MakcuManager()
        transport = MagicMock()
        transport.get_button_states.return_value = {
            'left': False,
            'right': True,
            'middle': False,
            'mouse4': False,
            'mouse5': False,
        }
        controller = MagicMock()
        controller.transport = transport
        manager._hardware = True
        manager._controller = controller
        self.assertTrue(manager.get_button_state('RMB'))
        self.assertFalse(manager.get_button_state('LMB'))
        transport.get_button_states.assert_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
