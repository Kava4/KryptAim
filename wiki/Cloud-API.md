# Cloud API

Hosted services and remote configuration.

---

## License validation

Base URL (default): `https://project-mkgdr.vercel.app/api`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/license/validate` | POST | Validate supporter key + HWID |

Used when **AI premium mode** is enabled. Recoil stays free.

Override: env `KRYPTAIM_CLOUD_API`

Local proxy: `POST /api/access/validate_license`

---

## Remote feature flags

Fetched from GitHub (cached ~5 min):

```
https://raw.githubusercontent.com/AimSyncCore/KryptAim/Beta/release/app-config.json
```

Example:

```json
{
  "ai_premium_only": false
}
```

Set `"ai_premium_only": true` to lock AI behind Ko-fi keys **without rebuilding the exe**.

Override URL: env `KRYPTAIM_APP_CONFIG_URL`

---

## Community models (GitHub + Aimmy)

Not served from Vercel. The app reads:

| Source | Content |
|--------|---------|
| [AimSyncCore/KryptAim/models](https://github.com/AimSyncCore/KryptAim/tree/Beta/models) | Official catalog + `catalog.json` |
| [Aimmy models](https://github.com/Babyhamsta/Aimmy/tree/Aimmy-V2/models) | CS2 `.onnx` files (filtered) |

Local routes:

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/ai/community/models` | GET | Catalog + installed |
| `/api/ai/community/download` | POST | Download to `%APPDATA%\KryptAim\models\` |

---

## Pattern sharing (legacy cloud)

Recoil Lab pattern upload may use `/api/patterns` on the Vercel host if deployed. Optional for local-only use.

---

## Related

- [AI Engine](AI-Engine)
- [Configuration](Configuration)
