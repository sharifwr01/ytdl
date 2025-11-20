# ⚡ Quick Start Guide

5 মিনিটে YouTube Telegram Bot setup করুন!

## 📦 Prerequisites

শুধুমাত্র এই দুটি জিনিস দরকার:
- Docker & Docker Compose
- Telegram Bot Token

## 🚀 Installation (5 মিনিট)

### Step 1: Bot Token নিন (2 মিনিট)

1. Telegram এ [@BotFather](https://t.me/botfather) খুলুন
2. `/newbot` command পাঠান
3. Bot এর নাম দিন (e.g., "My YouTube Bot")
4. Username দিন (e.g., "my_youtube_bot")
5. Token copy করুন (দেখতে এরকম: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Bot Setup করুন (3 মিনিট)

```bash
# 1. Repository clone করুন
git clone https://github.com/yourusername/yt-telegram-bot.git
cd yt-telegram-bot

# 2. Environment file তৈরি করুন
cp .env.example .env

# 3. আপনার bot token দিন
nano .env  # অথবা যেকোনো text editor
# TELEGRAM_TOKEN=আপনার_বট_টোকেন_এখানে

# 4. Bot start করুন
docker-compose up -d

# 5. Logs দেখুন (optional)
docker-compose logs -f bot
```

### Step 3: Test করুন! ✅

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
/settings - ভাষা পরিবর্তন করুন
```

### Download করার পদ্ধতি

1. **Video Download:**
   ```
   পাঠান: https://youtube.com/watch?v=VIDEO_ID
   Format: Video চুজ করুন
   Quality: 720p অথবা আপনার পছন্দের quality
   ```

2. **Audio Download (MP3):**
   ```
   পাঠান: https://youtube.com/watch?v=VIDEO_ID
   Format: Audio চুজ করুন
   Quality: Best Quality
   ```

## ⚙️ Configuration

### Essential Settings (.env file)

```env
# Required - আপনার bot token
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Optional - Limits
RATE_LIMIT_PER_USER_PER_DAY=20  # প্রতিদিন 20টি download
MAX_FILE_MB=50                   # Maximum 50MB direct upload

# Optional - Admin
ADMIN_USER_IDS=123456789         # আপনার Telegram User ID
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