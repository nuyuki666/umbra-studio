import { query } from './db.js';

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { action, login, email, password_hash, name, company, phone, old_hash, new_hash } = req.body || {};

    if (action === 'register') {
      if (!login || !email || !password_hash || !name) {
        return res.status(400).json({ error: 'Заполните обязательные поля' });
      }

      // Check existing
      const existing = await query(
        `SELECT id, login, email FROM studio_users WHERE login = '${login.replace(/'/g, "''")}' OR email = '${email.replace(/'/g, "''")}';`
      );
      if (existing.length > 0) {
        return res.status(400).json({ error: 'Пользователь с таким логином или email уже существует' });
      }

      const rows = await query(
        `INSERT INTO studio_users (login, email, password_hash, name, company, phone) 
         VALUES ('${login.replace(/'/g, "''")}', '${email.replace(/'/g, "''")}', '${password_hash.replace(/'/g, "''")}', '${name.replace(/'/g, "''")}', '${(company || '').replace(/'/g, "''")}', '${(phone || '').replace(/'/g, "''")}')
         RETURNING id, login, email, name, company, phone, role, created_at;`
      );

      return res.status(200).json({ ok: true, user: rows[0] });
    }

    if (action === 'login') {
      const qVal = (login || email || '').trim().replace(/'/g, "''");
      const rows = await query(
        `SELECT id, login, email, password_hash, name, company, phone, role, created_at 
         FROM studio_users 
         WHERE login = '${qVal}' OR email = '${qVal}' 
         LIMIT 1;`
      );

      if (rows.length === 0) {
        return res.status(401).json({ error: 'Пользователь не найден' });
      }

      const user = rows[0];
      if (user.password_hash !== password_hash) {
        return res.status(401).json({ error: 'Неверный пароль' });
      }

      delete user.password_hash;
      return res.status(200).json({ ok: true, user });
    }

    if (action === 'change_password') {
      const qVal = (login || '').trim().replace(/'/g, "''");
      const rows = await query(
        `SELECT id, password_hash FROM studio_users WHERE login = '${qVal}' OR email = '${qVal}' LIMIT 1;`
      );

      if (rows.length === 0) {
        return res.status(404).json({ error: 'Пользователь не найден' });
      }

      if (rows[0].password_hash !== old_hash) {
        return res.status(400).json({ error: 'Текущий пароль указан неверно' });
      }

      await query(
        `UPDATE studio_users SET password_hash = '${new_hash.replace(/'/g, "''")}' WHERE id = ${rows[0].id};`
      );

      return res.status(200).json({ ok: true });
    }

    if (action === 'update_profile') {
      const qVal = (login || '').trim().replace(/'/g, "''");
      const rows = await query(
        `UPDATE studio_users 
         SET name = '${(name || '').replace(/'/g, "''")}', 
             company = '${(company || '').replace(/'/g, "''")}', 
             phone = '${(phone || '').replace(/'/g, "''")}' 
         WHERE login = '${qVal}' OR email = '${qVal}'
         RETURNING id, login, email, name, company, phone, role, created_at;`
      );

      if (rows.length === 0) {
        return res.status(404).json({ error: 'Пользователь не найден' });
      }

      return res.status(200).json({ ok: true, user: rows[0] });
    }

    return res.status(400).json({ error: 'Неизвестное действие' });
  } catch (err) {
    console.error('Auth API Error:', err);
    return res.status(500).json({ error: 'Ошибка сервера базы данных: ' + err.message });
  }
}
