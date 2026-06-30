const { adminAuthorized, json } = require('../../../lib/http');
const { listKeys } = require('../../../lib/license');

module.exports = async (req, res) => {
  if (req.method !== 'GET') {
    return json(res, 405, { ok: false, error: 'Method not allowed' });
  }
  if (!adminAuthorized(req)) {
    return json(res, 401, { ok: false, error: 'Unauthorized' });
  }

  try {
    const url = new URL(req.url, 'http://localhost');
    const limit = Number(url.searchParams.get('limit') || 50);
    const status = url.searchParams.get('status') || '';
    const result = await listKeys({ limit, status });
    return json(res, 200, { ok: true, ...result });
  } catch (err) {
    console.error('[admin/keys/list]', err);
    return json(res, 500, { ok: false, error: err.message || 'Internal error' });
  }
};
