# Telegram Message Forwarding Bot

## Features
- Secure message forwarding from admins to authorized groups
- Dynamic group management (auto-add/remove groups)
- Webhook & Polling support
- Comprehensive logging (bot.log)
- Admin controls with config.json
- SSL/TLS support for webhooks

## Installation
1. Clone repository:
`git clone https://github.com/iatco13/tg_msg_bot.git`
`cd tg_msg_bot`

2. Create virtual environment:
`python3 -m venv .venv`
`source .venv/bin/activate`  # Linux/Mac
`.venv\Scripts\activate`     # Windows

3. Install dependencies:
`pip install -r requirements.txt`

## Configuration
1. Environment Setup:
`cp .env_template.txt .env`
`nano .env`

Example .env:
`TG_BOT_TOKEN=your_bot_token_here`
`TG_BOT_ID=your_bot_id`
`WEBHOOK_URL=https://yourdomain.com/webhook`
`CERT_PEM=certs/fullchain.pem`
`CERT_KEY=certs/privkey.key`
`TG_DELAY=30`

2. Admin/Chat Setup:
`cp config_template.json config.json`

Example config.json:
`{"admins": [{"id": "123456789", "name": "Admin"}], "chats": [{"name": "Group1", "id": "-100123456789", "authorized": true}]}`

## Usage
Start bot:
`./bot.sh start`

Stop bot:
`./bot.sh stop`

View logs:
`tail -f bot.log`

## Webhook Setup (Nginx example)
`server {`
`    listen 443 ssl;`
`    server_name yourdomain.com;`
`    ssl_certificate /path/to/certs/fullchain.pem;`
`    ssl_certificate_key /path/to/certs/privkey.key;`
`    location /webhook {`
`        proxy_pass http://localhost:8443;`
`        proxy_set_header Host $host;`
`        proxy_set_header X-Real-IP $remote_addr;`
`    }`
`}`

## Troubleshooting
- Webhook issues: Verify SSL certs and bot token
- Permission errors: `chmod 644 .env config.json`
- Check detailed logs in `bot.log`

## License
GNU GPLv3