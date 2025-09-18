"""
YouTube Video Downloader
Handles downloading videos from YouTube URLs for analysis
"""

import yt_dlp
import os
import tempfile
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime

class YouTubeDownloader:
    """Handles YouTube video downloads for analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the YouTube downloader
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self._setup_logging()
        self._setup_download_options()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_download_options(self):
        """Setup yt-dlp download options"""
        self.ydl_opts = {
            'format': 'best[height<=720]',  # Limit to 720p to keep file sizes reasonable
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': False,  # Show progress
            'no_warnings': False,
            'extract_flat': False,
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
    
    def download_video(self, url: str, output_dir: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Download a video from YouTube URL
        
        Args:
            url: YouTube video URL
            output_dir: Directory to save the video (optional)
            
        Returns:
            Tuple of (success, file_path, metadata)
        """
        try:
            print(f"🎬 Starting YouTube download: {url}")
            self.logger.info(f"Starting YouTube download: {url}")
            
            # Create temporary directory if none specified
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="youtube_download_")
            
            # Update output template for the directory
            self.ydl_opts['outtmpl'] = os.path.join(output_dir, '%(title)s.%(ext)s')
            
            # Get video info first
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                video_title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', 'Unknown')
                view_count = info.get('view_count', 0)
                
                print(f"📺 Video Info:")
                print(f"   Title: {video_title}")
                print(f"   Duration: {duration // 60}:{duration % 60:02d}")
                print(f"   Uploader: {uploader}")
                print(f"   Views: {view_count:,}")
                
                # Check duration (limit to 30 minutes for analysis)
                if duration > 1800:  # 30 minutes
                    print(f"⚠️  Warning: Video is {duration // 60} minutes long. Analysis may take longer.")
            
            # Download the video
            print("⬇️  Downloading video...")
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded file
            downloaded_files = [f for f in os.listdir(output_dir) if f.endswith(('.mp4', '.webm', '.mkv', '.avi'))]
            
            if not downloaded_files:
                raise Exception("No video file found after download")
            
            video_file = os.path.join(output_dir, downloaded_files[0])
            file_size = os.path.getsize(video_file)
            
            print(f"✅ Download completed: {downloaded_files[0]} ({file_size / (1024*1024):.2f} MB)")
            
            metadata = {
                'title': video_title,
                'duration': duration,
                'uploader': uploader,
                'view_count': view_count,
                'url': url,
                'file_size': file_size,
                'download_time': datetime.now().isoformat()
            }
            
            self.logger.info(f"Download completed: {video_file}")
            return True, video_file, metadata
            
        except Exception as e:
            error_msg = f"Error downloading video: {str(e)}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg)
            return False, "", {}
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get video information without downloading
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video metadata dictionary
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', '')[:500],  # First 500 chars
                    'upload_date': info.get('upload_date', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': url
                }
                
        except Exception as e:
            self.logger.error(f"Error getting video info: {str(e)}")
            return {}
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if the URL is a valid YouTube URL
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid YouTube URL, False otherwise
        """
        youtube_domains = [
            'youtube.com',
            'youtu.be',
            'm.youtube.com',
            'www.youtube.com'
        ]
        
        return any(domain in url.lower() for domain in youtube_domains)
