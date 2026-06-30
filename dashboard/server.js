const express = require('express');
const { Pool } = require('pg');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 7860;

// Connect to Neon PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL_SYNC,
  ssl: { rejectUnauthorized: false }
});

app.use(express.static(path.join(__dirname, 'dist')));

app.get('/api/stats', async (req, res) => {
    try {
        const client = await pool.connect();
        const result = await client.query('SELECT jobs_applied, last_run FROM auto_apply_state ORDER BY id DESC LIMIT 1');
        client.release();
        
        if (result.rows.length > 0) {
            res.json(result.rows[0]);
        } else {
            res.json({ jobs_applied: 0, last_run: null });
        }
    } catch (err) {
        console.error("DB Error:", err);
        res.status(500).json({ error: "Failed to fetch stats" });
    }
});

// Serve React App
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`🚀 Hugging Face Dashboard Server running on port ${PORT}`);
});
