# Cloud deployment

The Cloud stack hosts the public landing page, license server, and community pattern API.

## Stack

| Service | Role |
|---------|------|
| Vercel | Hosts `Cloud/api/index.py` as serverless Flask |
| Supabase | PostgreSQL `licenses` and `patterns` tables |
| Discord webhook | Optional feedback relay |

**Production URL:** `https://project-mkgdr.vercel.app`

Desktop app setting: `CLOUD_API_URL` in `Server/app.py` and `Server/cloud_manager.py`.

---

## Deploy to Vercel

```bash
cd Cloud
vercel --prod
```

`vercel.json` rewrites all routes to the Python function:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "api/index" }]
}
```

## Environment variables

| Name | Description |
|------|-------------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_KEY` | **service_role** secret (required for writes) |
| `KOFI_TOKEN` | Ko-fi webhook verification |
| `DISCORD_FEEDBACK_WEBHOOK` | Feedback embeds |
| `PATREON_SECRET` | Optional |
| `PAYPAL_WEBHOOK_ID` | Optional |

Never use the Supabase `anon` key for the license API if RLS blocks inserts.

---

## Database setup

1. Open Supabase → SQL Editor.
2. Run the full script: `Cloud/supabase_trial_migration.sql`.

This adds trial columns (`trial_start`, `last_heartbeat`, `used_minutes`, …) and `display_name`, plus a `service_role` RLS policy.

### Verify trial endpoint

```powershell
python -c "import requests; r=requests.post('https://project-mkgdr.vercel.app/api/license/validate', json={'key':'FREETRIAL','hwid':'test-123','activate_trial':True}); print(r.status_code, r.text)"
```

Expect `200` and `"valid": true`.

---

## Trial logic summary

| Constant | Value |
|----------|-------|
| `TRIAL_LIMIT_MINUTES` | 120 (2 hours) |
| License key | `TRIAL_<hwid>` |
| Reset | New UTC day |
| Accrual | Heartbeat deltas while app open (< 5 min gaps) |

Implementation: `Cloud/api/index.py` → `validate_license_remote()`.

---

## Ko-fi automation

`POST /api/webhook/kofi` upserts `licenses` row with donor email as `key`, `tier: Donator`, `active: true`.

Configure the verification token to match `KOFI_TOKEN` in Vercel.

---

## Local vs cloud pattern paths

| Client | URL pattern |
|--------|-------------|
| `cloud_manager.py` | `https://project-mkgdr.vercel.app/api/...` |
| `Server/app.py` proxy | Same host + `/api/...` |

---

## Troubleshooting

| Error | Cause |
|-------|--------|
| `display_name` column not found | Migration not applied |
| Trial activation failed | RLS or wrong API key |
| 500 on validate | Check Vercel function logs |

See [Troubleshooting](../support/troubleshooting.md).
