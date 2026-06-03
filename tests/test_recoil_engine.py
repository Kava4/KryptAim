import unittest
from unittest.mock import patch

from Recoil import recoil as recoil_module


class RecoilEngineTests(unittest.TestCase):
    def setUp(self):
        recoil_module._state.update({
            'step_index': 0,
            'next_step_at': 0.0,
            'compensation_x': 0.0,
            'compensation_y': 0.0,
            'was_active': False,
        })

    @patch('Recoil.recoil.time.sleep')
    @patch('Recoil.recoil.load_config')
    def test_disabled_recoil_sleeps_without_move(self, load_config, _sleep):
        load_config.return_value = {'recoil_enabled': False}
        with patch.object(recoil_module, '_move_mouse') as move:
            recoil_module.run_recoil()
        move.assert_not_called()

    @patch('Recoil.recoil.time.sleep')
    @patch('Recoil.recoil._fire_button_held')
    @patch('Recoil.recoil.load_config')
    def test_simple_mode_moves_while_lmb_held(self, load_config, button_held, _sleep):
        button_held.side_effect = lambda key: key == 'LMB'
        load_config.return_value = {
            'recoil_enabled': True,
            'recoil_mode': 'simple',
            'recoil_require_rmb': False,
            'recoil_safety_features_enabled': False,
            'recoil_input_method': 'software',
            'recoil_simple_settings': {'recoil_x': 0, 'recoil_y': 5, 'recoil_delay': 50},
            'recoil_speed_control': 100,
        }
        with patch.object(recoil_module, '_move_mouse') as move:
            recoil_module.run_recoil()
        move.assert_called_once()
        args = move.call_args[0]
        self.assertEqual(args[1], 0)
        self.assertEqual(args[2], 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
