# Production deployment guide

## Option 1: Docker Compose (Recommended)

### Setup
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Update deployment
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## Option 2: Systemd Services (Linux)

### Setup
```bash
# Create user for bot
sudo useradd -r -s /bin/false telegram-bot

# Copy files to deployment directory
sudo mkdir -p /opt/telegram-bot
sudo cp -r . /opt/telegram-bot/
sudo chown -R telegram-bot:telegram-bot /opt/telegram-bot

# Create virtual environment
cd /opt/telegram-bot
sudo -u telegram-bot python3 -m venv venv
sudo -u telegram-bot venv/bin/pip install -r requirements.txt

# Initialize database
sudo -u telegram-bot venv/bin/python init_db.py

# Copy systemd service files
sudo cp telegram-bot.service /etc/systemd/system/
sudo cp miniapp-web.service /etc/systemd/system/

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot miniapp-web
sudo systemctl start telegram-bot miniapp-web

# Check status
sudo systemctl status telegram-bot
sudo systemctl status miniapp-web
```

### View logs
```bash
sudo journalctl -u telegram-bot -f
sudo journalctl -u miniapp-web -f
```

### Update deployment
```bash
cd /opt/telegram-bot
sudo -u telegram-bot git pull
sudo -u telegram-bot venv/bin/pip install -r requirements.txt
sudo systemctl restart telegram-bot miniapp-web
```

## Option 3: Manual (Development/Testing)

```bash
# Terminal 1: Bot
python main.py

# Terminal 2: Web Server
python web_server.py
```

## Nginx Configuration for Mini App

Create `/etc/nginx/sites-available/miniapp`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable SSL with Let's Encrypt:
```bash
sudo ln -s /etc/nginx/sites-available/miniapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```

## Environment Variables

Required in `.env`:
```env
BOT_TOKEN=your_bot_token
DATABASE_URL=sqlite+aiosqlite:///./bot.db
FORUM_GROUP_ID=your_forum_group_id
MINI_APP_URL=https://your-domain.com/miniapp
```

## Database Backup

```bash
# Backup
cp bot.db bot.db.backup.$(date +%Y%m%d_%H%M%S)

# Restore
cp bot.db.backup.YYYYMMDD_HHMMSS bot.db
```

## Monitoring

Check bot is responding:
```bash
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe"
```

Check web server:
```bash
curl http://localhost:8080/api/shop
```

## Troubleshooting

**Bot not starting:**
- Check BOT_TOKEN in .env
- Check logs: `journalctl -u telegram-bot -n 50`
- Verify database file permissions

**Mini App not loading:**
- Verify MINI_APP_URL is HTTPS
- Check web server is running on port 8080
- Verify Nginx proxy is configured correctly
- Check browser console for errors

**Database locked errors:**
- Ensure only one bot instance is running
- Check file permissions on bot.db
- Consider switching to PostgreSQL for production
