import { Client } from 'pg';

export interface BotState {
    jobs_applied: number;
    last_run: string | null;
    session_cookies: any | null;
}

export async function getDbConnection(): Promise<Client | null> {
    const dbUrl = process.env.DATABASE_URL_SYNC || process.env.NEON_URL;
    if (!dbUrl) {
        console.warn("WARNING: No Database URL provided. Falling back to temporary in-memory state.");
        return null;
    }
    
    try {
        const client = new Client({ connectionString: dbUrl });
        await client.connect();
        
        await client.query(`
            CREATE TABLE IF NOT EXISTS auto_apply_state (
                id SERIAL PRIMARY KEY,
                jobs_applied INTEGER DEFAULT 0,
                last_run TIMESTAMP,
                session_cookies JSON
            )
        `);
        
        try {
            await client.query(`ALTER TABLE auto_apply_state ADD COLUMN session_cookies JSON`);
        } catch (e) {
            // Column likely already exists
        }
        
        const countRes = await client.query('SELECT COUNT(*) FROM auto_apply_state');
        if (parseInt(countRes.rows[0].count) === 0) {
            await client.query('INSERT INTO auto_apply_state (jobs_applied) VALUES (0)');
        }
        
        return client;
    } catch (error) {
        console.error(`Database Connection Error:`, error);
        return null;
    }
}

export async function loadState(client: Client | null): Promise<BotState> {
    if (!client) return { jobs_applied: 0, last_run: null, session_cookies: null };
    try {
        const res = await client.query('SELECT jobs_applied, last_run, session_cookies FROM auto_apply_state ORDER BY id DESC LIMIT 1');
        if (res.rows.length > 0) {
            return {
                jobs_applied: res.rows[0].jobs_applied,
                last_run: res.rows[0].last_run ? res.rows[0].last_run.toString() : null,
                session_cookies: res.rows[0].session_cookies
            };
        }
    } catch (e) {
        console.error("DB Load State Error:", e);
    }
    return { jobs_applied: 0, last_run: null, session_cookies: null };
}

export async function saveState(client: Client | null, appliedThisRun: number, updatedCookies: any | null = null) {
    if (!client) return;
    try {
        if (updatedCookies) {
            await client.query(
                'UPDATE auto_apply_state SET jobs_applied = jobs_applied + $1, last_run = NOW(), session_cookies = $2',
                [appliedThisRun, JSON.stringify(updatedCookies)]
            );
        } else {
            await client.query(
                'UPDATE auto_apply_state SET jobs_applied = jobs_applied + $1, last_run = NOW()',
                [appliedThisRun]
            );
        }
    } catch (e) {
        console.error("DB Save State Error:", e);
    }
}
