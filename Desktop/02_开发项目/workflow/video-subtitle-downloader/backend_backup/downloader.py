import yt_dlp
import whisper
import os
import json
from pathlib import Path
from typing import Dict, List, Optional

class VideoSubtitleDownloader:
    def __init__(self):
        self.whisper_model = None
        self.download_dir = "downloads"
        Path(self.download_dir).mkdir(exist_ok=True)
    
    def get_video_info(self, url: str) -> Dict:
        """获取视频基本信息"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'has_subtitles': bool(info.get('subtitles', {})),
                    'available_subtitles': list(info.get('subtitles', {}).keys()),
                    'automatic_captions': list(info.get('automatic_captions', {}).keys())
                }
            except Exception as e:
                raise Exception(f"无法获取视频信息: {str(e)}")
