const { fetchQuotaStatus, json, normalizeHwid, readJsonBody } = require('../../lib/quota');

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
    const status = await fetchQuotaStatus(hwid);
    return json(res, 200, status);
  } catch (err) {
    console.error('[quota/status]', err);
    return json(res, 500, { ok: false, error: err.message || 'Internal error' });
  }
};
