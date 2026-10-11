// Serverless PostgreSQL Connector for Neon (Direct HTTPS SQL API)
// Compatible with Vercel Serverless Functions with zero external binary dependencies.

const PRIMARY_URL = process.env.DATABASE_URL_HTTP || 'https://ep-cold-breeze-avl01r33-pooler.c-11.us-east-1.aws.neon.tech/sql';
const PRIMARY_CONN = process.env.DATABASE_URL || 'postgresql://neondb_owner:npg_DJ9xBOlZcmd8@ep-cold-breeze-avl01r33-pooler.c-11.us-east-1.aws.neon.tech/neondb?sslmode=require';

const BACKUP_URL = 'https://ep-rapid-tooth-b8gvxrrp-pooler.c-14.us-east-1.aws.neon.tech/sql';
const BACKUP_CONN = 'postgresql://neondb_owner:npg_Lp5TF9zwEJMc@ep-rapid-tooth-b8gvxrrp-pooler.c-14.us-east-1.aws.neon.tech/neondb?sslmode=require';

export async function query(sql, params = []) {
  try {
    return await executeSql(PRIMARY_URL, PRIMARY_CONN, sql, params);
  } catch (err) {
    console.warn('Primary DB failed, trying backup Neon instance:', err.message);
    return await executeSql(BACKUP_URL, BACKUP_CONN, sql, params);
  }
}

async function executeSql(endpoint, connString, sql, params) {
  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Neon-Connection-String': connString
    },
    body: JSON.stringify({ query: sql, params })
  });

  if (!resp.ok) {
    const errorBody = await resp.text();
    throw new Error(`Neon SQL error (${resp.status}): ${errorBody}`);
  }

  const result = await resp.json();
  return result.rows || [];
}
