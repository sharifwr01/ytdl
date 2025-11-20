"""
Unit tests for YouTube Telegram Bot
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# Import bot modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot import (
    get_or_create_user,
    check_rate_limit,
    get_today_downloads,
    is_valid_youtube_url,
    download_video,
    get_text,
    User
)


class TestUserManagement:
    """Test user management functions"""
    
    @pytest.mark.asyncio
    async def test_create_new_user(self):
        """Test creating a new user"""
        user = await get_or_create_user(123456789, "testuser")
        
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.total_downloads == 0
        assert isinstance(user.first_seen, datetime)
    
    @pytest.mark.asyncio
    async def test_get_existing_user(self):
        """Test getting an existing user"""
        # Create user first
        user1 = await get_or_create_user(123456789, "testuser")
        original_first_seen = user1.first_seen
        
        # Get same user
        user2 = await get_or_create_user(123456789, "testuser")
        
        assert user2.telegram_id == user1.telegram_id
        assert user2.first_seen == original_first_seen


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_new_user(self):
        """Test rate limit for new user"""
        result = await check_rate_limit(999999)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit exceeded"""
        user_id = 888888
        
        # Simulate max downloads
        for _ in range(20):
            await check_rate_limit(user_id)
        
        # Should be rate limited now
        result = await check_rate_limit(user_id)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_today_downloads(self):
        """Test getting today's download count"""
        user_id = 777777
        
        # Make 5 downloads
        for _ in range(5):
            await check_rate_limit(user_id)
        
        count = await get_today_downloads(user_id)
        assert count == 5


class TestURLValidation:
    """Test YouTube URL validation"""
    
    def test_valid_youtube_urls(self):
        """Test various valid YouTube URLs"""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ&t=10s",
        ]
        
        for url in valid_urls:
            assert is_valid_youtube_url(url), f"Failed for: {url}"
    
    def test_invalid_youtube_urls(self):
        """Test invalid URLs"""
        invalid_urls = [
            "https://vimeo.com/123456",
            "https://example.com",
            "not a url",
            "",
            "youtube.com",  # Missing protocol
        ]
        
        for url in invalid_urls:
            assert not is_valid_youtube_url(url), f"Should fail for: {url}"


class TestTranslations:
    """Test translation functionality"""
    
    def test_english_translation(self):
        """Test English translations"""
        text = get_text("en", "welcome")
        assert "Welcome" in text
        assert "YouTube" in text
    
    def test_bangla_translation(self):
        """Test Bangla translations"""
        text = get_text("bn", "welcome")
        assert "স্বাগতম" in text
    
    def test_fallback_to_english(self):
        """Test fallback to English for unknown language"""
        text = get_text("xx", "welcome")
        assert "Welcome" in text
    
    def test_translation_with_params(self):
        """Test translations with parameters"""
        text = get_text("en", "rate_limited", limit=20)
        assert "20" in text


class TestDownloadFunctionality:
    """Test download functionality"""
    
    @pytest.mark.asyncio
    async def test_download_video_success(self):
        """Test successful video download"""
        mock_message = AsyncMock()
        mock_user = Mock()
        mock_user.telegram_id = 123456789
        mock_user.language = "en"
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            # Mock yt-dlp
            mock_instance = mock_ydl.return_value.__enter__.return_value
            mock_instance.extract_info.return_value = {
                'title': 'Test Video',
                'ext': 'mp4'
            }
            mock_instance.prepare_filename.return_value = '/tmp/test_video.mp4'
            
            # Create fake file
            test_file = Path('/tmp/test_video.mp4')
            test_file.touch()
            
            try:
                result = await download_video(
                    url="https://youtube.com/watch?v=test",
                    format_type="video",
                    quality="720p",
                    message=mock_message,
                    user=mock_user
                )
                
                assert result is not None
                assert result.exists()
            finally:
                # Cleanup
                if test_file.exists():
                    test_file.unlink()
    
    @pytest.mark.asyncio
    async def test_download_audio_success(self):
        """Test successful audio download"""
        mock_message = AsyncMock()
        mock_user = Mock()
        mock_user.telegram_id = 123456789
        mock_user.language = "en"
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = mock_ydl.return_value.__enter__.return_value
            mock_instance.extract_info.return_value = {
                'title': 'Test Audio',
                'ext': 'mp3'
            }
            mock_instance.prepare_filename.return_value = '/tmp/test_audio.mp3'
            
            test_file = Path('/tmp/test_audio.mp3')
            test_file.touch()
            
            try:
                result = await download_video(
                    url="https://youtube.com/watch?v=test",
                    format_type="audio",
                    quality="best",
                    message=mock_message,
                    user=mock_user
                )
                
                assert result is not None
            finally:
                if test_file.exists():
                    test_file.unlink()


