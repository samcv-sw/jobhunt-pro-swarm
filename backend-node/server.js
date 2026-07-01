const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Basic health check for cron ping
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'OK', timestamp: new Date() });
});

// Mock API endpoint for dashboard stats
app.get('/api/stats', (req, res) => {
    res.json({
        totalApplications: 154,
        interviews: 12,
        offers: 2,
        successRate: '7.8%'
    });
});

app.listen(PORT, () => {
    console.log(`Backend server running on port ${PORT}`);
});
