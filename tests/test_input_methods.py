import unittest

from Input.methods import resolve_mouse_input_method, sync_legacy_recoil_input_method, use_alt_input


class InputMethodsTests(unittest.TestCase):
    def test_default_is_makcu(self):
        self.assertEqual(resolve_mouse_input_method({}), 'makcu')
        self.assertFalse(use_alt_input({}))

    def test_legacy_software_maps_win32(self):
        cfg = {'recoil_input_method': 'software'}
        self.assertEqual(resolve_mouse_input_method(cfg), 'win32')
        self.assertTrue(use_alt_input(cfg))

    def test_explicit_ghub(self):
        cfg = {'mouse_input_method': 'ghub'}
        self.assertEqual(resolve_mouse_input_method(cfg), 'ghub')
        self.assertTrue(use_alt_input(cfg))

    def test_sync_legacy_recoil_input_method(self):
        cfg = {'mouse_input_method': 'ghub'}
        sync_legacy_recoil_input_method(cfg)
        self.assertEqual(cfg['recoil_input_method'], 'hardware')

        cfg = {'mouse_input_method': 'win32'}
        sync_legacy_recoil_input_method(cfg)
        self.assertEqual(cfg['recoil_input_method'], 'software')


if __name__ == '__main__':
    unittest.main(verbosity=2)
