-- Fix: "column reference hwid is ambiguous" (optional — tick now uses direct upsert in Vercel)
-- Safe to re-run

create or replace function public.increment_ai_free_quota(
  p_hwid text,
  p_delta numeric,
  p_limit numeric default 7200
)
returns table (
  out_hwid text,
  out_usage_date date,
  out_used_seconds numeric,
  out_limit_seconds numeric
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
  select u.hwid, u.usage_date, u.used_seconds, u.limit_seconds
  from (
    update public.ai_free_quota as t
    set used_seconds = least(v_limit, t.used_seconds + greatest(0, coalesce(p_delta, 0))),
        limit_seconds = v_limit,
        updated_at = now()
    where t.hwid = p_hwid and t.usage_date = v_date
    returning t.hwid, t.usage_date, t.used_seconds, t.limit_seconds
  ) as u;
end;
$$;

grant execute on function public.increment_ai_free_quota(text, numeric, numeric) to service_role;
