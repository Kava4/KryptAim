# Classic UI backup

Snapshot before **KryptAim Hub** theme (tactical gold sidebar layout).

## Restore classic UI

```bat
copy /Y web\_backup_classic\templates\index.html web\templates\index.html
copy /Y web\_backup_classic\templates\_navbar.html web\templates\_navbar.html
copy /Y web\_backup_classic\templates\_footer.html web\templates\_footer.html
copy /Y web\_backup_classic\templates\_ai_panel.html web\templates\_ai_panel.html
copy /Y web\_backup_classic\templates\_shell_scripts.html web\templates\_shell_scripts.html
copy /Y web\_backup_classic\static\theme.css web\static\theme.css
copy /Y web\_backup_classic\static\shell.js web\static\shell.js
copy /Y web\_backup_classic\static\updates.js web\static\updates.js
```

Remove `kryptaim-hub.css`, `hub-nav.js`, `vision-feed.js` from `index.html` if linked.

Or open **`http://localhost:5000/?ui=classic`** (classic layout without editing files).
