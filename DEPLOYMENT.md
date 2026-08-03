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

If the release contains database migrations, apply them before starting:
```bash
docker-compose run --rm bot alembic upgrade head
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

# Initialize database and mark the current schema version
sudo -u telegram-bot venv/bin/python init_db.py
sudo -u telegram-bot venv/bin/alembic stamp head

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
sudo systemctl stop telegram-bot miniapp-web
sudo -u telegram-bot cp bot.db bot.db.backup.$(date +%Y%m%d_%H%M%S)
sudo -u telegram-bot git pull
sudo -u telegram-bot venv/bin/pip install -r requirements.txt
sudo -u telegram-bot venv/bin/alembic upgrade head
sudo systemctl start telegram-bot miniapp-web
```

Always stop the services and back up the database before applying migrations.
See `MIGRATIONS.md` for details.

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

Optional (defaults shown):
```env
QUEUE_WAIT_MINUTES=5
BROADCAST_TIMEOUT_MINUTES=10
BROADCAST_DELAY_MS=50
WEB_HOST=0.0.0.0
WEB_PORT=8080
```

## Database Backup

Stop the services first, or use the SQLite backup command on a live database:

```bash
# Safe backup while the bot is running
sqlite3 bot.db ".backup 'bot.db.backup.$(date +%Y%m%d_%H%M%S)'"

# Backup with services stopped
cp bot.db bot.db.backup.$(date +%Y%m%d_%H%M%S)

# Restore (services must be stopped)
cp bot.db.backup.YYYYMMDD_HHMMSS bot.db
```

A plain `cp` of a database that is being written to can produce a corrupted copy.

## Monitoring

Check bot is responding:
```bash
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe"
```

Check web server is up. All `/api/` routes require a signed
`X-Telegram-Init-Data` header, so an unauthenticated request is expected to
return `401` — that response still proves the server is alive:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/api/shop
# expected: 401
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

**Mini App shows an authorization error:**
- The app must be opened from inside Telegram, not in a normal browser
- `initData` older than 24 hours is rejected — reopen the app
- Bot and web server must use the same BOT_TOKEN

**Broadcast stuck in SENDING:**
- The process died mid-broadcast
- Inspect the `broadcasts` table and reset the status manually before resending

**Database locked errors:**
- Ensure only one bot instance is running
- Check file permissions on bot.db
- Consider switching to PostgreSQL for production
