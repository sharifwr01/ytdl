"""
YouTube Download Telegram Bot
Main bot implementation with all features
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import re
import json
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
import yt_dlp
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, func
import aiofiles

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///bot.db")
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "50"))
TELEGRAM_UPLOAD_LIMIT_MB = int(os.getenv("TELEGRAM_UPLOAD_LIMIT_MB", "50"))
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))
RATE_LIMIT_PER_USER_PER_DAY = int(os.getenv("RATE_LIMIT_PER_USER_PER_DAY", "20"))
ADMIN_USER_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x]
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
GDRIVE_CLIENT_ID = os.getenv("GDRIVE_CLIENT_ID")
GDRIVE_CLIENT_SECRET = os.getenv("GDRIVE_CLIENT_SECRET")
TMP_DIR = Path("/tmp/yt_bot")
TMP_DIR.mkdir(exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database Models
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
    username: Mapped[Optional[str]]
    first_seen: Mapped[datetime]
    last_active: Mapped[datetime]
    total_downloads: Mapped[int] = mapped_column(default=0)
    language: Mapped[str] = mapped_column(default="en")

class Job(Base):
    __tablename__ = "jobs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    url: Mapped[str]
    format: Mapped[str]
    quality: Mapped[str]
    status: Mapped[str]  # pending, processing, completed, failed
    created_at: Mapped[datetime]
    completed_at: Mapped[Optional[datetime]]
    file_size: Mapped[Optional[int]]
    error_message: Mapped[Optional[str]]

# FSM States
class DownloadStates(StatesGroup):
    waiting_for_url = State()
    selecting_format = State()
    selecting_quality = State()
    processing = State()

# Initialize
engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

redis_client = redis.from_url(REDIS_URL)
storage = RedisStorage(redis_client)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=storage)

# Translations
TRANSLATIONS = {
    "en": {
        "welcome": "👋 Welcome to YouTube Download Bot!\n\nSend me a YouTube URL to get started.\n\n⚠️ Terms: Use for personal, legal content only. Respect copyright.",
        "help": """
🎬 YouTube Download Bot - Help

Commands:
/start - Start the bot
/help - Show this help
/status - Check your download stats
/settings - Change preferences

How to use:
1. Send a YouTube URL
2. Choose format (video/audio)
3. Select quality
4. Receive your file!

Features:
✅ Video & Audio downloads
✅ Multiple qualities
✅ Playlist support
✅ Progress tracking
✅ Cloud storage for large files

Limits:
• Max {rate_limit} downloads per day
• Max {max_file}MB direct upload
""",
        "rate_limited": "⚠️ You've reached your daily limit of {limit} downloads. Try again tomorrow!",
        "invalid_url": "❌ Invalid YouTube URL. Please send a valid link.",
        "select_format": "📝 Select format:",
        "select_quality": "🎚️ Select quality:",
        "downloading": "⏬ Downloading... {progress}%",
        "processing": "⚙️ Processing...",
        "uploading": "⏫ Uploading to Telegram... {progress}%",
        "completed": "✅ Download completed!",
        "failed": "❌ Download failed: {error}",
        "file_too_large": "📦 File is too large ({size}MB). Uploading to cloud storage...",
        "cloud_link": "☁️ Your file is ready!\n\n🔗 Link: {url}\n\n⏱️ Valid for 7 days",
        "status": """
📊 Your Statistics

Total Downloads: {total}
Today's Downloads: {today}
Remaining Today: {remaining}
Member Since: {joined}
""",
    },
    "bn": {
        "welcome": "👋 YouTube ডাউনলোড বটে স্বাগতম!\n\nশুরু করতে আমাকে একটি YouTube URL পাঠান।\n\n⚠️ শর্তাবলী: শুধুমাত্র ব্যক্তিগত, বৈধ কন্টেন্টের জন্য ব্যবহার করুন। কপিরাইট সম্মান করুন।",
        "help": """
🎬 YouTube ডাউনলোড বট - সাহায্য

