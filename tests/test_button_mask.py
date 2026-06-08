import unittest

from AI.Engine.button_mask import BUTTON_NAME_TO_IDX, button_name_to_idx, mask_indices_from_config


class ButtonMaskTests(unittest.TestCase):
    def test_button_name_mapping(self):
        self.assertEqual(button_name_to_idx('RMB'), 1)
        self.assertEqual(button_name_to_idx('lmb'), 0)
        self.assertIsNone(button_name_to_idx('None'))

    def test_mask_indices_from_config(self):
        config = {
            'ai_mask_aim_button': 'RMB',
            'ai_mask_trigger_button': 'MMB',
        }
        self.assertEqual(mask_indices_from_config(config), [1, 2])

    def test_all_buttons_mapped(self):
        for name in ('LMB', 'RMB', 'MMB', 'M4', 'M5'):
            self.assertIn(name, BUTTON_NAME_TO_IDX)


if __name__ == '__main__':
    unittest.main()
