from Makcu.makcu_manager import makcu_manager
from Server.app import run_flask, stop_flask
from Server.ocr_ws_server import start_ocr_ws_server_thread
from Recoil.recoil import run_recoil
from Recoil.hotkeys import HotkeyStateTracker, get_bound_weapon
from Recoil.weapon_data import WeaponData
from Config.app_identity import get_app_name, get_app_version, is_beta_channel
from Config.config_manager import load_config, save_config
from Makcu.software_manager import software_manager

from tkinter import messagebox
import threading
import tkinter as tk
import socket
import webbrowser
import os
import sys
import time
import logging
from pathlib import Path

# Setup logging to file for debugging when running as .exe
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aimsyc_debug.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'  # Overwrite log file on each run
)
logger = logging.getLogger('AimSync')
hotkey_tracker = HotkeyStateTracker()


def _app_icon_path() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "static" / "AimSync_logo.ico"
    return Path(__file__).resolve().parent / "Server" / "static" / "AimSync_logo.ico"


def _apply_window_icon(root: tk.Tk) -> None:
    icon = _app_icon_path()
    if not icon.is_file():
        return
    try:
        root.iconbitmap(default=str(icon))
    except tk.TclError:
        pass


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "0.0.0.0"

def open_browser(url: str) -> None:
    try:
        if hasattr(os, "startfile"):
            os.startfile(url)
            return
    except Exception:
        pass

    try:
        webbrowser.open_new_tab(url)
        return
    except Exception:
        pass

    try:
        webbrowser.open(url, new=1, autoraise=True)
    except Exception:
        pass


def startup():
    try:
        threading.Thread(target=run_flask, daemon=True).start()
    except Exception as e:
        messagebox.showinfo("AimSync", f"Failed to start Flask server: {e}")
        return

    url = f"http://{get_local_ip()}:5000"
    open_browser(url)
    return url


def shutdown(root):
    """Handles the application shutdown when the window is closed."""
    try:
        makcu_manager.disconnect()
        stop_flask()
    finally:
        try:
            root.destroy()
        except Exception:
            pass
        # Ensure all background threads (recoil loop, etc.) are terminated
        os._exit(0)


def _get_available_weapons(game_id):
    wd = WeaponData.get_game_data(game_id)
    weapons = [attr for attr in dir(wd) if not attr.startswith('_') and isinstance(getattr(wd, attr), list)]
    weapons.sort()
    return weapons


def _set_active_weapon(config, weapon_name, available_weapons):
    if weapon_name not in available_weapons:
        return False
    current_weapon = config.get('recoil_game_settings', {}).get('weapon')
    if current_weapon == weapon_name:
        return False
    config['recoil_game_settings']['weapon'] = weapon_name
    save_config(config)
    logger.info("Weapon hotkey selected %s", weapon_name)
    return True


def monitor_hotkeys():
    """Independent thread to monitor weapon cycle and direct-select hotkeys."""
    if not is_beta_channel():
        return
    logger.info("Hotkey monitor started.")
    last_game_id = None
    available_weapons = []

    while True:
        try:
            config = load_config()
            game_id = config.get('active_game', 'cs2')

            # Refresh weapon list if the game has changed
            if game_id != last_game_id:
                available_weapons = _get_available_weapons(game_id)
                last_game_id = game_id
                logger.info(f"Game changed to {game_id}. Available weapons: {available_weapons}")

            cycle_key = config.get('weapon_cycle_hotkey') or config.get('recoil_cycle_keybind', 'None')
            if available_weapons and hotkey_tracker.is_pressed_once('weapon_cycle', cycle_key):
                current_wep = config.get('recoil_game_settings', {}).get('weapon', '')
                idx = available_weapons.index(current_wep) if current_wep in available_weapons else -1
                next_wep = available_weapons[(idx + 1) % len(available_weapons)]
                config['recoil_game_settings']['weapon'] = next_wep
                save_config(config)
                logger.info(f"Change Weapon Key: Switched from {current_wep} to {next_wep}")

            direct_weapon = get_bound_weapon(config, hotkey_tracker)
            if direct_weapon and available_weapons:
                _set_active_weapon(config, direct_weapon, available_weapons)
        except Exception as e:
            logger.error(f"Hotkey Monitor Error: {e}")

        time.sleep(0.01) # 100Hz polling rate

def run_recoil_loop():
    print("[AimSync] Recoil engine initialized.")
    while True:


        run_recoil()


def main():
    # Attempt to connect to hardware, but continue startup regardless
    if makcu_manager.connect() is None:
        print("[AimSync] Warning: Makcu hardware not detected. Running in management-only mode.")

    if is_beta_channel():
        start_ocr_ws_server_thread()
    startup()

    root = tk.Tk()
    _apply_window_icon(root)
    root.withdraw()
    root.title(f"{get_app_name()} {get_app_version()}")

    def on_close():
        shutdown(root)

    root.protocol("WM_DELETE_WINDOW", on_close)

    threading.Thread(target=monitor_hotkeys, daemon=True).start()
    threading.Thread(target=run_recoil_loop, daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()