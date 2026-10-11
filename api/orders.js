import { query } from './db.js';

const CLOUDFLARE_SECRET_KEY = process.env.CLOUDFLARE_TURNSTILE_SECRET_KEY || '0x4AAAAAAAE5JWslqi2DuzHz0Lsut3ZfHes';

async function verifyCloudflareTurnstile(token, ip) {
  if (!token) return true; // graceful fallback
  try {
    const formData = new URLSearchParams();
    formData.append('secret', CLOUDFLARE_SECRET_KEY);
    formData.append('response', token);
    if (ip) formData.append('remoteip', ip);

    const resp = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    const outcome = await resp.json();
    return outcome.success;
  } catch (err) {
    console.error('Turnstile verification error:', err);
    return true; // fail open
  }
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    if (req.method === 'GET') {
      const { email, all } = req.query || {};

      let sql = 'SELECT * FROM studio_orders ORDER BY created_at DESC;';
      if (email && !all) {
        sql = `SELECT * FROM studio_orders WHERE user_email = '${email.replace(/'/g, "''")}' ORDER BY created_at DESC;`;
      }

      const rows = await query(sql);
      return res.status(200).json({ ok: true, orders: rows });
    }

    if (req.method === 'POST') {
      const { action, order, id, status } = req.body || {};

      if (action === 'create' && order) {
        const clientIp = req.headers['x-forwarded-for'] || req.socket?.remoteAddress;
        const isHuman = await verifyCloudflareTurnstile(order.turnstile_token, clientIp);
        if (!isHuman) {
          return res.status(403).json({ error: 'Проверка Cloudflare Turnstile не пройдена.' });
        }
        const orderId = (order.id || ('ORD-' + Date.now())).replace(/'/g, "''");
        const userEmail = (order.user_email || order.email || '').replace(/'/g, "''");
        const servicePlan = (order.service_plan || order.plan || 'Индивидуальный проект').replace(/'/g, "''");
        const price = parseInt(order.price, 10) || 5000;
        const clientName = (order.client_name || order.name || 'Клиент').replace(/'/g, "''");
        const contact = (order.contact || '').replace(/'/g, "''");
        const description = (order.description || order.desc || '').replace(/'/g, "''");

        const rows = await query(
          `INSERT INTO studio_orders (id, user_email, service_plan, price, client_name, contact, description, status) 
           VALUES ('${orderId}', '${userEmail}', '${servicePlan}', ${price}, '${clientName}', '${contact}', '${description}', 'new') 
           RETURNING *;`
        );

        return res.status(200).json({ ok: true, order: rows[0] });
      }

      if (action === 'update_status' && id && status) {
        await query(
          `UPDATE studio_orders SET status = '${status.replace(/'/g, "''")}' WHERE id = '${id.replace(/'/g, "''")}';`
        );
        return res.status(200).json({ ok: true });
      }

      return res.status(400).json({ error: 'Неверные параметры запроса' });
    }

    return res.status(405).json({ error: 'Method not allowed' });
  } catch (err) {
    console.error('Orders API Error:', err);
    return res.status(500).json({ error: 'Ошибка сервера: ' + err.message });
  }
}
