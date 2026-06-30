const crypto = require('crypto');
const { getSupabase } = require('./supabase');

const MONTHLY_DAYS = Number(process.env.SUPPORTER_MONTHLY_DAYS || 30);

function normalizeKey(raw) {
  return String(raw || '').trim().toUpperCase();
}

function normalizeHwid(raw) {
  const hwid = String(raw || '').trim();
  if (!hwid || hwid.length > 128) return null;
  return hwid;
}

function normalizePlan(raw) {
  const plan = String(raw || 'monthly').trim().toLowerCase();
  return plan === 'unlimited' ? 'unlimited' : 'monthly';
}

function monthlyExpiryFromNow() {
  return new Date(Date.now() + MONTHLY_DAYS * 24 * 60 * 60 * 1000).toISOString();
}

function daysLeft(expiresAt) {
  if (!expiresAt) return null;
  const ms = new Date(expiresAt).getTime() - Date.now();
  return Math.max(0, Math.ceil(ms / (24 * 60 * 60 * 1000)));
}

function isMonthlyExpired(row) {
  if (normalizePlan(row.plan) !== 'monthly') return false;
  if (!row.expires_at) return false;
  return new Date(row.expires_at).getTime() <= Date.now();
}

function invalid(message) {
  return {
    valid: false,
    tier: 'Free',
    plan: 'free',
    display_name: '',
    message: message || 'Invalid key',
    unlimited: false,
    days_left: 0,
  };
}

function valid(row) {
  const plan = normalizePlan(row.plan);
  const unlimited = plan === 'unlimited';
  const left = unlimited ? null : daysLeft(row.expires_at);
  return {
    valid: true,
    tier: unlimited ? 'Supporter Unlimited' : 'Supporter Monthly',
    plan,
    display_name: row.label || 'Supporter',
    message: '',
    license_key: row.license_key,
    hwid_bound: Boolean(row.hwid),
    unlimited,
    days_left: left,
    expires_at: row.expires_at || null,
  };
}

const KEY_FIELDS = 'license_key, hwid, label, status, plan, expires_at, bound_at';

async function validateSupporterKey(key, hwid) {
  const licenseKey = normalizeKey(key);
  if (!licenseKey) return invalid('Key required');

  const supabase = getSupabase();
  const { data: row, error } = await supabase
    .from('supporter_keys')
    .select(KEY_FIELDS)
    .eq('license_key', licenseKey)
    .maybeSingle();

  if (error) throw error;
  if (!row) return invalid('Key not found');
  if (row.status !== 'active') return invalid('Key revoked');
  if (isMonthlyExpired(row)) return invalid('Monthly subscription expired');

  if (!row.hwid) {
    const bindPatch = {
      hwid,
      bound_at: new Date().toISOString(),
    };
    if (normalizePlan(row.plan) === 'monthly' && !row.expires_at) {
      bindPatch.expires_at = monthlyExpiryFromNow();
    }
    const { data: bound, error: bindErr } = await supabase
      .from('supporter_keys')
      .update(bindPatch)
      .eq('license_key', licenseKey)
      .is('hwid', null)
      .select(KEY_FIELDS)
      .maybeSingle();
    if (bindErr) throw bindErr;
    if (!bound) {
      const { data: again } = await supabase
        .from('supporter_keys')
        .select(KEY_FIELDS)
        .eq('license_key', licenseKey)
        .maybeSingle();
      if (!again || again.hwid !== hwid) return invalid('Key already bound to another PC');
      if (isMonthlyExpired(again)) return invalid('Monthly subscription expired');
      return valid(again);
    }
    if (isMonthlyExpired(bound)) return invalid('Monthly subscription expired');
    return valid(bound);
  }

  if (row.hwid !== hwid) return invalid('Key bound to another PC');
  return valid(row);
}

function generateKey() {
  const seg = () => crypto.randomBytes(2).toString('hex').toUpperCase();
  return `KR-${seg()}-${seg()}-${seg()}`;
}

async function createKey({ label, notes, source, licenseKey, plan }) {
  const supabase = getSupabase();
  const key = normalizeKey(licenseKey || generateKey());
  const normalizedPlan = normalizePlan(plan);
  const { data, error } = await supabase
    .from('supporter_keys')
    .insert({
      license_key: key,
      label: label || (normalizedPlan === 'unlimited' ? 'Supporter Unlimited' : 'Supporter Monthly'),
      notes: notes || null,
      source: source || 'admin',
      status: 'active',
      plan: normalizedPlan,
      expires_at: null,
    })
    .select('license_key, label, status, source, plan, created_at')
    .single();
  if (error) throw error;
  return data;
}

async function revokeKey(licenseKey) {
  const supabase = getSupabase();
  const key = normalizeKey(licenseKey);
  const { data, error } = await supabase
    .from('supporter_keys')
    .update({ status: 'revoked' })
    .eq('license_key', key)
    .select('license_key, status')
    .maybeSingle();
  if (error) throw error;
  if (!data) return null;
  return data;
}

async function resetHwid(licenseKey) {
  const supabase = getSupabase();
  const key = normalizeKey(licenseKey);
  const { data, error } = await supabase
    .from('supporter_keys')
    .update({ hwid: null, bound_at: null })
    .eq('license_key', key)
    .select('license_key, hwid, status, plan, expires_at')
    .maybeSingle();
  if (error) throw error;
  return data;
}

async function deleteKey(licenseKey) {
  const supabase = getSupabase();
  const key = normalizeKey(licenseKey);
  const { data, error } = await supabase
    .from('supporter_keys')
    .delete()
    .eq('license_key', key)
    .select('license_key')
    .maybeSingle();
  if (error) throw error;
  return data;
}

async function listKeys({ limit = 50, status = '' } = {}) {
  const supabase = getSupabase();
  let query = supabase
    .from('supporter_keys')
    .select(
      'license_key, hwid, label, status, source, plan, expires_at, created_at, bound_at',
      { count: 'exact' },
    )
    .order('created_at', { ascending: false })
    .limit(Math.min(200, Math.max(1, limit)));
  if (status) query = query.eq('status', status);
  const { data, error, count } = await query;
  if (error) throw error;
  return { keys: data || [], count };
}

module.exports = {
  normalizeKey,
  normalizeHwid,
  normalizePlan,
  validateSupporterKey,
  createKey,
  revokeKey,
  resetHwid,
  deleteKey,
  listKeys,
  generateKey,
  MONTHLY_DAYS,
};
