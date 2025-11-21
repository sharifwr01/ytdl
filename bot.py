"""
YouTube Download Telegram Bot - Enhanced Version with Client API
Features: 4K support, 2GB+ upload via Pyrogram, GDrive integration, No VPS storage
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import re
import json
from pathlib import Path
import shutil
import tempfile

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage

# Pyrogram for large file uploads (2GB+)
from pyrogram import Client as PyrogramClient
from pyrogram.types import Message as PyrogramMessage

import yt_dlp
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, func
import aiofiles

# Google Drive imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_ID = int(os.getenv("API_ID"))  # Get from my.telegram.org
API_HASH = os.getenv("API_HASH")   # Get from my.telegram.org
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///bot.db")
MAX_FILE_MB = 4000  # 4GB with Pyrogram (Telegram supports up to 4GB)
TELEGRAM_UPLOAD_LIMIT_MB = 4000  # 4GB via Client API
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5"))
RATE_LIMIT_PER_USER_PER_DAY = int(os.getenv("RATE_LIMIT_PER_USER_PER_DAY", "50"))
ADMIN_USER_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x]
STORAGE_BACKEND = "gdrive"
GDRIVE_CLIENT_ID = os.getenv("GDRIVE_CLIENT_ID")
GDRIVE_CLIENT_SECRET = os.getenv("GDRIVE_CLIENT_SECRET")
GDRIVE_FOLDER_NAME = "YTDL"

# Use temp directory that auto-cleans
TMP_DIR = Path(tempfile.gettempdir()) / "yt_bot"
TMP_DIR.mkdir(exist_ok=True)

# Google Drive Scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

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
    language: Mapped[str] = mapped_column(default="bn")
    gdrive_token: Mapped[Optional[str]]
    is_admin: Mapped[bool] = mapped_column(default=False)

class Job(Base):
    __tablename__ = "jobs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    url: Mapped[str]
    format: Mapped[str]
    quality: Mapped[str]
    status: Mapped[str]
    created_at: Mapped[datetime]
    completed_at: Mapped[Optional[datetime]]
    file_size: Mapped[Optional[int]]
    error_message: Mapped[Optional[str]]
    gdrive_link: Mapped[Optional[str]]

# FSM States
class DownloadStates(StatesGroup):
    waiting_for_url = State()
    selecting_format = State()
    selecting_quality = State()
    selecting_storage = State()
    processing = State()

class GDriveAuthStates(StatesGroup):
    waiting_for_code = State()

# Initialize
engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

redis_client = redis.from_url(REDIS_URL)
storage = RedisStorage(redis_client)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=storage)

# Initialize Pyrogram Client for large uploads
app = PyrogramClient(
    "yt_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=TELEGRAM_TOKEN
)

# Translations (Bangla focused)
TRANSLATIONS = {
    "bn": {
        "welcome": "👋 YouTube ডাউনলোড বটে স্বাগতম!\n\n✨ Features:\n• 4K Quality পর্যন্ত\n• 4GB পর্যন্ত ফাইল (Telegram Client API)\n• Google Drive সাপোর্ট\n• সর্বোচ্চ গতি\n\nএকটি YouTube URL পাঠান।",
        "help": """
🎬 YouTube ডাউনলোড বট

📝 কমান্ড:
/start - বট চালু করুন
/help - সাহায্য
/status - পরিসংখ্যান
/gdrive - Google Drive সংযুক্ত করুন
/admin - Admin panel (শুধু admin)

🎯 কিভাবে ব্যবহার করবেন:
1. YouTube URL পাঠান
2. Format চুজ করুন
3. Quality নির্বাচন করুন
4. Download!