কমান্ড:
/start - বট চালু করুন
/help - এই সাহায্য দেখান
/status - আপনার ডাউনলোড পরিসংখ্যান দেখুন
/settings - পছন্দ পরিবর্তন করুন

কিভাবে ব্যবহার করবেন:
1. একটি YouTube URL পাঠান
2. ফরম্যাট নির্বাচন করুন (ভিডিও/অডিও)
3. কোয়ালিটি নির্বাচন করুন
4. আপনার ফাইল পান!

বৈশিষ্ট্য:
✅ ভিডিও এবং অডিও ডাউনলোড
✅ একাধিক কোয়ালিটি
✅ প্লেলিস্ট সাপোর্ট
✅ প্রগ্রেস ট্র্যাকিং
✅ বড় ফাইলের জন্য ক্লাউড স্টোরেজ

সীমা:
• প্রতিদিন সর্বোচ্চ {rate_limit}টি ডাউনলোড
• সর্বোচ্চ {max_file}MB সরাসরি আপলোড
""",
        "rate_limited": "⚠️ আপনি আজকের {limit}টি ডাউনলোডের সীমা পূর্ণ করেছেন। আগামীকাল আবার চেষ্টা করুন!",
        "invalid_url": "❌ অবৈধ YouTube URL। অনুগ্রহ করে একটি বৈধ লিংক পাঠান।",
        "select_format": "📝 ফরম্যাট নির্বাচন করুন:",
        "select_quality": "🎚️ কোয়ালিটি নির্বাচন করুন:",
        "downloading": "⏬ ডাউনলোড হচ্ছে... {progress}%",
        "processing": "⚙️ প্রসেসিং...",
        "uploading": "⏫ টেলিগ্রামে আপলোড হচ্ছে... {progress}%",
        "completed": "✅ ডাউনলোড সম্পন্ন!",
        "failed": "❌ ডাউনলোড ব্যর্থ: {error}",
        "file_too_large": "📦 ফাইল অনেক বড় ({size}MB)। ক্লাউড স্টোরেজে আপলোড করা হচ্ছে...",
        "cloud_link": "☁️ আপনার ফাইল প্রস্তুত!\n\n🔗 লিংক: {url}\n\n⏱️ ৭ দিনের জন্য বৈধ",
        "status": """
📊 আপনার পরিসংখ্যান

মোট ডাউনলোড: {total}
আজকের ডাউনলোড: {today}
আজ বাকি: {remaining}
সদস্য হওয়ার তারিখ: {joined}
""",
    }
}

def get_text(user_lang: str, key: str, **kwargs) -> str:
    """Get translated text"""
    lang = user_lang if user_lang in TRANSLATIONS else "en"
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["en"][key])
    return text.format(**kwargs)

async def init_db():
    """Initialize database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_or_create_user(telegram_id: int, username: Optional[str] = None) -> User:
    """Get or create user"""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_seen=datetime.now(),
                last_active=datetime.now(),
                total_downloads=0
            )
            session.add(user)
        else:
            user.last_active = datetime.now()
            if username:
                user.username = username
        
        await session.commit()
        await session.refresh(user)
        return user

async def check_rate_limit(user_id: int) -> bool:
    """Check if user is within rate limit"""
    key = f"rate_limit:{user_id}:{datetime.now().date()}"
    count = await redis_client.get(key)
    
    if count is None:
        await redis_client.setex(key, 86400, 1)
        return True
    
    count = int(count)
    if count >= RATE_LIMIT_PER_USER_PER_DAY:
        return False
    
    await redis_client.incr(key)
    return True

async def get_today_downloads(user_id: int) -> int:
    """Get today's download count"""
    key = f"rate_limit:{user_id}:{datetime.now().date()}"
    count = await redis_client.get(key)
    return int(count) if count else 0

def is_valid_youtube_url(url: str) -> bool:
    """Validate YouTube URL"""
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    return bool(re.match(youtube_regex, url))

