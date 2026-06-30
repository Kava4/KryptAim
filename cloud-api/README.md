# AimSync Cloud API

Deploy to **Vercel** (`project-mkgdr`) + **Supabase**.

## Supabase SQL (run in order)

1. `supabase/001_ai_free_quota.sql` — free 2h/day quota per HWID
2. `supabase/003_supporter_keys.sql` — supporter license keys (**new table, ignore old `licenses`**)

## Vercel env vars

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_KEY` | Service role key |
| `AI_FREE_DAILY_SECONDS` | `7200` (optional) |
| `ADMIN_SECRET` | Secret for admin key management routes |

## Deploy files

```
lib/supabase.js
lib/http.js
lib/quota.js
lib/license.js
api/quota/status.js
api/quota/tick.js
api/license/validate.js
api/admin/keys/create.js
api/admin/keys/revoke.js
api/admin/keys/reset-hwid.js
api/admin/keys/list.js
```

```bash
npm install @supabase/supabase-js
vercel deploy --prod
```

---

## Admin mini-app (browser UI)

After deploy, open:

```
https://project-mkgdr.vercel.app/admin
```

1. Enter your `ADMIN_SECRET` (stored in browser session only)
2. Create **monthly** or **unlimited** keys
3. Copy, list, revoke, reset PC binding — no curl needed

Deploy the `public/` folder with your Vercel project (Vercel serves `public/admin/index.html` automatically).

---

## Supporter keys — daily management (curl alternative)

### Create a key (admin)

```bash
# Monthly supporter (< €25) — 30 days Vision AI from first activation
curl -X POST https://project-mkgdr.vercel.app/api/admin/keys/create \
  -H "Content-Type: application/json" \
  -H "x-admin-secret: YOUR_ADMIN_SECRET" \
  -d "{\"label\":\"Monthly supporter\",\"plan\":\"monthly\"}"

# Unlimited supporter (€25+) — no expiry
curl -X POST https://project-mkgdr.vercel.app/api/admin/keys/create \
  -H "Content-Type: application/json" \
  -H "x-admin-secret: YOUR_ADMIN_SECRET" \
  -d "{\"label\":\"VIP supporter\",\"plan\":\"unlimited\"}"
```

| Plan | Who | Vision AI |
|------|-----|-----------|
| `monthly` | Standard Ko-fi / &lt; €25 | Full access **30 days** from first PC activation |
| `unlimited` | €25+ donations | **No expiry**, no daily 2h cap |

Optional env: `SUPPORTER_MONTHLY_DAYS=30`

Response includes auto-generated key: `KR-A1B2-C3D4-E5F6`

Optional body fields: `license_key` (custom), `notes`, `source`, `plan`

### List keys

```bash
curl "https://project-mkgdr.vercel.app/api/admin/keys/list?limit=50" \
  -H "x-admin-secret: YOUR_ADMIN_SECRET"
```

### Revoke key

```bash
curl -X POST https://project-mkgdr.vercel.app/api/admin/keys/revoke \
  -H "Content-Type: application/json" \
  -H "x-admin-secret: YOUR_ADMIN_SECRET" \
  -d "{\"license_key\":\"KR-....\"}"
```

### Reset HWID (move key to new PC)

```bash
curl -X POST https://project-mkgdr.vercel.app/api/admin/keys/reset-hwid \
  -H "Content-Type: application/json" \
  -H "x-admin-secret: YOUR_ADMIN_SECRET" \
  -d "{\"license_key\":\"KR-....\"}"
```

### Validate (app uses this automatically)

```bash
curl -X POST https://project-mkgdr.vercel.app/api/license/validate \
  -H "Content-Type: application/json" \
  -d "{\"key\":\"KR-....\",\"hwid\":\"123456789\"}"
```

---

## Free quota

See `POST /api/quota/status` and `POST /api/quota/tick` — same as before.

Supporter keys bypass the **2h/day free cap** while active:

- **monthly** — 30 days from first activation (then back to free tier)
- **unlimited** — no expiry (€25+ tier)

---

## App

- Keys validated via `app/core/license_cloud.py` → cloud API
- User enters key in **Global Settings** or **Activate Vision AI**
- First activation binds **HWID** (one PC per key)
- Dev key `DEV-KRYPTAIM` only with `run_dev.bat`
