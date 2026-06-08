# Upload these pages to GitHub Wiki

GitHub Wiki is a **separate git repository**:

```
https://github.com/Kava4/AimSync.wiki.git
```

## One-time setup

```bash
git clone https://github.com/Kava4/AimSync.wiki.git
cd AimSync.wiki
```

Copy every `.md` file from this `wiki/` folder into the clone **except** `WIKI-UPLOAD.md`.

Required files:
- `Home.md` (wiki front page)
- `_Sidebar.md` (left navigation)
- All other `*.md` pages

## Publish

```bash
cd AimSync.wiki
git add .
git commit -m "Initial AimSync wiki"
git push
```

Wiki will be live at: https://github.com/Kava4/AimSync/wiki

## Update later

Edit pages in the wiki clone (or use the GitHub web editor), then `git commit` + `git push`.

## Notes

- Page titles = filename without `.md` (`Dual-PC-CS2.md` → URL `.../Dual-PC-CS2`)
- `Home.md` is the wiki home page
- `_Sidebar.md` controls the left menu on every page
- Do **not** upload `WIKI-UPLOAD.md` as a wiki page