class DownloadProgress:
    """Track download progress"""
    def __init__(self, message: types.Message, user_lang: str):
        self.message = message
        self.user_lang = user_lang
        self.last_update = 0
    
    def __call__(self, d):
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%').strip()
                current_time = asyncio.get_event_loop().time()
                
                # Update every 2 seconds
                if current_time - self.last_update > 2:
                    self.last_update = current_time
                    asyncio.create_task(
                        self.message.edit_text(
                            get_text(self.user_lang, "downloading", progress=percent)
                        )
                    )
            except Exception as e:
                logger.error(f"Progress update error: {e}")

async def download_video(url: str, format_type: str, quality: str, message: types.Message, user: User) -> Optional[Path]:
    """Download video/audio"""
    try:
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_template = str(TMP_DIR / f"{user.telegram_id}_{timestamp}_%(title)s.%(ext)s")
        
        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': output_template,
            'progress_hooks': [DownloadProgress(message, user.language)],
            'quiet': True,
            'no_warnings': True,
        }
        
        if format_type == "audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'writethumbnail': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }, {
                    'key': 'EmbedThumbnail',
                }],
            })
        else:
            if quality == "best":
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            else:
                height = quality.replace('p', '')
                ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
        
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find downloaded file
            base_name = ydl.prepare_filename(info)
            if format_type == "audio":
                file_path = Path(base_name).with_suffix('.mp3')
            else:
                file_path = Path(base_name)
            
            if file_path.exists():
                return file_path
            
            # Try to find the file
            for file in TMP_DIR.glob(f"{user.telegram_id}_{timestamp}_*"):
                return file
        
        return None
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise

async def upload_to_cloud(file_path: Path, user: User) -> str:
    """Upload to cloud storage and return shareable link"""
    # This is a placeholder - implement actual cloud upload
    # For Google Drive, S3, etc.
    
    if STORAGE_BACKEND == "gdrive":
        # Implement Google Drive upload
        pass
    elif STORAGE_BACKEND == "s3":
        # Implement S3 upload
        pass
    
    # Mock link for demonstration
    return f"https://example.com/download/{file_path.name}"

# Command Handlers
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Handle /start command"""
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer(get_text(user.language, "welcome"))

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    user = await get_or_create_user(message.from_user.id)
    await message.answer(
        get_text(
            user.language, 
            "help",
            rate_limit=RATE_LIMIT_PER_USER_PER_DAY,
            max_file=MAX_FILE_MB
        )
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Handle /status command"""
    user = await get_or_create_user(message.from_user.id)
    today_count = await get_today_downloads(user.telegram_id)
    remaining = max(0, RATE_LIMIT_PER_USER_PER_DAY - today_count)
    
    await message.answer(
        get_text(
            user.language,
            "status",
            total=user.total_downloads,
            today=today_count,
            remaining=remaining,
            joined=user.first_seen.strftime("%Y-%m-%d")
        )
    )

