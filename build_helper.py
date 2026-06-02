import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build-helper"
ICON = ROOT / "Server" / "static" / "AimSync_logo.ico"
ENTRYPOINT = ROOT / "AI" / "HelperApp" / "main.py"
HELPER_EXE = DIST / "AimSyncHelper.exe"
SPEC = ROOT / "AimSyncHelper.spec"


def main() -> None:
    print("Building OCR helper with PyInstaller...")

    BUILD.mkdir(parents=True, exist_ok=True)

    if HELPER_EXE.exists():
        HELPER_EXE.unlink()

    if SPEC.exists():
        SPEC.unlink()

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--console",
        "--onefile",
        "--distpath",
        str(DIST),
        "--workpath",
        str(BUILD),
        "--specpath",
        str(ROOT),
        "--name",
        "AimSyncHelper",
    ]

    if ICON.is_file():
        command += ["--icon", str(ICON)]
        print(f"Using icon: {ICON}")
    else:
        print(f"Warning: icon not found ({ICON}); exe will use default PyInstaller icon.")

    command += [
        str(ENTRYPOINT),
    ]

    subprocess.run(command, cwd=ROOT, check=True)

    exe = HELPER_EXE
    if not exe.exists():
        raise FileNotFoundError(f"Expected executable was not created: {exe}")

    print(f"Build complete: {exe}")
    print("Ship this file to the gaming PC for helper-only OCR usage.")


if __name__ == "__main__":
    main()
