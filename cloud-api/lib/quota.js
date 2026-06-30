const { getSupabase } = require('./supabase');

const DEFAULT_LIMIT_SECONDS = Number(process.env.AI_FREE_DAILY_SECONDS || 7200);

function todayUtc() {
  return new Date().toISOString().slice(0, 10);
}

function normalizeHwid(raw) {
  const hwid = String(raw || '').trim();
  if (!hwid || hwid.length > 128) return null;
  return hwid;
}

function buildStatus(row, limitSeconds = DEFAULT_LIMIT_SECONDS) {
  const used = Number(row?.used_seconds || 0);
  const limit = Number(row?.limit_seconds || limitSeconds);
  const remaining = Math.max(0, limit - used);
  return {
    ok: true,
    date: row?.usage_date || todayUtc(),
    hwid: row?.hwid,
    limit_seconds: limit,
    limit_minutes: Math.max(1, Math.round(limit / 60)),
    used_seconds: used,
    used_minutes: Math.max(0, Math.round(used / 60)),
    remaining_seconds: Math.round(remaining),
    remaining_minutes: Math.max(0, Math.round(remaining / 60)),
    exhausted: remaining <= 0,
    unlimited: false,
  };
}

async function fetchQuotaStatus(hwid) {
  const supabase = getSupabase();
  const usageDate = todayUtc();
  const { data, error } = await supabase
    .from('ai_free_quota')
    .select('hwid, usage_date, used_seconds, limit_seconds')
    .eq('hwid', hwid)
    .eq('usage_date', usageDate)
    .maybeSingle();

  if (error) throw error;
  if (!data) {
    return buildStatus({ hwid, usage_date: usageDate, used_seconds: 0, limit_seconds: DEFAULT_LIMIT_SECONDS });
  }
  return buildStatus(data);
}

async function tickQuota(hwid, deltaSeconds) {
  const delta = Math.max(0, Number(deltaSeconds) || 0);
  const supabase = getSupabase();
  const usageDate = todayUtc();
  const limit = DEFAULT_LIMIT_SECONDS;

  const { data: existing, error: readErr } = await supabase
    .from('ai_free_quota')
    .select('hwid, usage_date, used_seconds, limit_seconds')
    .eq('hwid', hwid)
    .eq('usage_date', usageDate)
    .maybeSingle();

  if (readErr) throw readErr;

  const nextUsed = Math.min(limit, Number(existing?.used_seconds || 0) + delta);

  const { data, error } = await supabase
    .from('ai_free_quota')
    .upsert(
      {
        hwid,
        usage_date: usageDate,
        used_seconds: nextUsed,
        limit_seconds: limit,
        updated_at: new Date().toISOString(),
      },
      { onConflict: 'hwid,usage_date' },
    )
    .select('hwid, usage_date, used_seconds, limit_seconds')
    .single();

  if (error) throw error;
  return buildStatus(data);
}

function json(res, statusCode, body) {
  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify(body));
}

async function readJsonBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString('utf8').trim();
  if (!raw) return {};
  return JSON.parse(raw);
}

module.exports = {
  DEFAULT_LIMIT_SECONDS,
  normalizeHwid,
  fetchQuotaStatus,
  tickQuota,
  json,
  readJsonBody,
};
