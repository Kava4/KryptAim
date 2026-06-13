"""Target parsing for trigger."""

from __future__ import annotations

import unittest

from app.ai.targets import (
    _matches_class,
    aim_x_from_bbox,
    aim_y_from_bbox,
    predictions_from_detections,
)


class TargetParsingTests(unittest.TestCase):
    def test_center_target_in_zone(self) -> None:
        dets = [{
            'x1': 310.0, 'y1': 310.0, 'x2': 330.0, 'y2': 330.0,
            'confidence': 0.9, 'class_id': 0, 'class_name': 'CT',
        }]
        targets = predictions_from_detections(dets, 640, player_label='')
        self.assertEqual(len(targets), 1)
        self.assertLess(targets[0].image_dist, 20.0)

    def test_player_class_filter(self) -> None:
        dets = [
            {
                'x1': 300.0, 'y1': 300.0, 'x2': 340.0, 'y2': 340.0,
                'confidence': 0.9, 'class_id': 0, 'class_name': 'CT',
            },
            {
                'x1': 300.0, 'y1': 300.0, 'x2': 340.0, 'y2': 340.0,
                'confidence': 0.9, 'class_id': 1, 'class_name': 'T',
            },
        ]
        ct_only = predictions_from_detections(dets, 640, player_label='CT')
        self.assertEqual(len(ct_only), 1)

    def test_t_filter_does_not_match_ct(self) -> None:
        self.assertFalse(_matches_class('CT', 0, 'T'))
        self.assertTrue(_matches_class('T', 1, 'T'))
        self.assertTrue(_matches_class('CT', 0, 'CT'))

    def test_head_aim_point_offset_right(self) -> None:
        x1, x2 = 300.0, 340.0
        center = (x1 + x2) / 2.0
        head_x = aim_x_from_bbox(x1, x2, aim_point='head', is_head_class=False)
        self.assertAlmostEqual(head_x, center + (x2 - x1) * 0.075)

    def test_body_aim_point_centered(self) -> None:
        x1, x2 = 300.0, 340.0
        body_x = aim_x_from_bbox(x1, x2, aim_point='body', is_head_class=False)
        self.assertAlmostEqual(body_x, (x1 + x2) / 2.0)

    def test_head_aim_point_above_body_center(self) -> None:
        y1, y2 = 200.0, 400.0
        center = (y1 + y2) / 2.0
        head_y = aim_y_from_bbox(y1, y2, aim_point='head', is_head_class=False)
        self.assertLess(head_y, center)

    def test_chest_alias_maps_to_head(self) -> None:
        x1, x2 = 300.0, 340.0
        center = (x1 + x2) / 2.0
        alias_x = aim_x_from_bbox(x1, x2, aim_point='chest', is_head_class=False)
        self.assertAlmostEqual(alias_x, center + (x2 - x1) * 0.075)

    def test_head_class_uses_box_center(self) -> None:
        dets = [{
            'x1': 300.0, 'y1': 200.0, 'x2': 340.0, 'y2': 240.0,
            'confidence': 0.9, 'class_id': 2, 'class_name': 'head',
        }]
        targets = predictions_from_detections(
            dets, 640, player_label='', head_class='head', aim_point='head',
        )
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0].screen_center_y, 220.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