class TestCommandHandlers:
    """Test bot command handlers"""
    
    @pytest.mark.asyncio
    async def test_start_command(self):
        """Test /start command"""
        from bot import cmd_start
        
        mock_message = AsyncMock()
        mock_message.from_user.id = 123456789
        mock_message.from_user.username = "testuser"
        
        await cmd_start(mock_message)
        
        # Verify message was sent
        mock_message.answer.assert_called_once()
        args = mock_message.answer.call_args[0]
        assert "Welcome" in args[0] or "স্বাগতম" in args[0]
    
    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test /help command"""
        from bot import cmd_help
        
        mock_message = AsyncMock()
        mock_message.from_user.id = 123456789
        
        await cmd_help(mock_message)
        
        mock_message.answer.assert_called_once()
        args = mock_message.answer.call_args[0]
        assert "Commands" in args[0] or "কমান্ড" in args[0]
    
    @pytest.mark.asyncio
    async def test_status_command(self):
        """Test /status command"""
        from bot import cmd_status
        
        mock_message = AsyncMock()
        mock_message.from_user.id = 123456789
        
        await cmd_status(mock_message)
        
        mock_message.answer.assert_called_once()
        args = mock_message.answer.call_args[0]
        assert "Statistics" in args[0] or "পরিসংখ্যান" in args[0]


class TestDatabase:
    """Test database operations"""
    
    @pytest.mark.asyncio
    async def test_user_creation_in_db(self):
        """Test user is created in database"""
        from bot import async_session, User
        from sqlalchemy import select
        
        user = await get_or_create_user(555555, "dbtest")
        
        # Verify in database
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == 555555)
            )
            db_user = result.scalar_one_or_none()
            
            assert db_user is not None
            assert db_user.telegram_id == 555555
            assert db_user.username == "dbtest"
    
    @pytest.mark.asyncio
    async def test_user_update_in_db(self):
        """Test user updates in database"""
        from bot import async_session, User
        from sqlalchemy import select
        
        # Create user
        user = await get_or_create_user(444444, "updatetest")
        
        # Update downloads
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == 444444)
            )
            db_user = result.scalar_one()
            db_user.total_downloads += 1
            await session.commit()
        
        # Verify update
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == 444444)
            )
            db_user = result.scalar_one()
            assert db_user.total_downloads == 1


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_url_handling(self):
        """Test handling of invalid URLs"""
        from bot import handle_url
        
        mock_message = AsyncMock()
        mock_message.text = "not a valid url"
        mock_message.from_user.id = 123456789
        
        mock_state = AsyncMock()
        
        await handle_url(mock_message, mock_state)
        
        # Should send error message
        mock_message.answer.assert_called_once()
        args = mock_message.answer.call_args[0]
        assert "Invalid" in args[0] or "অবৈধ" in args[0]
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test rate limit error handling"""
        from bot import handle_url
        
        user_id = 333333
        
        # Exhaust rate limit
        for _ in range(25):
            await check_rate_limit(user_id)
        
        mock_message = AsyncMock()
        mock_message.text = "https://youtube.com/watch?v=test"
        mock_message.from_user.id = user_id
        
        mock_state = AsyncMock()
        
        await handle_url(mock_message, mock_state)
        
        # Should send rate limit message
        mock_message.answer.assert_called_once()


class TestFileHandling:
    """Test file handling"""
    
    def test_file_size_check(self):
        """Test file size checking"""
        test_file = Path('/tmp/test_size.txt')
        test_file.write_text("x" * (50 * 1024 * 1024))  # 50MB
        
        try:
            size_mb = test_file.stat().st_size / (1024 * 1024)
            assert size_mb >= 50
            assert size_mb <= 51
        finally:
            test_file.unlink()
    
    def test_tmp_directory_creation(self):
        """Test temporary directory creation"""
        from bot import TMP_DIR
        
        assert TMP_DIR.exists()
        assert TMP_DIR.is_dir()


# Fixtures
@pytest.fixture(autouse=True)
async def setup_teardown():
    """Setup and teardown for each test"""
    # Setup
    from bot import init_db
    await init_db()
    
    yield
    
    # Teardown
    # Clean up test data
    pass


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=bot", "--cov-report=html"])