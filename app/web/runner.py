"""Start Flask web UI + background workers."""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

from app.core.paths import app_root
from app.core.runtime import dev_mode_enabled
from app.makcu.manager import makcu_manager
from app.runtime.worker import recoil_worker
from web.app import get_local_ip, run_flask, set_shutdown_callback, stop_flask


def _hide_console_window() -> None:
    """Hide stray console if the exe was built with console subsystem."""
    try:
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def _setup_logging() -> None:
    log_dir = Path(os.environ.get('APPDATA', Path.home())) / 'AimSync'
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_dir / 'aimsync.log'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a',
    )


def _open_browser(url: str) -> None:
    try:
        if hasattr(os, 'startfile'):
            os.startfile(url)
            return
    except OSError:
        pass
    try:
        webbrowser.open_new_tab(url)
    except Exception:
        webbrowser.open(url, new=1, autoraise=True)


def _acquire_single_instance() -> bool:
    if sys.platform != 'win32':
        return True
    try:
        import ctypes

        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, 'Local\\AimSync_Rebuild_v1')
        if ctypes.windll.kernel32.GetLastError() == 183:
            return False
        return True
    except Exception:
        return True


def _start_ai_worker(stop_event: threading.Event, logger: logging.Logger) -> None:
    from app.bootstrap.runtime import is_ai_available
    from app.core.config import load_config, save_config
    from app.core.licensing import ai_access_status

    access = ai_access_status()
    if not access.get('allowed'):
        config = load_config()
        if config.get('ai_enabled'):
            config['ai_enabled'] = False
            save_config(config)
        logger.info('AI locked — supporter license required (%s)', access.get('message') or 'no key')
        return

    if not is_ai_available():
        logger.info(
            'AI runtime not available — recoil/UI only. '
            'Install from Global Settings after unlocking AI.'
        )
        return
    from app.runtime.ai_worker import ai_worker

    threading.Thread(target=ai_worker, args=(stop_event,), name='AiWorker', daemon=True).start()


def run_web_app(*, dev_mode: bool | None = None) -> int:
    """Flask UI + recoil worker; AI when runtime is bundled or installed."""
    if getattr(sys, 'frozen', False) and sys.platform == 'win32':
        _hide_console_window()

    if dev_mode is None:
        dev_mode = dev_mode_enabled()

    if not _acquire_single_instance():
        logging.getLogger('AimSync').warning('AimSync is already running.')
        return 1

    root = app_root()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    if dev_mode:
        os.environ['AIMSYNC_DEV'] = '1'

    _setup_logging()
    logger = logging.getLogger('AimSync')

    stop_event = threading.Event()
    makcu_manager.set_dev_allowed(dev_mode)
    makcu_manager.connect()

    threading.Thread(target=run_flask, name='Flask', daemon=True).start()
    threading.Thread(target=recoil_worker, args=(stop_event,), name='RecoilWorker', daemon=True).start()
    _start_ai_worker(stop_event, logger)

    url = f'http://{get_local_ip()}:5000'
    time.sleep(0.45)
    _open_browser(url)
    logger.info('AimSync running at %s', url)
    if dev_mode:
        logger.info('AIMSYNC_DEV=1 — local mouse if Makcu unavailable')

    shutdown_requested = threading.Event()

    def request_shutdown(_shutdown_pc: bool = False) -> None:
        stop_event.set()
        stop_flask()
        makcu_manager.disconnect()
        shutdown_requested.set()
        if _shutdown_pc:
            import subprocess

            try:
                subprocess.run(
                    ['shutdown', '/s', '/t', '0'],
                    check=True,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
            except Exception:
                pass
        os._exit(0)

    set_shutdown_callback(request_shutdown)

    try:
        import tkinter as tk

        root_tk = tk.Tk()
        root_tk.withdraw()
        root_tk.title('AimSync')
        root_tk.protocol('WM_DELETE_WINDOW', lambda: request_shutdown(False))

        def poll() -> None:
            if shutdown_requested.is_set():
                root_tk.destroy()
                return
            root_tk.after(200, poll)

        poll()
        root_tk.mainloop()
    except Exception:
        logger.info('Tk unavailable — running headless; use Stop App in browser.')
        try:
            while not shutdown_requested.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            request_shutdown(False)

    return 0
