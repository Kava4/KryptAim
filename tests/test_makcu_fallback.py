import unittest

from Makcu.makcu_manager import makcu_manager


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


if __name__ == '__main__':
    unittest.main(verbosity=2)
