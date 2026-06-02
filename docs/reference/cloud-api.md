# Cloud API reference

**Production base URL:** `https://project-mkgdr.vercel.app`

Vercel rewrites all paths to `Cloud/api/index.py` (Flask).

---

## License

### `GET /api/license`

Returns API metadata.

### `POST /api/license/validate`

Validates donator keys and manages free trial state.

**Request (JSON):**

```json
{
  "key": "FREETRIAL",
  "hwid": "123456789",
  "activate_trial": true
}
```

| Field | Description |
|-------|-------------|
| `key` | Donator email/key, or `FREETRIAL` / empty for trial |
| `hwid` | Machine identifier (MAC-based from desktop app) |
| `activate_trial` | `true` to start daily trial window |

**Success (trial active):**

```json
{
  "valid": true,
  "tier": "Donator",
  "display_name": "Free Trial: 119m 45s left",
  "remaining_seconds": 7185,
  "trial_available": false,
  "days_left": null
}
```

**Trial not started:**

```json
{
  "valid": false,
  "trial_available": true,
  "display_name": "Free Trial Available"
}
```

**Exhausted:**

```json
{
  "valid": false,
  "error": "Daily 2-hour trial exhausted."
}
```

Trial keys are stored as `TRIAL_<hwid>` in Supabase `licenses` table.

---

## Community patterns

### `GET /api/patterns`

List pattern names and authors.

### `GET /api/pattern/content?name={name}`

Download pattern body.

### `POST /api/upload`

```json
{
  "name": "My Pattern",
  "author": "Player",
  "content": "0,-4,50\n-1,-3,45"
}
```

---

## Feedback

### `POST /api/feedback`

```json
{
  "message": "Bug description",
  "contact": "optional@email.com",
  "type": "Bug Report",
  "hwid": "..."
}
```

Forwards to Discord webhook when configured.

---

## Webhooks

| Path | Purpose |
|------|---------|
| `POST /api/webhook/kofi` | Ko-fi donations → license upsert |
| `POST /api/webhook/paypal` | PayPal events |
| `POST /api/webhook/patreon` | Patreon (stub) |

---

## Environment variables (Vercel)

| Variable | Required |
|----------|----------|
| `SUPABASE_URL` | Yes |
| `SUPABASE_KEY` | Yes (service role) |
| `KOFI_TOKEN` | Ko-fi webhook |
| `DISCORD_FEEDBACK_WEBHOOK` | Feedback |
| `PATREON_SECRET`, `PAYPAL_WEBHOOK_ID` | Optional |

---

## Database schema (licenses)

Run `Cloud/supabase_trial_migration.sql` in Supabase SQL Editor.

Required columns include: `key`, `active`, `tier`, `display_name`, `expires_at`, `trial_start`, `last_heartbeat`, `used_minutes`, `linked_hwids`, `max_hwids`, `last_ip`.

See [Cloud deployment](../development/cloud-deployment.md).

---

## Download redirect

### `GET /api/download`

Returns latest GitHub release URL JSON.
