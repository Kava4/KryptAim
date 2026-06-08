# Cloud API

Hosted services for licensing placeholders and community pattern sharing.

Base URL (default): `https://project-mkgdr.vercel.app`

---

## Pattern sharing

Used by Recoil Lab **Share** / **Refresh Community**.

| Endpoint | Purpose |
|----------|---------|
| List patterns | Returns community pattern metadata |
| Upload | POST pattern JSON with username |
| Load | Fetch pattern by id |

Empty community list is normal until users upload patterns.

Remote **model download** from a public store is **disabled** — use local `bin/models/` or manual upload in the AI tab.

---

## Licensing (placeholder)

Access mode is currently **free for all users**. `license_key` and `is_premium` fields exist for future use.

See dashboard **Access mode** section.

---

## Deployment

Maintainers deploy the cloud API separately (Vercel + Supabase). Not required for local-only / offline use.
