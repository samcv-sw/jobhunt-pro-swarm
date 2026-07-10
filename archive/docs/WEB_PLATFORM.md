# JobHunt Pro - SaaS Platform

## Overview
A complete SaaS platform for automated job applications. Users can:
1. Register and upload their CV
2. Create campaigns to apply to companies
3. Pay with crypto (BTC, ETH, USDT, LTC) or redeem codes
4. Track email opens and responses in real-time

## Features
- **User Registration** - Email/password authentication
- **CV Profiles** - Save and manage multiple CV versions
- **Campaigns** - Launch targeted job application campaigns
- **Payment System** - Crypto payments + redeem codes
- **Wallet** - Pre-paid balance system
- **API Access** - RESTful API for automation
- **Analytics** - Track opens, clicks, responses

## Pricing Tiers
| Tier | Companies | Price |
|------|-----------|-------|
| Starter | 100 | $5 |
| Basic | 200 | $10 |
| Pro | 500 | $20 |
| Enterprise | 1000 | $35 |
| Unlimited | 5000 | $100 |

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
copy .env.example .env
# Edit .env with your settings
```

### 3. Run the Server
```bash
cd web
python app.py
```

### 4. Access the Platform
- Website: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## API Usage

### Create Campaign
```bash
curl -X POST http://localhost:8000/api/v1/campaign \
  -F "api_key=your_api_key" \
  -F "profile_cv=Your CV text..." \
  -F "company_count=200" \
  -F "target_titles=Network Engineer" \
  -F "target_locations=Dubai"
```

### Check Campaign Status
```bash
curl "http://localhost:8000/api/v1/campaign/camp_xxx?api_key=your_api_key"
```

## Payment Integration

### Crypto Addresses (configure in app.py)
- BTC: bc1q...
- ETH: 0x...
- USDT: 0x...
- LTC: ltc1...

### Redeem Codes
Generate redeem codes via database:
```sql
INSERT INTO redeem_codes (code, value_usd) VALUES ('REDEEM-ABC123', 10);
```

## Deployment

### Option 1: Local Server
```bash
python web/app.py
```

### Option 2: Cloud (Render/Railway)
1. Push to GitHub
2. Connect to Render/Railway
3. Set environment variables
4. Deploy

### Option 3: VPS
```bash
# Install nginx
sudo apt install nginx

# Configure reverse proxy
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Run with systemd
sudo systemctl enable jobhunt
sudo systemctl start jobhunt
```

## Files Structure
```
cv sam new ma3 kimi/
├── web/
│   ├── app.py              # FastAPI backend
│   └── templates/          # HTML templates
│       ├── index.html      # Landing page
│       ├── pricing.html    # Pricing page
│       ├── register.html   # Registration
│       ├── login.html      # Login
│       ├── dashboard.html  # User dashboard
│       ├── upload_cv.html  # CV upload
│       ├── new_campaign.html # Create campaign
│       ├── campaign_detail.html # Campaign details
│       ├── wallet.html     # Wallet & payments
│       └── api_docs.html   # API documentation
├── core/                   # Backend modules
├── config.py               # Configuration
├── requirements.txt        # Dependencies
└── .env.example            # Environment template
```

## Scaling to 1M+ Jobs/Day

To handle massive scale:
1. **Database**: Upgrade from SQLite to PostgreSQL
2. **Queue**: Add Redis/Celery for task queue
3. **Workers**: Deploy multiple worker instances
4. **Email**: Add more providers (100+ accounts)
5. **Search**: Add more search engines + APIs

## Support
For issues, check logs in `jobhunt_saas.log`
