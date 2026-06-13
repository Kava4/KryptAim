"""Weapon pattern data."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.recoil import engine as recoil_engine
from app.recoil.weapon_data import WeaponData


class WeaponDataTests(unittest.TestCase):
    def test_galil_timed_profile(self) -> None:
        data = WeaponData()
        self.assertEqual(len(data.galil), 560)
        self.assertEqual(WeaponData.get_profile('galil'), 'timed')
        self.assertEqual(data.galil[0], (0.0, 0.0, 0.002))

    def test_galil_tail_tune(self) -> None:
        n = len(WeaponData().galil)
        start = int(n * 0.8)
        x0, y0 = WeaponData.apply_tail_tune('galil', start - 1, n, 10.0, 5.0)
        self.assertEqual((x0, y0), (10.0, 5.0))
        x1, y1 = WeaponData.apply_tail_tune('galil', start, n, 10.0, 5.0)
        self.assertAlmostEqual(x1, 8.2)
        self.assertAlmostEqual(y1, 5.0)

    def test_mp7_tail_tune(self) -> None:
        n = len(WeaponData().mp7)
        start = int(n * 0.75)
        x1, y1 = WeaponData.apply_tail_tune('mp7', start, n, 10.0, 10.0)
        self.assertAlmostEqual(x1, 8.2)
        self.assertAlmostEqual(y1, 9.2)

    def test_spray_weapons_present(self) -> None:
        data = WeaponData()
        self.assertEqual(len(data.m4a4), 87)
        self.assertEqual(len(data.famas), 71)
        self.assertEqual(len(data.mp9), 63)
        self.assertEqual(len(data.mac10), 72)
        self.assertEqual(WeaponData.get_profile('m4a4'), 'spray')
        self.assertEqual(WeaponData.get_profile('assault_rifle'), 'smooth')

    def test_weapon_categories(self) -> None:
        labels = WeaponData.weapon_labels()
        rifles = WeaponData.weapons_in_category('rifle')
        smgs = WeaponData.weapons_in_category('smg')
        self.assertEqual(len(rifles), 5)
        self.assertEqual(len(smgs), 7)
        self.assertEqual(set(rifles) | set(smgs), set(labels))
        self.assertEqual(WeaponData.category_for_weapon('galil'), 'rifle')
        self.assertEqual(WeaponData.category_for_weapon('mp7'), 'smg')

    def test_weapon_teams(self) -> None:
        labels = WeaponData.weapon_labels()
        ct_rifles = WeaponData.weapons_in_team_category('ct', 'rifle')
        t_rifles = WeaponData.weapons_in_team_category('t', 'rifle')
        ct_smgs = WeaponData.weapons_in_team_category('ct', 'smg')
        t_smgs = WeaponData.weapons_in_team_category('t', 'smg')
        self.assertEqual(ct_rifles, ('m4a4', 'm4a1s', 'famas'))
        self.assertEqual(t_rifles, ('assault_rifle', 'galil'))
        self.assertEqual(ct_smgs, ('mp9', 'mp7', 'mp5sd', 'p90', 'ump45', 'bizon'))
        self.assertEqual(t_smgs, ('mac10', 'p90'))
        self.assertEqual(
            set(ct_rifles) | set(t_rifles) | set(ct_smgs) | set(t_smgs),
            set(labels),
        )
        self.assertEqual(WeaponData.team_for_weapon('assault_rifle'), 't')
        self.assertEqual(WeaponData.team_for_weapon('m4a4'), 'ct')
        self.assertEqual(WeaponData.team_for_weapon('p90'), 't')

    def test_aie_timed_smgs_present(self) -> None:
        data = WeaponData()
        expected = {
            'mp7': 324,
            'mp5sd': 360,
            'p90': 600,
            'ump45': 300,
            'bizon': 768,
        }
        for weapon_id, steps in expected.items():
            pattern = getattr(data, weapon_id)
            self.assertEqual(len(pattern), steps, weapon_id)
            self.assertEqual(WeaponData.get_profile(weapon_id), 'timed')
        labels = WeaponData.weapon_labels()
        self.assertEqual(len(labels), 12)

    @patch('app.recoil.engine.time.perf_counter', side_effect=[0.0, 0.0, 0.001])
    @patch('app.recoil.engine.time.sleep')
    @patch('app.recoil.engine.makcu_manager')
    def test_timed_profile_moves_before_sleep(self, makcu, sleep, _perf) -> None:
        recoil_engine.reset_recoil_state()
        makcu.get_button_state.side_effect = lambda b: b == 'LMB'
        config = {
            'recoil_enabled': True,
            'recoil_keybind': 'M4',
            'recoil_require_rmb': False,
            'recoil_return_crosshair': False,
            'recoil_randomisation': False,
            'recoil_x_control': 100,
            'recoil_y_control': 100,
            'recoil_cs2_settings': {
                'cs2_weapon': 'galil',
                'cs2_sensitivity': 2.25,
            },
        }
        pattern = [(4.0, 8.0, 0.01)]
        with (
            patch.object(recoil_engine, 'get_config', return_value=config),
            patch.object(WeaponData, 'get_pattern', return_value=pattern),
            patch.object(WeaponData, 'get_profile', return_value='timed'),
        ):
            recoil_engine.run_recoil()
        makcu.move_relative.assert_called_once()
        sleep.assert_called_once()
        self.assertGreater(sleep.call_args[0][0], 0)

    @patch('app.recoil.engine.time.sleep')
    @patch('app.recoil.engine.makcu_manager')
    def test_spray_profile_timing(self, makcu, sleep) -> None:
        recoil_engine.reset_recoil_state()
        makcu.get_button_state.side_effect = lambda b: b == 'LMB'
        config = {
            'recoil_enabled': True,
            'recoil_keybind': 'M4',
            'recoil_require_rmb': False,
            'recoil_return_crosshair': False,
            'recoil_randomisation': False,
            'recoil_x_control': 100,
            'recoil_y_control': 100,
            'recoil_cs2_settings': {
                'cs2_weapon': 'm4a4',
                'cs2_sensitivity': 3.09,
            },
        }
        with patch.object(recoil_engine, 'get_config', return_value=config):
            recoil_engine.run_recoil()
        makcu.move_mouse_smoothly.assert_not_called()
        recoil_engine._shot_count = 2
        recoil_engine._lmb_was_pressed = True
        with patch.object(recoil_engine, 'get_config', return_value=config):
            recoil_engine.run_recoil()
        makcu.move_relative.assert_called_once()
        self.assertAlmostEqual(makcu.move_relative.call_args[0][1], 4.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
