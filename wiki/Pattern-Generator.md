# Pattern Generator

Build weapon recoil data from spray captures (image or GIF).

---

## Open

1. Launch AimSync.
2. **Recoil Lab** → **Pattern Generator** (new tab).

Or run standalone:

```powershell
cd PatternGenerator
python gui.py
```

---

## Workflow

1. **Load media** — local `.png`, `.jpg`, `.webp`, `.gif` or URL.
2. **Auto-Suggest** — initial bullet points.
3. **Manual edit** — click to add, right-click undo, reorder list.
4. **Frame slider** — inspect GIF frames.
5. **Export mode** — keep **Canonical 1:1** for `weapon_data.py` style.
6. **Generate Pattern** — preview compensation vectors.
7. **Append to Game Data** — writes to `Recoil/games/<game>.py` (`.bak` created).

---

## API (embedded in dashboard)

Prefix: `/api/pattern-generator`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/weapons/<game_id>` | GET | List weapons for game |
| `/detect` | POST | Detect from uploaded file |
| `/detect-url` | POST | Detect from image URL |
| `/preview` | POST | Preview recoil pattern |
| `/append` | POST | Append to game Python file |

See [Local API](Local-API).
