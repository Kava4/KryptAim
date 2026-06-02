from Makcu.makcu_manager import makcu_manager
from Server.app import run_flask, stop_flask
from Recoil.recoil import run_recoil
from Recoil.weapon_data import WeaponData
from Config.config_manager import load_config, save_config
from Config.version import APP_VERSION
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


def monitor_hotkeys():
    """Independent thread to monitor for weapon cycling hotkeys without blocking the recoil engine."""
    logger.info("Hotkey monitor started.")
    last_cycle_state = False
    last_game_id = None
    available_weapons = []

    while True:
        try:
            config = load_config()
            game_id = config.get('active_game', 'cs2')

            # Refresh weapon list if the game has changed
            if game_id != last_game_id:
                wd = WeaponData.get_game_data(game_id)
                available_weapons = [attr for attr in dir(wd) if not attr.startswith('_') and isinstance(getattr(wd, attr), list)]
                available_weapons.sort()
                last_game_id = game_id
                logger.info(f"Game changed to {game_id}. Available weapons: {available_weapons}")
            cycle_key = config.get('recoil_cycle_keybind', 'None')
            
            # Debug: Log cycle_key every 50 iterations to avoid spam
            if monitor_hotkeys._iter_count % 50 == 0:
                logger.debug(f"cycle_key={cycle_key}, current weapon={config.get('recoil_game_settings', {}).get('weapon', 'unknown')}")
            
            if cycle_key and cycle_key != 'None':
                current_state = software_manager.get_button_state(cycle_key)
                logger.debug(f"Key: {cycle_key}, current_state: {current_state}, last_state: {last_cycle_state}")
                if current_state and not last_cycle_state:
                    # Button pressed: cycle to next weapon
                    current_wep = config.get('recoil_game_settings', {}).get('weapon', '')
                    idx = available_weapons.index(current_wep) if current_wep in available_weapons else -1
                    next_wep = available_weapons[(idx + 1) % len(available_weapons)]
                    
                    config['recoil_game_settings']['weapon'] = next_wep
                    save_config(config)
                    logger.info(f"Change Weapon Key: Switched from {current_wep} to {next_wep}")
                last_cycle_state = current_state
            else:
                last_cycle_state = False
        except Exception as e:
            logger.error(f"Hotkey Monitor Error: {e}")
        
        monitor_hotkeys._iter_count += 1
        time.sleep(0.01) # 100Hz polling rate

# Initialize iteration counter for debug logging
monitor_hotkeys._iter_count = 0

def run_recoil_loop():
    print("[AimSync] Recoil engine initialized.")
    while True:


        run_recoil()


def main():
    # Attempt to connect to hardware, but continue startup regardless
    if makcu_manager.connect() is None:
        print("[AimSync] Warning: Makcu hardware not detected. Running in management-only mode.")

    startup()

    root = tk.Tk()
    _apply_window_icon(root)
    root.withdraw()
    root.title(f"AimSync {APP_VERSION}")

    def on_close():
        shutdown(root)

    root.protocol("WM_DELETE_WINDOW", on_close)

    threading.Thread(target=monitor_hotkeys, daemon=True).start()
    threading.Thread(target=run_recoil_loop, daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()