✨ বৈশিষ্ট্য:
✅ 4K Quality (2160p)
✅ 4GB পর্যন্ত upload (Client API)
✅ Google Drive backup
✅ Fast download
✅ সর্বোচ্চ গতি
""",
        "rate_limited": "⚠️ দৈনিক {limit}টি ডাউনলোডের সীমা পূর্ণ!",
        "invalid_url": "❌ অবৈধ YouTube URL!",
        "select_format": "📝 Format নির্বাচন করুন:",
        "select_quality": "🎚️ Quality নির্বাচন করুন:",
        "select_storage": "💾 Storage অপশন:",
        "downloading": "⏬ ডাউনলোড হচ্ছে... {progress}%",
        "processing": "⚙️ প্রসেসিং...",
        "uploading": "⏫ আপলোড হচ্ছে... {progress}%",
        "uploading_telegram": "📱 Telegram এ আপলোড হচ্ছে... {progress}%",
        "uploading_gdrive": "☁️ Google Drive এ আপলোড হচ্ছে...",
        "completed": "✅ ডাউনলোড সম্পন্ন!",
        "failed": "❌ ডাউনলোড ব্যর্থ: {error}",
        "file_info": "📦 File: {size}MB\n\n💾 Storage option চুজ করুন:",
        "gdrive_link": "☁️ আপনার ফাইল প্রস্তুত!\n\n🔗 Link: {url}\n\n📏 Size: {size}MB\n⏰ Valid for 7 days",
        "status": """
📊 আপনার পরিসংখ্যান

📥 মোট ডাউনলোড: {total}
📅 আজকের ডাউনলোড: {today}
⏳ আজ বাকি: {remaining}
📆 যোগদান: {joined}
☁️ Google Drive: {gdrive_status}
🚀 Upload Limit: 4GB (Client API)
""",
        "gdrive_connect": """
🔗 Google Drive সংযুক্ত করুন

1. এই লিংকে ক্লিক করুন:
{auth_url}

2. Google account দিয়ে login করুন
3. Permission দিন
4. Code copy করুন
5. এখানে paste করুন

⚠️ 5 মিনিটের মধ্যে code পাঠান!
""",
        "gdrive_connected": "✅ Google Drive সংযুক্ত হয়েছে!",
        "gdrive_error": "❌ Google Drive সংযুক্ত করতে ব্যর্থ!",
        "admin_panel": """
👑 Admin Panel

📊 Statistics:
• Total Users: {users}
• Today Downloads: {downloads}
• Active Now: {active}

