const { json, readJsonBody } = require('../../lib/http');
const { normalizeHwid, validateSupporterKey } = require('../../lib/license');

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return json(res, 405, { valid: false, error: 'Method not allowed' });
  }

  try {
    const body = await readJsonBody(req);
    const key = body.key || body.license_key || '';
    const hwid = normalizeHwid(body.hwid);
    if (!hwid) {
      return json(res, 400, { valid: false, message: 'hwid required' });
    }
    const result = await validateSupporterKey(key, hwid);
    return json(res, 200, { ok: true, ...result });
  } catch (err) {
    console.error('[license/validate]', err);
    return json(res, 500, { valid: false, message: err.message || 'Internal error' });
  }
};
