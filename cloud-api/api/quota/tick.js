const { json, normalizeHwid, readJsonBody, tickQuota } = require('../../lib/quota');

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return json(res, 405, { ok: false, error: 'Method not allowed' });
  }

  try {
    const body = await readJsonBody(req);
    const hwid = normalizeHwid(body.hwid);
    if (!hwid) {
      return json(res, 400, { ok: false, error: 'hwid required' });
    }
    const delta = Number(body.delta_seconds ?? body.delta ?? 0);
    if (!Number.isFinite(delta) || delta < 0 || delta > 600) {
      return json(res, 400, { ok: false, error: 'delta_seconds must be 0..600' });
    }
    const status = await tickQuota(hwid, delta);
    return json(res, 200, status);
  } catch (err) {
    console.error('[quota/tick]', err);
    return json(res, 500, { ok: false, error: err.message || 'Internal error' });
  }
};
