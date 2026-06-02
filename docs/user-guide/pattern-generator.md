# Pattern Generator

Pattern Generator converts spray screenshots/GIFs into recoil steps and can write them directly to Game Engine weapon data files.

## Where to open it

- Embedded in **Recoil Lab** via the **Pattern Generator** button.
- Standalone page at `http://127.0.0.1:5000/pattern-generator`.

## Workflow

1. Choose an image or GIF (`.png`, `.jpg`, `.webp`, `.gif`).
2. Use **Auto-Suggest** or click bullet points manually in order.
3. Tune `Delay`, `Scale X/Y`, and invert options.
4. Click **Generate Pattern** to produce `x,y,delay_ms` text.
5. (Optional) Click **Send to Recoil Lab** to push output into the editor.
6. Select game + weapon name and click **Append to Game Data**.

## Append behavior

- Appends or updates only the selected weapon in `Recoil/games/<game>.py`.
- Creates a timestamped `.bak` backup before writing.
- Uses deterministic formatting for easier diff/review.

## Notes

- Manual-first is the primary v1 flow.
- Auto-Suggest is a simple helper and may require manual cleanup.
- This tool edits local game data files; keep backups under version control when possible.
