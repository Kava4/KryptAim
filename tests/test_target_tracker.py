"""Target lead / prediction tests."""

from __future__ import annotations

import unittest

from app.ai.target_tracker import TargetTracker
from app.ai.types import Prediction


class TargetTrackerTests(unittest.TestCase):
    def test_lead_moves_zone_closer_for_moving_target(self) -> None:
        tracker = TargetTracker()
        t0 = Prediction(confidence=0.9, image_dist=12.0, screen_center_x=332, screen_center_y=320)
        tracker.apply([t0], image_size=640, lookahead_ms=0, inference_ms=0)
        t1 = Prediction(confidence=0.9, image_dist=8.0, screen_center_x=324, screen_center_y=320)
        led = tracker.apply([t1], image_size=640, lookahead_ms=40, inference_ms=20)
        self.assertLess(led[0].image_dist, t1.image_dist)

    def test_resets_when_target_lost(self) -> None:
        tracker = TargetTracker()
        t0 = Prediction(confidence=0.9, image_dist=4.0, screen_center_x=320, screen_center_y=320)
        tracker.apply([t0], image_size=640, lookahead_ms=30, inference_ms=0)
        out = tracker.apply([], image_size=640, lookahead_ms=30, inference_ms=0)
        self.assertEqual(out, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
