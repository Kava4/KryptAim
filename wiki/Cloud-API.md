# Cloud API

Hosted services and remote configuration.

---

## License validation

Base URL (default): `https://project-mkgdr.vercel.app/api`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/license/validate` | POST | Validate supporter key + HWID |
| `/quota/status` | POST | Read free Vision AI daily quota (HWID) |
| `/quota/tick` | POST | Add engine runtime seconds (HWID) |

Used when **AI premium mode** is enabled. Recoil stays free.

Override: env `KRYPTAIM_CLOUD_API`

Local proxy: `POST /api/access/validate_license`

### Free tier quota (2h/day)

When `ai_premium_only` is **false**, Vision AI is free with a **120 min/day** limit tracked per HWID.

- **Cloud (Supabase)** is the source of truth when online
- Local `ai_free_usage.json` is cache + offline fallback
- Disable cloud sync: env `AI_FREE_QUOTA_CLOUD_OFF=1`
- Disable quota entirely: env `AI_FREE_QUOTA_OFF=1`

Deploy cloud routes: see `cloud-api/README.md` in the repo.

Supporter keys bypass quota (unlimited) via `/license/validate`.

---

## Remote feature flags

Fetched from GitHub (cached ~5 min):

```
https://raw.githubusercontent.com/Kava4/AimSync/Beta/release/app-config.json
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
| [Kava4/AimSync/models](https://github.com/Kava4/AimSync/tree/Beta/models) | Official catalog + `catalog.json` |
| [Aimmy models](https://github.com/Babyhamsta/Aimmy/tree/Aimmy-V2/models) | CS2 `.onnx` files (filtered) |

Local routes:

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/ai/community/models` | GET | Catalog + installed |
| `/api/ai/community/download` | POST | Download to `%APPDATA%\AimSync\models\` |

---

## Pattern sharing (legacy cloud)

Recoil Lab pattern upload may use `/api/patterns` on the Vercel host if deployed. Optional for local-only use.

---

## Related

- [AI Engine](AI-Engine)
- [Configuration](Configuration)
