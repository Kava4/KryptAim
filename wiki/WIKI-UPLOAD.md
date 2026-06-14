# Upload these pages to GitHub Wiki

GitHub Wiki is a **separate git repository**:

```
https://github.com/AimSyncCore/KryptAim.wiki.git
```

Live wiki: https://github.com/AimSyncCore/KryptAim/wiki

## Automatic sync (recommended)

Push changes under `wiki/` to the `Beta` or `main` branch — the **Sync Wiki** GitHub Action publishes them.

Manual run: **Actions → Sync Wiki → Run workflow**.

## Manual sync (local)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_github_wiki.ps1
```

Requires the wiki git repo to exist (create the first page once from the GitHub **Wiki** tab if the script reports “not initialized”).

## One-time manual setup (if Action fails)

```bash
git clone https://github.com/AimSyncCore/KryptAim.wiki.git
cd KryptAim.wiki
```

Copy every `.md` file from this `wiki/` folder into the clone **except** `WIKI-UPLOAD.md`.

Required files:
- `Home.md` (wiki front page)
- `_Sidebar.md` (left navigation)
- All other `*.md` pages

```bash
git add .
git commit -m "Initial KryptAim wiki"
git push
```

## Notes

- Page titles = filename without `.md` (`Dual-PC-CS2.md` → URL `.../Dual-PC-CS2`)
- `Home.md` is the wiki home page
- `_Sidebar.md` controls the left menu on every page
- Do **not** upload `WIKI-UPLOAD.md` as a wiki page

