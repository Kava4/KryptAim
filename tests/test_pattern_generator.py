import unittest

from PatternGenerator.engine import (
    _auto_suggest_cs2pulse,
    build_recoil_steps,
    detect_points_and_preview,
    laser_fit_steps,
    resample_deltas,
)

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


@unittest.skipIf(Image is None, "Pillow is required")
class PatternGeneratorEngineTests(unittest.TestCase):
    def _make_cs2pulse_gif_bytes(self) -> bytes:
        import io

        frames = []
        base = Image.new("RGB", (200, 300), (0, 0, 0))
        for idx in range(5):
            frame = base.copy()
            px = frame.load()
            y = 250 - idx * 20
            x = 100 + idx * 3
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    px[x + dx, y + dy] = (255, 255, 255)
            frames.append(frame)

        buffer = io.BytesIO()
        frames[0].save(
            buffer,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=40,
            loop=0,
        )
        return buffer.getvalue()

    def test_cs2pulse_frame_diff_orders_bullets(self):
        import io

        frames = []
        base = Image.new("RGB", (200, 300), (0, 0, 0))
        for idx in range(4):
            frame = base.copy()
            px = frame.load()
            y = 250 - idx * 25
            x = 100
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    px[x + dx, y + dy] = (255, 255, 255)
            frames.append(frame)

        points = _auto_suggest_cs2pulse(frames)
        self.assertGreaterEqual(len(points), 3)
        ys = [p[1] for p in points]
        self.assertGreater(ys[0], ys[-1])

    def test_detect_points_and_preview_uses_last_frame_for_cs2pulse(self):
        payload = detect_points_and_preview(self._make_cs2pulse_gif_bytes(), detect_style="cs2pulse")
        self.assertEqual(payload["detect_style"], "cs2pulse")
        self.assertGreater(payload["frame_count"], 1)
        self.assertEqual(payload["recommended_frame_index"], payload["frame_count"] - 1)
        self.assertGreaterEqual(len(payload["suggested_points"]), 3)

    def test_build_recoil_steps_canonical_inverts_spray(self):
        raw_points = [{"x": 100, "y": 200}, {"x": 110, "y": 180}, {"x": 120, "y": 150}]
        payload = build_recoil_steps(raw_points, delay_ms=100, invert_x=True, invert_y=True)
        lines = payload["pattern_text"].splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "-10.0,20.0,0.1")
        self.assertEqual(lines[1], "-10.0,30.0,0.1")

    def test_laser_fit_matches_reference_totals(self):
        raw_points = [{"x": 100, "y": 300}, {"x": 102, "y": 280}, {"x": 108, "y": 250}, {"x": 112, "y": 220}]
        reference = [(0, 10, 0.1), (0, 10, 0.1), (-5, 20, 0.1)]
        fitted = laser_fit_steps(raw_points, reference, horizontal_strength=0.5)
        self.assertAlmostEqual(sum(s[0] for s in fitted), sum(s[0] for s in reference) * 0.5, places=1)

    def test_build_recoil_steps_laser_fit_export(self):
        raw_points = [{"x": 10, "y": 20}, {"x": 12, "y": 10}, {"x": 15, "y": 0}]
        reference = [(0, 5, 0.1), (-2, 8, 0.1)]
        payload = build_recoil_steps(
            raw_points,
            export_mode="laser_fit",
            reference_steps=reference,
        )
        self.assertEqual(payload["export_mode"], "laser_fit")
        self.assertEqual(len(payload["steps_seconds"]), len(reference))


if __name__ == "__main__":
    unittest.main(verbosity=2)
