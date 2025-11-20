# 🎬 YouTube Download Telegram Bot

একটি সম্পূর্ণ feature-rich Telegram bot যা YouTube থেকে video এবং audio download করতে পারে। Production-ready এবং scalable architecture সহ।

## ✨ Features

### Core Features
- ✅ **Video & Audio Download** - Multiple formats এবং qualities
- ✅ **Playlist Support** - পুরো playlist বা specific videos
- ✅ **Progress Tracking** - Real-time download progress
- ✅ **Multiple Languages** - English এবং বাংলা support
- ✅ **Rate Limiting** - Per-user daily limits
- ✅ **Cloud Storage** - বড় files এর জন্য Google Drive/S3 integration
- ✅ **Queue Management** - Concurrent downloads with queue
- ✅ **Admin Panel** - Admin-only commands

### Advanced Features
- 🎚️ Multiple quality options (1080p, 720p, 480p, 360p, best)
- 🎵 Audio extraction with MP3 conversion
- 📊 User statistics tracking
- 🔒 Rate limiting এবং abuse prevention
- ☁️ Automatic cloud upload for large files
- 📝 Detailed logging এবং error handling
- 🌍 Multi-language support (i18n)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker এবং Docker Compose (optional)
- Telegram Bot Token ([BotFather](https://t.me/botfather) থেকে নিন)
- Redis (caching এবং queue এর জন্য)
- PostgreSQL (optional, SQLite default)

### Installation

#### Method 1: Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/sharifwr01/ytdl.git
cd yt-telegram-bot
```

2. **Configure environment**
```bash
cp .env.example .env
nano .env  # আপনার configuration দিন
```

3. **Start the bot**
```bash
docker-compose up -d
```

4. **Check logs**
```bash
docker-compose logs -f bot
```

#### Method 2: Local Setup

1. **Clone এবং virtual environment তৈরি করুন**
```bash
git clone https://github.com/sharifwr01/ytdl.git
cd yt-telegram-bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Dependencies install করুন**
```bash
pip install -r requirements.txt
```

3. **FFmpeg install করুন**
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

4. **Redis start করুন**
```bash
# Docker দিয়ে
docker run -d -p 6379:6379 redis:7-alpine

# Or local installation
redis-server
```

5. **Environment configure করুন**
```bash
cp .env.example .env
# .env file edit করে আপনার values দিন
```

6. **Database initialize করুন**
```bash
python -c "import asyncio; from bot import init_db; asyncio.run(init_db())"
```

7. **Bot run করুন**
```bash
python bot.py
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_TOKEN` | Telegram bot token | - | ✅ |
| `DB_URL` | Database connection URL | sqlite+aiosqlite:///bot.db | ❌ |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379 | ✅ |
| `MAX_FILE_MB` | Max file size for direct upload | 50 | ❌ |
| `TELEGRAM_UPLOAD_LIMIT_MB` | Telegram's upload limit | 50 | ❌ |
| `MAX_CONCURRENT_DOWNLOADS` | Concurrent downloads limit | 3 | ❌ |
| `RATE_LIMIT_PER_USER_PER_DAY` | Daily download limit per user | 20 | ❌ |
| `ADMIN_USER_IDS` | Admin Telegram user IDs (comma-separated) | - | ❌ |
| `STORAGE_BACKEND` | Storage backend (local/gdrive/s3) | local | ❌ |

### Database Options

**SQLite (Default)**
```env
DB_URL=sqlite+aiosqlite:///bot.db
```

**PostgreSQL**
```env
DB_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

**MySQL**
```env
DB_URL=mysql+aiomysql://user:password@localhost:3306/dbname
```

### Cloud Storage Setup

#### Google Drive
1. Google Cloud Console এ project তৈরি করুন
2. Drive API enable করুন
3. OAuth 2.0 credentials তৈরি করুন
4. `.env` এ credentials যোগ করুন:
```env
STORAGE_BACKEND=gdrive
GDRIVE_CLIENT_ID=your_client_id
GDRIVE_CLIENT_SECRET=your_client_secret
```

#### AWS S3
```env
STORAGE_BACKEND=s3
S3_ENDPOINT=https://s3.amazonaws.com
S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

## 📱 Usage

### User Commands

| Command | Description |
|---------|-------------|
| `/start` | Bot start করুন এবং welcome message দেখুন |
| `/help` | সব commands এবং features দেখুন |
| `/status` | আপনার download statistics দেখুন |
| `/settings` | Language এবং preferences পরিবর্তন করুন |

### How to Download

1. Bot কে একটি YouTube URL পাঠান
2. Format select করুন (Video অথবা Audio)
3. Quality select করুন
4. Download complete হওয়ার জন্য অপেক্ষা করুন!

### Examples

**Video Download:**
```
https://youtube.com/watch?v=dQw4w9WgXcQ
→ Select Video → Select 720p → Download!
```

**Audio Download:**
```
https://youtube.com/watch?v=dQw4w9WgXcQ
→ Select Audio → Best Quality → Download as MP3!
```

**Playlist:**
```
https://youtube.com/playlist?list=PLxxxxxx
→ Select format → Downloads first 50 videos
```

## 🏗️ Architecture

```
┌─────────────┐
│   Telegram  │
│    Users    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Bot Server │
│  (aiogram)  │
└──────┬──────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌─────────────┐ ┌─────────────┐
│    Redis    │ │  PostgreSQL │
│   (Queue)   │ │  (Database) │
└─────────────┘ └─────────────┘
       │
       ▼
┌─────────────┐
│   yt-dlp    │
│  (Download) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   FFmpeg    │
│  (Convert)  │
└──────┬──────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Telegram │  │  Google  │  │   AWS    │
│  Upload  │  │  Drive   │  │    S3    │
└──────────┘  └──────────┘  └──────────┘
```

## 📊 Monitoring

### Logs
```bash
# Docker
docker-compose logs -f bot

# Local
tail -f bot.log
```

### Health Check
Bot এর health check করুন:
```bash
curl http://localhost:8000/health
```

### Metrics (Optional)
Prometheus metrics expose করুন:
```python
# Enable in bot.py
ENABLE_METRICS=true
```

## 🔒 Security

### Rate Limiting
- Per-user daily limits
- Global concurrent download limits
- IP-based rate limiting (optional)

### Input Validation
- YouTube URL validation
- Malicious input filtering
- File size checks

### Data Privacy
- User data encryption
- GDPR compliance
- Data retention policies

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test
pytest tests/test_download.py
```

### Test Coverage
```bash
coverage run -m pytest
coverage report
coverage html
```

## 🚢 Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Production Settings
1. Use PostgreSQL instead of SQLite
2. Enable Redis persistence
3. Set up proper logging
4. Configure backup strategy
5. Enable monitoring
6. Use webhook mode for better performance

### Webhook Mode
```bash
# Configure nginx
cp nginx.conf.example nginx.conf

# Start with webhook profile
docker-compose --profile webhook up -d
```

## 📈 Scaling

### Horizontal Scaling
```yaml
# docker-compose.yml
services:
  bot:
    deploy:
      replicas: 3
```

### Worker Scaling
```env
MAX_CONCURRENT_DOWNLOADS=10
```

### Database Optimization
- Use connection pooling
- Enable query caching
- Regular vacuum/optimize

## 🛠️ Troubleshooting

### Common Issues

**Bot not responding:**
```bash
# Check logs
docker-compose logs bot

# Restart bot
docker-compose restart bot
```

**Download fails:**
- Check FFmpeg installation
- Verify yt-dlp is updated
- Check disk space

**Database errors:**
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Debug Mode
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 📝 Contributing

Contributions welcome! এই steps follow করুন:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black .
isort .

# Lint
flake8 .
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## ⚠️ Legal Notice

এই bot শুধুমাত্র educational এবং personal use এর জন্য। YouTube এর Terms of Service মেনে চলুন:

- শুধুমাত্র আপনার নিজের বা permission আছে এমন content download করুন
- Copyright protected content download করবেন না
- Fair use guidelines follow করুন
- Local laws এবং regulations মেনে চলুন

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [FFmpeg](https://ffmpeg.org/) - Media processing

## 📞 Support

- Issues: [GitHub Issues](https://github.com/yourusername/yt-telegram-bot/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/yt-telegram-bot/discussions)
- Email: support@example.com

## 🗺️ Roadmap

- [ ] Video quality preview
- [ ] Batch download support
- [ ] Custom thumbnail upload
- [ ] Video trimming feature
- [ ] Subtitle download
- [ ] Multi-language audio tracks
- [ ] Mobile app integration
- [ ] Web interface

---

Made with ❤️ by [Your Name]

**Star ⭐ this repo if you find it useful!**
