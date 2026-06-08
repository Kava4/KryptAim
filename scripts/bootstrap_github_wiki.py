"""Create the first GitHub Wiki page so .wiki.git can receive git pushes."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

ROOT = Path(__file__).resolve().parents[1]
OWNER = "AimSyncCore"
REPO = "AimSync"


def main() -> int:
    token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {token}",
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "AimSync-wiki-bootstrap",
        }
    )

    new_url = f"https://github.com/{OWNER}/{REPO}/wiki/_new"
    response = session.get(new_url, allow_redirects=True, timeout=30)
    print(f"GET {new_url} -> {response.status_code} {response.url}")
    if response.status_code != 200:
        print(response.text[:500])
        return 1

    match = re.search(r'name="authenticity_token"\s+value="([^"]+)"', response.text)
    if not match:
        print("Could not find authenticity_token on wiki new page.")
        return 1

    body = (ROOT / "wiki" / "Home.md").read_text(encoding="utf-8")
    data = {
        "authenticity_token": match.group(1),
        "page[format]": "markdown",
        "page[name]": "Home",
        "page[title]": "Home",
        "page[body]": body,
        "commit": "Create Home page",
    }
    post_url = f"https://github.com/{OWNER}/{REPO}/wiki"
    created = session.post(post_url, data=data, allow_redirects=True, timeout=30)
    print(f"POST {post_url} -> {created.status_code} {created.url}")
    if created.status_code >= 400 and "Home" not in created.url:
        print(created.text[:800])
        return 1

    print("Wiki bootstrap OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
