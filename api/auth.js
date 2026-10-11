import { query } from './db.js';

const CLOUDFLARE_SECRET_KEY = process.env.CLOUDFLARE_TURNSTILE_SECRET_KEY || '0x4AAAAAAAE5JWslqi2DuzHz0Lsut3ZfHes';

async function verifyCloudflareTurnstile(token, ip) {
  if (!token) return true; // graceful fallback for local testing
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
    console.error('Cloudflare Turnstile verify error:', err);
    return true; // fail open
  }
}

const FORBIDDEN_PATTERNS = [
  /gitler/i,
  /hitler/i,
  /гитлер/i,
  /nazi/i,
  /нацист/i,
  /фашист/i,
  /fascist/i,
  /fuhrer/i,
  /f[uü]hrer/i,
  /фюрер/i,
  /ху[йеяиёю]/i,
  /xui/i,
  /huy/i,
  /xyi/i,
  /пизд/i,
  /pizd/i,
  /пезд/i,
  /еба[тьнл]/i,
  /еб[аёе]/i,
  /ёб[ануты]/i,
  /ebat/i,
  /ebal/i,
  /eblan/i,
  /бля[тд]/i,
  /blya/i,
  /blyad/i,
  /мудак/i,
  /мудил/i,
  /mudak/i,
  /сука/i,
  /сучк/i,
  /suka/i,
  /гандон/i,
  /gandon/i,
  /залуп/i,
  /zalup/i,
  /чмо/i,
  /fuck/i,
  /bitch/i,
  /cunt/i,
  /dick/i,
  /cock/i,
  /pussy/i,
  /nigger/i,
  /nigga/i,
  /whore/i,
  /slut/i
];

function containsForbiddenWord(str) {
  if (!str) return false;
  const raw = String(str).toLowerCase();
  for (const regex of FORBIDDEN_PATTERNS) {
    if (regex.test(raw)) return true;
  }
  const normalized = raw
    .replace(/[@4]/g, 'a')
    .replace(/[0]/g, 'o')
    .replace(/[1!|]/g, 'i')
    .replace(/[3]/g, 'e')
    .replace(/[$5]/g, 's')
    .replace(/[8]/g, 'b')
    .replace(/[\s\._\-\*~`+=,]/g, '');
  for (const regex of FORBIDDEN_PATTERNS) {
    if (regex.test(normalized)) return true;
  }
  const cyrToLat = normalized
    .replace(/а/g, 'a')
    .replace(/в/g, 'b')
    .replace(/е/g, 'e')
    .replace(/ё/g, 'e')
    .replace(/к/g, 'k')
    .replace(/м/g, 'm')
    .replace(/н/g, 'h')
    .replace(/о/g, 'o')
    .replace(/р/g, 'p')
    .replace(/с/g, 'c')
    .replace(/т/g, 't')
    .replace(/у/g, 'y')
    .replace(/х/g, 'x');
  for (const regex of FORBIDDEN_PATTERNS) {
    if (regex.test(cyrToLat)) return true;
  }
  return false;
}

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
    const { action, login, email, password_hash, name, company, phone, old_hash, new_hash, turnstile_token } = req.body || {};

    if (action === 'register' || action === 'login') {
      const clientIp = req.headers['x-forwarded-for'] || req.socket?.remoteAddress;
      const isHuman = await verifyCloudflareTurnstile(turnstile_token, clientIp);
      if (!isHuman) {
        return res.status(403).json({ error: 'Проверка Cloudflare Turnstile не пройдена.' });
      }
    }

    if (action === 'register') {
      if (!login || !password_hash || !name) {
        return res.status(400).json({ error: 'Заполните обязательные поля' });
      }

      if (login.trim().length < 5) {
        return res.status(400).json({ error: 'Логин должен содержать минимум 5 символов' });
      }

      if (containsForbiddenWord(login) || containsForbiddenWord(email) || containsForbiddenWord(name)) {
        return res.status(400).json({ error: 'Логин или имя содержит недопустимые слова' });
      }

      const emailVal = (email && email.includes('@')) ? email.trim() : (login.includes('@') ? login.trim() : `${login.trim()}@umbra.studio`);
      const cleanLogin = login.trim();
      const isUmbra = cleanLogin.toLowerCase() === 'umbra' || emailVal.toLowerCase().startsWith('umbra@');
      const userRole = isUmbra ? 'admin' : 'user';

      // Check existing
      const existing = await query(
        `SELECT id, login, email FROM studio_users WHERE login = '${cleanLogin.replace(/'/g, "''")}' OR email = '${emailVal.replace(/'/g, "''")}';`
      );
      if (existing.length > 0) {
        return res.status(400).json({ error: 'Пользователь с таким логином или email уже существует' });
      }

      const rows = await query(
        `INSERT INTO studio_users (login, email, password_hash, name, company, phone, role) 
         VALUES ('${cleanLogin.replace(/'/g, "''")}', '${emailVal.replace(/'/g, "''")}', '${password_hash.replace(/'/g, "''")}', '${name.trim().replace(/'/g, "''")}', '${(company || '').trim().replace(/'/g, "''")}', '${(phone || '').trim().replace(/'/g, "''")}', '${userRole}')
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

      if ((user.login && user.login.toLowerCase() === 'umbra') || (user.email && user.email.toLowerCase().startsWith('umbra@'))) {
        user.role = 'admin';
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
      if (name && containsForbiddenWord(name)) {
        return res.status(400).json({ error: 'Имя содержит недопустимые слова' });
      }
      if (company && containsForbiddenWord(company)) {
        return res.status(400).json({ error: 'Название компании содержит недопустимые слова' });
      }

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
