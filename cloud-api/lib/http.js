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

function adminAuthorized(req) {
  const secret = process.env.ADMIN_SECRET || process.env.KRYPTAIM_ADMIN_SECRET || '';
  if (!secret) return false;
  const header = req.headers['x-admin-secret'] || req.headers['authorization'] || '';
  const token = String(header).replace(/^Bearer\s+/i, '').trim();
  return token === secret;
}

module.exports = { json, readJsonBody, adminAuthorized };
