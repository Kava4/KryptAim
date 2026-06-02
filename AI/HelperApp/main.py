import asyncio
import logging
import sys
from pathlib import Path

if __package__ in {None, ''}:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from Config.config_manager import load_config
from AI.HelperApp.OCR.cs2_reader import Cs2Reader
from AI.HelperApp.ws_client import HelperWsClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AimSync.Helper')


async def run_helper() -> None:
    config = load_config()
    reader = Cs2Reader(
        poll_ms=config.get('ocr_poll_ms', 250),
        roi=config.get('ocr_roi_cs2', {}),
        minimum_confidence=config.get('ocr_confidence_threshold', 0.7),
    )
    client = HelperWsClient(
        server_url=config.get('ocr_helper_ws_url', 'ws://127.0.0.1:8765/ws/ocr'),
        token=config.get('ocr_helper_token', ''),
    )

    logger.info("OCR helper started. Target: %s", client.server_url)
    if not reader._get_bbox():
        logger.warning("OCR helper ROI is not configured yet. Set ocr_roi_cs2 before expecting detections.")
    while True:
        try:
            detection = reader.detect_weapon()
            if detection:
                logger.info("Detected weapon: %s (confidence %.2f)", detection['weapon'], detection['confidence'])
                await client.send_event(detection)
            else:
                await client.send_heartbeat()
            await asyncio.sleep(reader.poll_ms / 1000.0)
        except Exception as exc:
            logger.warning("Helper connection retry after error: %s", exc)
            await asyncio.sleep(1.0)


def main() -> None:
    asyncio.run(run_helper())


if __name__ == '__main__':
    main()
