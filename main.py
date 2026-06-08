"""AimSync desktop entry."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

# Before ultralytics/torch imports anywhere in the process.
os.environ.setdefault('YOLO_AUTOINSTALL', 'false')


def _startup_log_path() -> Path:
    from Config.config_manager import get_base_dir

    base = get_base_dir()
    base.mkdir(parents=True, exist_ok=True)
    return base / 'startup.log'


def _write_startup_log(message: str) -> None:
    try:
        path = _startup_log_path()
        with open(path, 'a', encoding='utf-8') as handle:
            handle.write(message)
            if not message.endswith('\n'):
                handle.write('\n')
    except OSError:
        pass


def _show_fatal_error(title: str, message: str) -> None:
    _write_startup_log(f'FATAL: {title}\n{message}')
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        pass


def main() -> None:
    try:
        _run_app()
    except Exception:
        tb = traceback.format_exc()
        _write_startup_log(tb)
        _show_fatal_error(
            'AimSync failed to start',
            f'{tb[:1200]}\n\nLog: {_startup_log_path()}',
        )
        raise SystemExit(1) from None


def _enable_crash_logging() -> None:
    try:
        import faulthandler

        from Config.config_manager import get_base_dir

        log_dir = get_base_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        fault_path = log_dir / 'ai_engine_fault.log'
        with open(fault_path, 'a', encoding='utf-8') as handle:
            handle.write('\n--- process start ---\n')
            faulthandler.enable(file=handle, all_threads=True)
    except Exception:
        pass


def _run_app() -> None:
    import logging
    import socket
    import threading
    import time
    import webbrowser

    _enable_crash_logging()

    import tkinter as tk
    from tkinter import messagebox

    from Config.app_identity import get_app_name, get_app_version
    from Config.config_manager import get_base_dir, load_config, save_config
    from Makcu.makcu_manager import makcu_manager
    from Makcu.software_manager import software_manager
    from Recoil.hotkeys import HotkeyStateTracker, get_bound_weapon
    from Recoil.recoil import run_recoil
    from Server.app import run_flask, stop_flask
    from Server.weapon_actions import cycle_weapon, get_available_weapons, set_active_weapon

    logger = logging.getLogger('AimSync')
    hotkey_tracker = HotkeyStateTracker()
    browser_opened = False
    single_instance_mutex = None

    def setup_logging() -> None:
        log_dir = get_base_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'aimsyc_debug.log'
        logging.basicConfig(
            filename=str(log_file),
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='w',
        )
        _write_startup_log(f'Logging to {log_file}')

    def app_icon_path() -> Path:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS) / 'static' / 'AimSync_logo.ico'
        return Path(__file__).resolve().parent / 'Server' / 'static' / 'AimSync_logo.ico'

    def apply_window_icon(root: tk.Tk) -> None:
        icon = app_icon_path()
        if not icon.is_file():
            return
        try:
            root.iconbitmap(default=str(icon))
        except tk.TclError:
            pass

    def get_local_ip() -> str:
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe.connect(('8.8.8.8', 80))
            ip = probe.getsockname()[0]
            probe.close()
            return ip
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return '0.0.0.0'

    def acquire_single_instance() -> bool:
        nonlocal single_instance_mutex
        if sys.platform != 'win32':
            return True
        try:
            import ctypes

            name = 'Local\\AimSync_SingleInstance_v1'
            single_instance_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, name)
            if ctypes.windll.kernel32.GetLastError() == 183:
                return False
            return True
        except Exception as exc:
            logger.warning('Single-instance mutex unavailable: %s', exc)
            return True

    def open_browser(url: str) -> None:
        nonlocal browser_opened
        if browser_opened:
            return
        browser_opened = True
        try:
            if hasattr(os, 'startfile'):
                os.startfile(url)
                return
        except Exception:
            pass
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            webbrowser.open(url, new=1, autoraise=True)

    def startup() -> str:
        threading.Thread(target=run_flask, daemon=True).start()
        url = f'http://{get_local_ip()}:5000'
        time.sleep(0.4)
        open_browser(url)
        return url

    def shutdown(root: tk.Tk) -> None:
        try:
            from AI.Engine.engine import stop_ai_engine

            stop_ai_engine()
            makcu_manager.disconnect()
            stop_flask()
        finally:
            try:
                root.destroy()
            except Exception:
                pass
            os._exit(0)

    def monitor_hotkeys() -> None:
        logger.info('Hotkey monitor started.')
        last_game_id = None
        available_weapons: list[str] = []

        while True:
            try:
                config = load_config()
                game_id = config.get('active_game', 'cs2')

                if game_id != last_game_id:
                    available_weapons = get_available_weapons(game_id)
                    last_game_id = game_id

                cycle_key = config.get('weapon_cycle_hotkey') or config.get('recoil_cycle_keybind', 'None')
                if available_weapons and hotkey_tracker.is_pressed_once('weapon_cycle', cycle_key):
                    cycle_weapon(config)

                direct_weapon = get_bound_weapon(config, hotkey_tracker)
                if direct_weapon and available_weapons:
                    set_active_weapon(config, direct_weapon, available_weapons)

                ai_toggle = config.get('ai_engine_toggle_hotkey', 'None')
                if hotkey_tracker.is_pressed_once('ai_engine_toggle', ai_toggle):
                    config['ai_engine_enabled'] = not bool(config.get('ai_engine_enabled'))
                    save_config(config)
            except Exception as exc:
                logger.error('Hotkey Monitor Error: %s', exc)
            time.sleep(0.01)

    def ensure_dual_pc_defaults() -> None:
        config = load_config()
        changed = False
        if makcu_manager.is_hardware() and makcu_manager.is_connected():
            if config.get('recoil_input_method') == 'software':
                config['recoil_input_method'] = 'hardware'
                changed = True
        if changed:
            save_config(config)

    def run_recoil_loop() -> None:
        while True:
            try:
                run_recoil()
            except Exception as exc:
                logger.exception('Recoil loop error: %s', exc)
                time.sleep(0.1)

    if not acquire_single_instance():
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                get_app_name(),
                f'{get_app_name()} is already running.\n\n'
                'Close extra copies in Task Manager, then use the existing browser tab.',
            )
            root.destroy()
        except Exception:
            pass
        raise SystemExit(0)

    setup_logging()
    _write_startup_log('AimSync starting...')

    makcu_manager.connect()
    ensure_dual_pc_defaults()
    makcu_ready = makcu_manager.is_hardware() and makcu_manager.is_connected()
    logger.info(
        'Makcu startup: hardware=%s connected=%s',
        makcu_manager.is_hardware(),
        makcu_ready,
    )
    if not makcu_ready:
        cfg = load_config()
        if cfg.get('recoil_input_method') == 'hardware':
            logger.info(
                'No Makcu — recoil uses Software (SendInput). '
                'Set Input Method to Software in settings for single-PC play.'
            )

    from AI.Engine.engine import start_ai_engine_thread

    start_ai_engine_thread()
    startup()

    root = tk.Tk()
    apply_window_icon(root)
    root.withdraw()
    root.title(f'{get_app_name()} {get_app_version()}')
    root.protocol('WM_DELETE_WINDOW', lambda: shutdown(root))

    threading.Thread(target=monitor_hotkeys, daemon=True).start()
    threading.Thread(target=run_recoil_loop, daemon=True).start()
    _write_startup_log('Entering mainloop')
    root.mainloop()


if __name__ == '__main__':
    main()
