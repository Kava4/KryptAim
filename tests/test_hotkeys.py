import unittest

from Recoil.hotkeys import HotkeyValidationError, normalize_hotkey_string, parse_hotkey, validate_hotkey_bindings


class HotkeyTests(unittest.TestCase):
    def test_normalizes_single_mouse_key(self):
        self.assertEqual(normalize_hotkey_string('mouse4'), 'M4')

    def test_normalizes_legacy_mouse_key_name(self):
        self.assertEqual(normalize_hotkey_string('M4'), 'M4')

    def test_normalizes_combo_key(self):
        spec = parse_hotkey('Ctrl+F1')
        self.assertEqual(spec.normalized, 'ctrl+f1')
        self.assertEqual(spec.primary_key, 'f1')
        self.assertEqual(spec.modifiers, ('ctrl',))

    def test_rejects_duplicate_binding_conflict(self):
        with self.assertRaises(HotkeyValidationError):
            validate_hotkey_bindings('ctrl+f1', 'ctrl+f1', {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