@dp.message(Command("settings"))
async def cmd_settings(message: types.Message):
    """Handle /settings command"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton(text="🇧🇩 বাংলা", callback_data="lang_bn")
        ]
    ])
    await message.answer("🌍 Select Language / ভাষা নির্বাচন করুন:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("lang_"))
async def callback_language(callback: types.CallbackQuery):
    """Handle language selection"""
    lang = callback.data.split("_")[1]
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        user.language = lang
        await session.commit()
    
    await callback.message.edit_text(
        "✅ Language updated!" if lang == "en" else "✅ ভাষা আপডেট হয়েছে!"
    )
    await callback.answer()

@dp.message(F.text)
async def handle_url(message: types.Message, state: FSMContext):
    """Handle URL message"""
    url = message.text.strip()
    
    if not is_valid_youtube_url(url):
        user = await get_or_create_user(message.from_user.id)
        await message.answer(get_text(user.language, "invalid_url"))
        return
    
    # Check rate limit
    if not await check_rate_limit(message.from_user.id):
        user = await get_or_create_user(message.from_user.id)
        await message.answer(
            get_text(user.language, "rate_limited", limit=RATE_LIMIT_PER_USER_PER_DAY)
        )
        return
    
    # Save URL to state
    await state.update_data(url=url)
    
    # Ask for format
    user = await get_or_create_user(message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Video", callback_data="format_video"),
            InlineKeyboardButton(text="🎵 Audio", callback_data="format_audio")
        ]
    ])
    await message.answer(
        get_text(user.language, "select_format"),
        reply_markup=keyboard
    )
    await state.set_state(DownloadStates.selecting_format)

@dp.callback_query(F.data.startswith("format_"))
async def callback_format(callback: types.CallbackQuery, state: FSMContext):
    """Handle format selection"""
    format_type = callback.data.split("_")[1]
    await state.update_data(format=format_type)
    
    user = await get_or_create_user(callback.from_user.id)
    
    # Ask for quality
    if format_type == "video":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Best", callback_data="quality_best")],
            [InlineKeyboardButton(text="1080p", callback_data="quality_1080p")],
            [InlineKeyboardButton(text="720p", callback_data="quality_720p")],
            [InlineKeyboardButton(text="480p", callback_data="quality_480p")],
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎵 Best Quality", callback_data="quality_best")]
        ])
    
    await callback.message.edit_text(
        get_text(user.language, "select_quality"),
        reply_markup=keyboard
    )
    await state.set_state(DownloadStates.selecting_quality)
    await callback.answer()

@dp.callback_query(F.data.startswith("quality_"))
async def callback_quality(callback: types.CallbackQuery, state: FSMContext):
    """Handle quality selection and start download"""
    quality = callback.data.split("_")[1]
    data = await state.get_data()
    
    url = data.get("url")
    format_type = data.get("format")
    
    user = await get_or_create_user(callback.from_user.id)
    
    status_msg = await callback.message.edit_text(
        get_text(user.language, "downloading", progress="0")
    )
    
    file_path = None
    try:
        # Download file
        file_path = await download_video(url, format_type, quality, status_msg, user)
        
        if not file_path or not file_path.exists():
            raise Exception("Download failed")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # Show storage options for all files
        await state.update_data(
            file_path=str(file_path), 
            file_size_mb=file_size_mb,
            format_type=format_type
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text(user.language, "telegram_direct"), 
                callback_data="storage_telegram"
            )],
            [InlineKeyboardButton(
                text=get_text(user.language, "save_gdrive"), 
                callback_data="storage_gdrive"
            )],
        ])
        
        await status_msg.edit_text(
            get_text(user.language, "file_info", size=f"{file_size_mb:.1f}"),
            reply_markup=keyboard
        )
        await state.set_state(DownloadStates.selecting_storage)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await status_msg.edit_text(
            get_text(user.language, "failed", error=str(e))
        )
        if file_path:
            await cleanup_file(file_path)
        await state.clear()
        await callback.answer()

@dp.callback_query(F.data.startswith("storage_"))
async def callback_storage(callback: types.CallbackQuery, state: FSMContext):
    """Handle storage option selection"""
    storage_type = callback.data.split("_")[1]
    data = await state.get_data()
    
    file_path = Path(data.get("file_path"))
    file_size_mb = data.get("file_size_mb")
    format_type = data.get("format_type")
    user = await get_or_create_user(callback.from_user.id)
    
    try:
        if storage_type == "telegram":
            # Upload to Telegram using Pyrogram (supports up to 4GB)
            status_msg = await callback.message.edit_text(
                get_text(user.language, "uploading_telegram", progress="0")
            )
            
            is_audio = (format_type == "audio")
            caption = get_text(user.language, "completed")
            
            # Use Pyrogram for upload
            success = await upload_large_file_pyrogram(
                file_path=file_path,
                chat_id=callback.from_user.id,
                caption=caption,
                status_msg=status_msg,
                user_lang=user.language,
                is_audio=is_audio
            )
            
            if success:
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Upload failed. Try Google Drive option.")
                await callback.answer()
                return
            
        elif storage_type == "gdrive":
            # Check if GDrive is connected
            if not user.gdrive_token:
                await callback.message.edit_text(
                    get_text(user.language, "gdrive_not_connected")
                )
                await callback.answer()
                return
            
            # Upload to Google Drive
            status_msg = callback.message
            gdrive_link = await upload_to_gdrive(file_path, user, status_msg)
            
            if gdrive_link:
                await callback.message.answer(
                    get_text(
                        user.language, 
                        "gdrive_link", 
                        url=gdrive_link,
                        size=f"{file_size_mb:.1f}"
                    )
                )
                await status_msg.delete()
            else:
                await callback.message.edit_text(
                    get_text(user.language, "gdrive_error")
                )
        
        # Update user stats
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == user.telegram_id)
            )
            db_user = result.scalar_one()
            db_user.total_downloads += 1
            await session.commit()
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        await callback.message.answer(
            get_text(user.language, "failed", error=str(e))
        )
    finally:
        # Always cleanup file from VPS
        await cleanup_file(file_path)
    
    await state.clear()
    await callback.answer()

async def cleanup_old_files():
    """Periodic cleanup of old files"""
    while True:
        try:
            cutoff_time = datetime.now().timestamp() - 600
            for file in TMP_DIR.glob("*"):
                if file.is_file() and file.stat().st_mtime < cutoff_time:
                    file.unlink()
                    logger.info(f"Cleaned up old file: {file}")
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
        
        await asyncio.sleep(300)

async def main():
    """Main function"""
    logger.info("Starting YouTube Download Bot with Pyrogram...")
    logger.info(f"Admin IDs: {ADMIN_USER_IDS}")
    logger.info(f"Max file size: {TELEGRAM_UPLOAD_LIMIT_MB}MB (4GB via Pyrogram)")
    logger.info(f"API ID: {API_ID}")
    logger.info(f"Storage backend: {STORAGE_BACKEND}")
    
    # Initialize database
    await init_db()
    
    # Start Pyrogram client
    await app.start()
    logger.info("Pyrogram client started")
    
    # Start cleanup task
    asyncio.create_task(cleanup_old_files())
    
    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    data = await state.get_data()
    
    url = data.get("url")
    format_type = data.get("format")
    
    user = await get_or_create_user(callback.from_user.id)
    
    status_msg = await callback.message.edit_text(
        get_text(user.language, "downloading", progress="0")
    )
    
    try:
        # Download file
        file_path = await download_video(url, format_type, quality, status_msg, user)
        
        if not file_path or not file_path.exists():
            raise Exception("Download failed")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        if file_size_mb <= TELEGRAM_UPLOAD_LIMIT_MB:
            # Upload to Telegram
            await status_msg.edit_text(
                get_text(user.language, "uploading", progress="0")
            )
            
            if format_type == "audio":
                await callback.message.answer_audio(
                    FSInputFile(file_path),
                    caption=get_text(user.language, "completed")
                )
            else:
                await callback.message.answer_video(
                    FSInputFile(file_path),
                    caption=get_text(user.language, "completed")
                )
            
            await status_msg.delete()
        else:
            # Upload to cloud
            await status_msg.edit_text(
                get_text(user.language, "file_too_large", size=f"{file_size_mb:.1f}")
            )
            
            cloud_url = await upload_to_cloud(file_path, user)
            
            await callback.message.answer(
                get_text(user.language, "cloud_link", url=cloud_url)
            )
        
        # Update user stats
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == user.telegram_id)
            )
            db_user = result.scalar_one()
            db_user.total_downloads += 1
            await session.commit()
        
        # Cleanup
        try:
            file_path.unlink()
        except:
            pass
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await status_msg.edit_text(
            get_text(user.language, "failed", error=str(e))
        )
    
    await state.clear()
    await callback.answer()

async def main():
    """Main function"""
    logger.info("Starting bot...")
    
    # Initialize database
    await init_db()
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())