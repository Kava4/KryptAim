const { adminAuthorized, json, readJsonBody } = require('../../../lib/http');
const { createKey } = require('../../../lib/license');

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return json(res, 405, { ok: false, error: 'Method not allowed' });
  }
  if (!adminAuthorized(req)) {
    return json(res, 401, { ok: false, error: 'Unauthorized' });
  }

  try {
    const body = await readJsonBody(req);
    const row = await createKey({
      label: body.label,
      notes: body.notes,
      source: body.source || 'admin',
      licenseKey: body.license_key || body.key,
      plan: body.plan,
    });
    return json(res, 200, { ok: true, key: row });
  } catch (err) {
    console.error('[admin/keys/create]', err);
    return json(res, 500, { ok: false, error: err.message || 'Internal error' });
  }
};
