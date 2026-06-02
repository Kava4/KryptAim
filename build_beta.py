import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    print("Building beta desktop app...")
    env = os.environ.copy()
    env["AIMSYNC_CHANNEL"] = "beta"
    subprocess.run([sys.executable, "build_app.py"], cwd=ROOT, env=env, check=True)


if __name__ == "__main__":
    main()
