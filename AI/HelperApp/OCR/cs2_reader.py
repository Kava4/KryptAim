import logging
import time

from PIL import ImageGrab

from AI.HelperApp.OCR.preprocess import preprocess_frame
from AI.HelperApp.OCR.weapon_matcher import match_weapon_text, normalize_weapon_name

logger = logging.getLogger('AimSync.Helper')

try:
    import easyocr
except ImportError:  # pragma: no cover - optional runtime dependency
    easyocr = None


class Cs2Reader:
    """Capture a configured ROI and attempt to extract the current CS2 weapon text."""

    def __init__(self, poll_ms: int = 250, roi: dict | None = None, minimum_confidence: float = 0.7) -> None:
        self.poll_ms = max(50, int(poll_ms))
        self.roi = roi or {}
        self.minimum_confidence = float(minimum_confidence)
        self._ocr_reader = None
        self._last_weapon = None
        self._last_reported_at = 0.0

    def detect_weapon(self) -> dict | None:
        """Capture the configured ROI, run OCR, and return a normalized weapon payload."""
        bbox = self._get_bbox()
        if not bbox:
            return None

        frame = ImageGrab.grab(bbox=bbox)
        processed = preprocess_frame(frame)
        if processed is None:
            return None

        text_candidates = self._extract_text_candidates(processed)
        best_weapon = None
        best_confidence = 0.0

        for candidate_text, ocr_confidence in text_candidates:
            weapon, match_score = match_weapon_text(candidate_text)
            if not weapon:
                continue
            combined_confidence = float(ocr_confidence) * float(match_score)
            if combined_confidence > best_confidence:
                best_weapon = weapon
                best_confidence = combined_confidence

        if not best_weapon or best_confidence < self.minimum_confidence:
            return None

        now = time.time()
        if best_weapon == self._last_weapon and (now - self._last_reported_at) < 0.75:
            return None

        self._last_weapon = best_weapon
        self._last_reported_at = now
        return self.make_detection(best_weapon, best_confidence)

    @staticmethod
    def make_detection(weapon_text: str, confidence: float) -> dict:
        return {
            'type': 'weapon_detected',
            'game': 'cs2',
            'weapon': normalize_weapon_name(weapon_text),
            'confidence': float(confidence),
            'ts': int(time.time() * 1000),
        }

    def _get_bbox(self) -> tuple[int, int, int, int] | None:
        x = int(self.roi.get('x', 0) or 0)
        y = int(self.roi.get('y', 0) or 0)
        width = int(self.roi.get('width', 0) or 0)
        height = int(self.roi.get('height', 0) or 0)
        if width <= 0 or height <= 0:
            return None
        return (x, y, x + width, y + height)

    def _extract_text_candidates(self, processed_frame) -> list[tuple[str, float]]:
        if easyocr is None:
            return []

        if self._ocr_reader is None:
            logger.info("Initializing EasyOCR reader for helper OCR...")
            self._ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)

        results = self._ocr_reader.readtext(processed_frame)
        candidates: list[tuple[str, float]] = []
        for result in results:
            if len(result) != 3:
                continue
            _, text, confidence = result
            if text:
                candidates.append((str(text), float(confidence)))
        return candidates
