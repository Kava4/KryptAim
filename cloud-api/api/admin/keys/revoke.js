const { adminAuthorized, json, readJsonBody } = require('../../../lib/http');
const { revokeKey } = require('../../../lib/license');

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return json(res, 405, { ok: false, error: 'Method not allowed' });
  }
  if (!adminAuthorized(req)) {
    return json(res, 401, { ok: false, error: 'Unauthorized' });
  }

  try {
    const body = await readJsonBody(req);
    const key = body.license_key || body.key || '';
    const row = await revokeKey(key);
    if (!row) return json(res, 404, { ok: false, error: 'Key not found' });
    return json(res, 200, { ok: true, key: row });
  } catch (err) {
    console.error('[admin/keys/revoke]', err);
    return json(res, 500, { ok: false, error: err.message || 'Internal error' });
  }
};
