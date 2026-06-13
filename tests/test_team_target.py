"""CS2 team → enemy class mapping."""

from __future__ import annotations

import unittest

from app.ai.model_classes import apply_team_to_player_class
from app.ai.team_target import enemy_class_for_team, has_ct_t_classes


class TeamTargetTests(unittest.TestCase):
    def test_enemy_mapping(self) -> None:
        labels = ['CT', 'T']
        self.assertEqual(enemy_class_for_team('ct', labels), 'T')
        self.assertEqual(enemy_class_for_team('t', labels), 'CT')

    def test_has_ct_t(self) -> None:
        self.assertTrue(has_ct_t_classes(['CT', 'T']))
        self.assertFalse(has_ct_t_classes(['player', 'head']))

    def test_apply_team_to_config(self) -> None:
        updates = apply_team_to_player_class(
            {
                'ai_my_team': 'ct',
                'ai_model_path': 'cs2.onnx',
            },
        )
        self.assertEqual(updates, {})


if __name__ == '__main__':
    unittest.main()
