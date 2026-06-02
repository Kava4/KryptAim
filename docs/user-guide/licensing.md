# Licensing and free trial

AimSync uses a hybrid license model: local dashboard plus remote validation on Vercel with Supabase storage.

## Tiers

| Tier | Access |
|------|--------|
| **Free** | Global Settings, Safety, Simple Recoil, Recoil Lab (local save only) |
| **Trial** | Same as Donator for **2 hours of active use per calendar day** |
| **Donator** | Game Engine, cloud upload, supporter display name |

Trial and paid keys are verified against `https://project-mkgdr.vercel.app/api/license/validate`.

## Free trial mechanics

| Rule | Detail |
|------|--------|
| Duration | 120 minutes per day |
| Reset | Midnight UTC (based on last heartbeat date) |
| Binding | One trial row per machine: `TRIAL_<HWID>` |
| Pausable | Time only accrues while the app is open (heartbeat gaps under 5 minutes count) |
| Activation | User must click **Start Free Trial** once per day |

The UI shows a live countdown (`Free Trial: Xm YYs left`). License status refreshes on page load and every 15 seconds.

## Donator keys

Enter your Ko-fi / PayPal email or issued key in **Donator License → Apply**. Valid keys:

- Bind to HWID (device limit enforced server-side)
- Auto-ban if too many devices share one key
- May include `expires_at` for time-limited access

## Premium cache (anti-tamper)

`config.json` includes `is_premium`, but feature gates use an in-memory cache in `Server/cloud_manager.py` revalidated every five minutes against the Cloud API. Editing `is_premium` locally does not permanently unlock features.

## Administrator setup

For self-hosting the Cloud API or fixing trial database errors, see:

- [Cloud deployment](../development/cloud-deployment.md)
- SQL migration: `Cloud/supabase_trial_migration.sql`

## Troubleshooting trial

| Symptom | Fix |
|---------|-----|
| Trial activation failed | Run Supabase migration; use `service_role` key on Vercel |
| Game Engine still locked | Restart app after trial; hard-refresh browser |
| Countdown frozen | Ensure `license-status` HTMX poll is running (15s) |

See [Troubleshooting](../support/troubleshooting.md).
