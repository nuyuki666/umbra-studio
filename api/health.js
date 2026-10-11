import { query } from './db.js';

export default async function handler(req, res) {
  try {
    const rows = await query('SELECT NOW() as current_time, count(*) as user_count FROM studio_users;');
    return res.status(200).json({
      status: 'online',
      database: 'PostgreSQL (Neon)',
      healthy: true,
      data: rows[0]
    });
  } catch (err) {
    return res.status(500).json({
      status: 'error',
      database: 'PostgreSQL (Neon)',
      healthy: false,
      error: err.message
    });
  }
}
