import unittest

from AI.HelperApp.OCR.weapon_matcher import get_cs2_weapon_ids, match_weapon_text, normalize_weapon_name


class WeaponMatcherTests(unittest.TestCase):
    def test_normalize_weapon_name_strips_symbols(self):
        self.assertEqual(normalize_weapon_name('M4A1-S'), 'm4a1s')

    def test_match_weapon_text_handles_alias(self):
        weapon, score = match_weapon_text('AK-47')
        self.assertEqual(weapon, 'ak47')
        self.assertGreaterEqual(score, 0.9)

    def test_match_weapon_text_handles_fuzzy_input(self):
        weapon, score = match_weapon_text('five seven')
        self.assertEqual(weapon, 'fiveseven')
        self.assertGreater(score, 0.5)

    def test_cs2_weapon_ids_include_expected_weapons(self):
        weapons = get_cs2_weapon_ids()
        self.assertIn('ak47', weapons)
        self.assertIn('m4a1s', weapons)


if __name__ == '__main__':
    unittest.main(verbosity=2)
