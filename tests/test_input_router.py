import unittest
from unittest.mock import MagicMock, patch

from Input.router import InputRouter


class InputRouterTests(unittest.TestCase):
    def test_makcu_mode_does_not_create_backend(self):
        router = InputRouter()
        with patch('Input.router.create_backend') as create_backend:
            router.reload({'mouse_input_method': 'makcu'})
            create_backend.assert_not_called()
            self.assertIsNone(router._backend)

    def test_win32_mode_moves_via_backend(self):
        router = InputRouter()
        backend = MagicMock()
        backend.is_open.return_value = True
        with patch('Input.router.create_backend', return_value=backend):
            with patch('Input.router.load_config', return_value={'mouse_input_method': 'win32'}):
                router.reload({'mouse_input_method': 'win32'})
                router.move(3, -2)
        backend.move.assert_called_once_with(3, -2)

    def test_reload_disconnects_previous_backend(self):
        router = InputRouter()
        old = MagicMock()
        old.is_open.return_value = True
        router._backend = old
        router._method_key = 'win32'
        new = MagicMock()
        new.is_open.return_value = True
        with patch('Input.router.create_backend', return_value=new):
            router.reload({'mouse_input_method': 'ghub'})
        old.disconnect.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)