🎛️ Commands:
/broadcast - সবাইকে message পাঠান
/stats - বিস্তারিত statistics
/users - User list
""",
        "not_admin": "⛔ শুধুমাত্র admin access!",
        "telegram_direct": "📱 Telegram এ পাঠান (4GB পর্যন্ত)",
        "save_gdrive": "☁️ Google Drive এ সেভ করুন",
        "gdrive_not_connected": "⚠️ Google Drive সংযুক্ত নেই!\n\n/gdrive command দিয়ে সংযুক্ত করুন।",
    }
}

def get_text(user_lang: str, key: str, **kwargs) -> str:
    """Get translated text"""
    text = TRANSLATIONS["bn"].get(key, key)
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
                total_downloads=0,
                is_admin=telegram_id in ADMIN_USER_IDS
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
        self.last_percent = 0
    
    def __call__(self, d):
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%').strip().replace('%', '')
                try:
                    percent = float(percent_str)
                except:
                    percent = 0
                
                current_time = asyncio.get_event_loop().time()
                
                if (abs(percent - self.last_percent) >= 5 or 
                    current_time - self.last_update > 3):
                    self.last_update = current_time
                    self.last_percent = percent
                    asyncio.create_task(
                        self.message.edit_text(
                            get_text(self.user_lang, "downloading", 
                                   progress=f"{percent:.0f}")
                        )
                    )
            except Exception as e:
                logger.error(f"Progress update error: {e}")

async def get_gdrive_service(user: User):
    """Get Google Drive service for user"""
    if not user.gdrive_token:
        return None
    
    try:
        creds = pickle.loads(user.gdrive_token.encode('latin1'))
        
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            async with async_session() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == user.telegram_id)
                )
                db_user = result.scalar_one()
                db_user.gdrive_token = pickle.dumps(creds).decode('latin1')
                await session.commit()
        
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"GDrive service error: {e}")
        return None

async def get_or_create_gdrive_folder(service) -> str:
    """Get or create YTDL folder in Google Drive"""
    try:
        results = service.files().list(
            q=f"name='{GDRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        folders = results.get('files', [])
        
        if folders:
            return folders[0]['id']
        
        file_metadata = {
            'name': GDRIVE_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
    except Exception as e:
        logger.error(f"GDrive folder error: {e}")
        return None

async def upload_to_gdrive(file_path: Path, user: User, status_msg: types.Message) -> Optional[str]:
    """Upload file to Google Drive"""
    try:
        service = await get_gdrive_service(user)
        if not service:
            return None
        
        folder_id = await get_or_create_gdrive_folder(service)
        if not folder_id:
            return None
        
        await status_msg.edit_text(get_text(user.language, "uploading_gdrive"))
        
        file_metadata = {
            'name': file_path.name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(
            str(file_path),
            resumable=True,
            chunksize=10*1024*1024
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(
            fileId=file.get('id'),
            body=permission
        ).execute()
        
        return file.get('webViewLink')
    
    except Exception as e:
        logger.error(f"GDrive upload error: {e}")
        return None

async def upload_large_file_pyrogram(file_path: Path, chat_id: int, caption: str, 
                                     status_msg: types.Message, user_lang: str, 
                                     is_audio: bool = False) -> bool:
    """Upload large files using Pyrogram (up to 4GB)"""
    try:
        logger.info(f"Starting Pyrogram upload: {file_path.name} ({file_path.stat().st_size / (1024*1024):.1f}MB)")
        
        # Progress callback
        last_update = [0]
        async def progress(current, total):
            try:
                percent = (current / total) * 100
                current_time = asyncio.get_event_loop().time()
                
                if current_time - last_update[0] > 3:  # Update every 3 seconds
                    last_update[0] = current_time
                    await status_msg.edit_text(
                        get_text(user_lang, "uploading_telegram", progress=f"{percent:.0f}")
                    )
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
        
        # Upload based on file type
        if is_audio:
            await app.send_audio(
                chat_id=chat_id,
                audio=str(file_path),
                caption=caption,
                progress=progress
            )
        else:
            await app.send_video(
                chat_id=chat_id,
                video=str(file_path),
                caption=caption,
                supports_streaming=True,
                progress=progress
            )
        
        logger.info(f"Pyrogram upload completed: {file_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"Pyrogram upload error: {e}")
        return False

async def download_video(url: str, format_type: str, quality: str, message: types.Message, user: User) -> Optional[Path]:
    """Download video/audio with maximum speed"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_template = str(TMP_DIR / f"{user.telegram_id}_{timestamp}_%(title)s.%(ext)s")
        
        ydl_opts = {
            'outtmpl': output_template,
            'progress_hooks': [DownloadProgress(message, user.language)],
            'quiet': True,
            'no_warnings': True,
            'concurrent_fragment_downloads': 10,
            'retries': 10,
            'fragment_retries': 10,
            'http_chunk_size': 10485760,
        }
        
        if format_type == "audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'writethumbnail': True,
                'postprocessor_args': ['-threads', '0'],
            })
        else:
            if quality == "best":
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif quality == "2160p":
                ydl_opts['format'] = 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]'
            elif quality == "1440p":
                ydl_opts['format'] = 'bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440]'
            elif quality == "1080p":
                ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
            elif quality == "720p":
                ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'
            else:
                height = quality.replace('p', '')
                ydl_opts['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}]'
            
            ydl_opts['merge_output_format'] = 'mp4'
            ydl_opts['postprocessor_args'] = ['-threads', '0']
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            base_name = ydl.prepare_filename(info)
            if format_type == "audio":
                file_path = Path(base_name).with_suffix('.mp3')
            else:
                file_path = Path(base_name)
            
            if file_path.exists():
                return file_path
            
            for file in TMP_DIR.glob(f"{user.telegram_id}_{timestamp}_*"):
                return file
        
        return None
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise

async def cleanup_file(file_path: Path):
    """Delete file from VPS immediately"""
    try:
        if file_path and file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

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
    await message.answer(get_text(user.language, "help"))

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Handle /status command"""
    user = await get_or_create_user(message.from_user.id)
    today_count = await get_today_downloads(user.telegram_id)
    remaining = max(0, RATE_LIMIT_PER_USER_PER_DAY - today_count)
    
    gdrive_status = "✅ সংযুক্ত" if user.gdrive_token else "❌ সংযুক্ত নেই"
    
    await message.answer(
        get_text(
            user.language,
            "status",
            total=user.total_downloads,
            today=today_count,
            remaining=remaining,
            joined=user.first_seen.strftime("%Y-%m-%d"),
            gdrive_status=gdrive_status
        )
    )

@dp.message(Command("gdrive"))
async def cmd_gdrive(message: types.Message, state: FSMContext):
    """Handle /gdrive command"""
    user = await get_or_create_user(message.from_user.id)
    
    try:
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": GDRIVE_CLIENT_ID,
                    "client_secret": GDRIVE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
                }
            },
            SCOPES
        )
        
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        await state.update_data(flow=flow)
        await state.set_state(GDriveAuthStates.waiting_for_code)
        
        await message.answer(
            get_text(user.language, "gdrive_connect", auth_url=auth_url),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"GDrive auth error: {e}")
        await message.answer(get_text(user.language, "gdrive_error"))

@dp.message(GDriveAuthStates.waiting_for_code)
async def process_gdrive_code(message: types.Message, state: FSMContext):
    """Process Google Drive authorization code"""
    user = await get_or_create_user(message.from_user.id)
    data = await state.get_data()
    flow = data.get('flow')
    
    try:
        flow.fetch_token(code=message.text.strip())
        creds = flow.credentials
        
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == user.telegram_id)
            )
            db_user = result.scalar_one()
            db_user.gdrive_token = pickle.dumps(creds).decode('latin1')
            await session.commit()
        
        await message.answer(get_text(user.language, "gdrive_connected"))
        await state.clear()
    except Exception as e:
        logger.error(f"GDrive token error: {e}")
        await message.answer(get_text(user.language, "gdrive_error"))
        await state.clear()

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Handle /admin command"""
    user = await get_or_create_user(message.from_user.id)
    
    if not user.is_admin:
        await message.answer(get_text(user.language, "not_admin"))
        return
    
    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
    
    await message.answer(
        get_text(
            user.language,
            "admin_panel",
            users=total_users,
            downloads=0,
            active=0
        )
    )

@dp.message(F.text)
async def handle_url(message: types.Message, state: FSMContext):
    """Handle URL message"""
    url = message.text.strip()
    
    if not is_valid_youtube_url(url):
        user = await get_or_create_user(message.from_user.id)
        await message.answer(get_text(user.language, "invalid_url"))
        return
    
    if not await check_rate_limit(message.from_user.id):
        user = await get_or_create_user(message.from_user.id)
        await message.answer(
            get_text(user.language, "rate_limited", limit=RATE_LIMIT_PER_USER_PER_DAY)
        )
        return
    
    await state.update_data(url=url)
    
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
    
    if format_type == "video":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Best (4K)", callback_data="quality_best")],
            [InlineKeyboardButton(text="4K (2160p)", callback_data="quality_2160p")],
            [InlineKeyboardButton(text="2K (1440p)", callback_data="quality_1440p")],
            [InlineKeyboardButton(text="1080p Full HD", callback_data="quality_1080p")],
            [InlineKeyboardButton(text="720p HD", callback_data="quality_720p")],
            [InlineKeyboardButton(text="480p", callback_data="quality_480p")],
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎵 Best Quality (320kbps)", callback_data="quality_best")]
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