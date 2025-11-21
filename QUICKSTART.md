# ⚡ Quick Start Guide

10 মিনিটে YouTube Telegram Bot setup করুন - **4K support + 4GB upload + Google Drive!**

## 📦 Prerequisites

- Docker & Docker Compose
- Telegram Bot Token
- **Telegram API_ID & API_HASH** (4GB upload এর জন্য required)
- Google Drive API Credentials (optional, for cloud storage)

## 🚀 Installation (10 মিনিট)

### Step 1: Bot Token নিন (2 মিনিট)

1. Telegram এ [@BotFather](https://t.me/botfather) খুলুন
2. `/newbot` command পাঠান
3. Bot এর নাম দিন (e.g., "My YouTube Bot")
4. Username দিন (e.g., "my_youtube_bot")
5. Token copy করুন (দেখতে এরকম: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: API Credentials নিন (3 মিনিট) - **REQUIRED for 4GB upload**

1. **https://my.telegram.org** এ যান
2. Phone number দিয়ে login করুন
3. "API Development Tools" click করুন
4. Form fill করুন:
   - App title: `YouTube Bot`
   - Short name: `yt_bot`
5. "Create Application" click করুন
6. **Copy করুন:**
   - `api_id`: একটি number (e.g., `12345678`)
   - `api_hash`: একটি string (e.g., `0123456789abcdef...`)

**বিস্তারিত guide:** [API_SETUP.md](API_SETUP.md)

### Step 3: Bot Setup করুন (5 মিনিট)

```bash
# 1. Repository clone করুন
git clone https://github.com/yourusername/yt-telegram-bot.git
cd yt-telegram-bot

# 2. Environment file তৈরি করুন
cp .env.example .env

# 3. আপনার credentials দিন
nano .env  # অথবা যেকোনো text editor
# এই values গুলো যোগ করুন:
# TELEGRAM_TOKEN=আপনার_বট_টোকেন
# API_ID=আপনার_api_id
# API_HASH=আপনার_api_hash

# 4. Bot start করুন
docker-compose up -d

# 5. Logs দেখুন (optional)
docker-compose logs -f bot
```

### Step 3: (Optional) Google Drive Setup

বড় files এর জন্য Google Drive connect করুন:

1. [GDRIVE_SETUP.md](GDRIVE_SETUP.md) guide follow করুন
2. Google Cloud Console এ credentials তৈরি করুন
3. `.env` file এ credentials যোগ করুন:
```env
GDRIVE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=your_client_secret
```
4. Bot restart করুন: `docker-compose restart`
5. Telegram এ `/gdrive` command দিয়ে connect করুন

### Step 4: Test করুন! ✅

1. Telegram এ আপনার bot খুলুন
2. `/start` command দিন
3. একটি YouTube link পাঠান: `https://youtube.com/watch?v=dQw4w9WgXcQ`
4. Format এবং quality select করুন
5. Download শুরু হবে! 🎉

## 🎯 Basic Usage

### Commands

```
/start    - Bot চালু করুন
/help     - সাহায্য দেখুন
/status   - আপনার stats দেখুন
/gdrive   - Google Drive সংযুক্ত করুন
/admin    - Admin panel (শুধু admin)
```

### Download করার পদ্ধতি

1. **4K Video Download:**
   ```
   পাঠান: https://youtube.com/watch?v=VIDEO_ID
   Format: Video চুজ করুন
   Quality: 4K (2160p) অথবা Best
   ```

2. **High Quality Audio (320kbps MP3):**
   ```
   পাঠান: https://youtube.com/watch?v=VIDEO_ID
   Format: Audio চুজ করুন
   Quality: Best Quality
   ```

3. **বড় Files (50MB+):**
   ```
   Download complete হলে দুটি option:
   📱 Telegram এ পাঠান (2GB পর্যন্ত)
   ☁️ Google Drive এ সেভ করুন
   ```

## ⚙️ Configuration

### Essential Settings (.env file)

```env
# Required - আপনার bot token
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Required - API credentials (4GB upload এর জন্য)
API_ID=12345678
API_HASH=0123456789abcdef0123456789abcdef

# Limits (4GB Telegram Upload Enabled via Pyrogram!)
RATE_LIMIT_PER_USER_PER_DAY=50   # প্রতিদিন 50টি download
MAX_FILE_MB=4000                  # 4GB পর্যন্ত
TELEGRAM_UPLOAD_LIMIT_MB=4000    # 4GB direct upload

# Admin
ADMIN_USER_IDS=123456789          # আপনার Telegram User ID

# Google Drive (Optional but recommended)
GDRIVE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=your_client_secret
STORAGE_BACKEND=gdrive

# Performance (Maximum Speed!)
MAX_CONCURRENT_DOWNLOADS=5
YT_DLP_CONCURRENT_FRAGMENTS=10
```

### আপনার Telegram User ID কিভাবে খুঁজবেন?

1. [@userinfobot](https://t.me/userinfobot) খুলুন
2. `/start` দিন
3. আপনার ID দেখুন (e.g., `123456789`)

## 🐛 Troubleshooting

### Bot respond করছে না?

```bash
# Logs check করুন
docker-compose logs bot

# Bot restart করুন
docker-compose restart bot
```

### Download fail হচ্ছে?

```bash
# FFmpeg check করুন
docker-compose exec bot ffmpeg -version

# Services restart করুন
docker-compose restart
```

### Database error?

```bash
# Database reset করুন
docker-compose down -v
docker-compose up -d
```

## 📊 Check Status

```bash
# All services status
docker-compose ps

# Bot logs
docker-compose logs -f bot

# Resource usage
docker stats
```

## 🛑 Stop Bot

```bash
# Stop করুন
docker-compose down

# Stop + data মুছে ফেলুন
docker-compose down -v
```

## 🔄 Update Bot

```bash
# Latest code pull করুন
git pull origin main

# Rebuild এবং restart
docker-compose build --no-cache
docker-compose up -d
```

## 🎨 Customize

### Change Language

Bot এ `/settings` command দিয়ে ভাষা পরিবর্তন করুন।

### Change Limits

`.env` file edit করুন:
```env
RATE_LIMIT_PER_USER_PER_DAY=50  # আরো downloads
MAX_FILE_MB=100                 # বড় files
```

Restart করুন:
```bash
docker-compose restart
```

## 📱 Mobile Setup (Termux)

Android device এ run করতে চান?

```bash
# Termux install করুন
pkg update && pkg upgrade
pkg install python git

# Repository clone করুন
git clone https://github.com/yourusername/yt-telegram-bot.git
cd yt-telegram-bot

# Dependencies install করুন
pip install -r requirements.txt

# Bot run করুন
python bot.py
```

## 🌐 Public Bot Deploy

### Heroku (Free)

```bash
# Heroku CLI install করুন
# https://devcenter.heroku.com/articles/heroku-cli

# Login করুন
heroku login

# Create app
heroku create your-bot-name

# Set config
heroku config:set TELEGRAM_TOKEN=your_token

# Deploy
git push heroku main
```

### Railway (Free)

1. [Railway](https://railway.app) এ যান
2. GitHub connect করুন
3. Repository select করুন
4. Environment variables set করুন
5. Deploy! 🚀

## 💡 Tips

1. **Performance:**
   - SSD storage ব্যবহার করুন
   - Minimum 2GB RAM recommended
   - Stable internet connection

2. **Security:**
   - `.env` file কখনো commit করবেন না
   - Strong admin password ব্যবহার করুন
   - Regular updates করুন

3. **Optimization:**
   - Redis persistence enable করুন
   - PostgreSQL ব্যবহার করুন (SQLite এর বদলে)
   - Cloud storage setup করুন বড় files এর জন্য

## 📚 Next Steps

- [Full Documentation](README.md) পড়ুন
- [Deployment Guide](DEPLOYMENT.md) দেখুন
- [API Documentation](API.md) explore করুন
- [Contributing Guide](CONTRIBUTING.md) পড়ুন

## 🆘 Need Help?

- **Issues:** [GitHub Issues](https://github.com/yourusername/yt-telegram-bot/issues)
- **Email:** support@example.com
- **Discord:** [Join our server](https://discord.gg/example)

---

**🎉 Congratulations! Your bot is ready!**

এখন Telegram এ গিয়ে আপনার bot ব্যবহার শুরু করুন!