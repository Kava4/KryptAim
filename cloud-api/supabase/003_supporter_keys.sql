-- AimSync supporter keys (fresh — ignore legacy licenses table)
-- Run in Supabase SQL Editor

create table if not exists public.supporter_keys (
  license_key text primary key,
  hwid text,
  label text not null default 'Supporter',
  plan text not null default 'monthly' check (plan in ('monthly', 'unlimited')),
  status text not null default 'active' check (status in ('active', 'revoked')),
  source text not null default 'manual',
  notes text,
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  bound_at timestamptz
);

create index if not exists supporter_keys_hwid_idx on public.supporter_keys (hwid);
create index if not exists supporter_keys_status_idx on public.supporter_keys (status);

alter table public.supporter_keys enable row level security;
-- No public policies — Vercel uses service role only.

create or replace function public.touch_supporter_key_updated()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists supporter_keys_updated on public.supporter_keys;
create trigger supporter_keys_updated
  before update on public.supporter_keys
  for each row execute function public.touch_supporter_key_updated();
