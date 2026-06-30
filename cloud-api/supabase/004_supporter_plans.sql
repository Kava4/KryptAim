-- Add monthly vs unlimited plans (run if supporter_keys already exists)

alter table public.supporter_keys
  add column if not exists plan text not null default 'monthly';

alter table public.supporter_keys
  add column if not exists expires_at timestamptz;

alter table public.supporter_keys drop constraint if exists supporter_keys_plan_check;
alter table public.supporter_keys
  add constraint supporter_keys_plan_check check (plan in ('monthly', 'unlimited'));

create index if not exists supporter_keys_plan_idx on public.supporter_keys (plan);
create index if not exists supporter_keys_expires_idx on public.supporter_keys (expires_at);
