-- AimSync: free Vision AI daily quota (2h/day per HWID)
-- Run once in Supabase SQL Editor

create table if not exists public.ai_free_quota (
  hwid text not null,
  usage_date date not null default (timezone('utc', now()))::date,
  used_seconds numeric not null default 0 check (used_seconds >= 0),
  limit_seconds numeric not null default 7200 check (limit_seconds > 0),
  updated_at timestamptz not null default now(),
  primary key (hwid, usage_date)
);

create index if not exists ai_free_quota_usage_date_idx
  on public.ai_free_quota (usage_date);

alter table public.ai_free_quota enable row level security;

-- No public policies: only service role (Vercel) may read/write.

create or replace function public.increment_ai_free_quota(
  p_hwid text,
  p_delta numeric,
  p_limit numeric default 7200
)
returns table (
  hwid text,
  usage_date date,
  used_seconds numeric,
  limit_seconds numeric
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_date date := (timezone('utc', now()))::date;
  v_limit numeric := greatest(60, coalesce(p_limit, 7200));
begin
  insert into public.ai_free_quota (hwid, usage_date, used_seconds, limit_seconds)
  values (p_hwid, v_date, 0, v_limit)
  on conflict (hwid, usage_date) do nothing;

  return query
  update public.ai_free_quota q
  set used_seconds = least(v_limit, q.used_seconds + greatest(0, coalesce(p_delta, 0))),
      limit_seconds = v_limit,
      updated_at = now()
  where q.hwid = p_hwid and q.usage_date = v_date
  returning q.hwid, q.usage_date, q.used_seconds, q.limit_seconds;
end;
$$;

grant execute on function public.increment_ai_free_quota(text, numeric, numeric) to service_role;
