"""
通用视频字幕下载器
统一所有组件提供完整的字幕下载功能
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from urllib.parse import urlparse
import aiohttp
from datetime import datetime

from .config import subtitle_config, app_config, env_config
from .extractors.base_extractor import SubtitleSegment, SubtitleTrack, VideoInfo
from .extractors.youtube_extractor import YouTubeSubtitleExtractor
from .extractors.bilibili_extractor import BilibiliSubtitleExtractor
from .extractors.generic_extractor import GenericSubtitleExtractor
from .ai_generator import AISubtitleGenerator, TranscriptionResult
from .format_converter import SubtitleFormatConverter
from ..backend.task_manager import TaskManager
from ..backend.enhanced_downloader import EnhancedDownloader

logger = logging.getLogger(__name__)

@dataclass
class DownloadRequest:
    """下载请求数据结构"""
    url: str
    languages: List[str] = None
    formats: List[str] = None
    enable_ai_fallback: bool = True
    ai_model: str = "base"
    ai_model_type: str = "whisper"
    output_dir: str = ""
    filename_template: str = "{title}_{language}.{format}"
    quality_filter: str = "best"
    enable_translation: bool = False
    translation_target: str = "zh-CN"

@dataclass
class DownloadResult:
    """下载结果数据结构"""
    success: bool
    video_info: Optional[VideoInfo]
    subtitle_tracks: List[SubtitleTrack]
    downloaded_files: List[str]
    ai_generated: bool = False
    errors: List[str] = None
    processing_time: float = 0.0
    total_segments: int = 0

class UniversalSubtitleDownloader:
    """通用字幕下载器主类"""
    
    def __init__(self, proxy_manager=None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.proxy_manager = proxy_manager
        
        # 初始化组件
        self.ai_generator = AISubtitleGenerator()
        self.format_converter = SubtitleFormatConverter()
        self.task_manager = TaskManager()
        self.enhanced_downloader = EnhancedDownloader()
        
        # 初始化平台提取器
        self.extractors = {
            'youtube': YouTubeSubtitleExtractor(proxy_manager),
            'bilibili': BilibiliSubtitleExtractor(proxy_manager),
            'generic': GenericSubtitleExtractor(proxy_manager),  # 通用提取器作为后备
        }
        
        # 会话管理
        self.session = None
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_downloads': 0,
            'ai_generated_count': 0,
            'failed_requests': 0,
            'total_processing_time': 0.0
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def download_subtitles(self, request: DownloadRequest) -> DownloadResult:
        """主要的字幕下载方法"""
        start_time = asyncio.get_event_loop().time()
        self.stats['total_requests'] += 1
        
        try:
            self.logger.info(f"Starting subtitle download for: {request.url}")
            
            # 1. 识别平台并获取适当的提取器
            extractor = self._get_extractor(request.url)
            if not extractor:
                raise Exception(f"Unsupported platform for URL: {request.url}")
            
            # 2. 提取视频信息
            self.logger.info("Extracting video information...")
            video_info = await extractor.extract_video_info(request.url)
            
            # 3. 设置默认语言和格式
            languages = request.languages or ['zh-CN', 'en']
            formats = request.formats or ['srt', 'vtt']
            
            # 4. 尝试提取现有字幕
            self.logger.info(f"Attempting to extract existing subtitles for languages: {languages}")
            subtitle_tracks = await extractor.extract_subtitles(request.url, languages)
            
            ai_generated = False
            
            # 5. 如果没有找到字幕且启用AI回退，使用AI生成
            if not subtitle_tracks and request.enable_ai_fallback:
                self.logger.info("No existing subtitles found, attempting AI generation...")
                
                try:
                    # 下载音频用于AI转录
                    audio_file = await self._download_audio_for_ai(request.url, video_info)
                    
                    if audio_file:
                        # 使用AI生成字幕
                        ai_result = await self.ai_generator.generate_subtitles(
                            audio_file=audio_file,
                            target_language=languages[0] if languages else "auto",
                            model_name=request.ai_model,
                            model_type=request.ai_model_type
                        )
                        
                        # 创建AI生成的字幕轨道
                        ai_track = self.ai_generator.create_subtitle_track_from_ai(
                            ai_result, request.url
                        )
                        subtitle_tracks.append(ai_track)
                        ai_generated = True
                        self.stats['ai_generated_count'] += 1
                        
                        self.logger.info(f"AI generated {len(ai_result.segments)} subtitle segments")
                        
                        # 清理临时音频文件
                        try:
                            os.unlink(audio_file)
                        except:
                            pass
                    
                except Exception as e:
                    self.logger.warning(f"AI generation failed: {str(e)}")
            
            # 6. 翻译字幕（如果需要）
            if request.enable_translation and subtitle_tracks:
                self.logger.info(f"Translating subtitles to {request.translation_target}")
                translated_tracks = []
                
                for track in subtitle_tracks:
                    if track.language != request.translation_target:
                        try:
                            translated_segments = await self.ai_generator.translate_subtitles(
                                track.segments, request.translation_target
                            )
                            
                            translated_track = SubtitleTrack(
                                language=request.translation_target,
                                language_name=subtitle_config.SUPPORTED_LANGUAGES.get(
                                    request.translation_target, request.translation_target
                                ),
                                is_auto_generated=track.is_auto_generated,
                                format=track.format,
                                url=track.url,
                                segments=translated_segments,
                                quality=track.quality,
                                source=f"translated_from_{track.language}"
                            )
                            translated_tracks.append(translated_track)
                            
                        except Exception as e:
                            self.logger.warning(f"Translation failed for track {track.language}: {str(e)}")
                            translated_tracks.append(track)  # 保留原版本
                    else:
                        translated_tracks.append(track)
                
                subtitle_tracks = translated_tracks
            
            # 7. 格式转换和文件保存
            downloaded_files = []
            
            if subtitle_tracks:
                output_dir = Path(request.output_dir) if request.output_dir else app_config.DOWNLOAD_DIR
                output_dir.mkdir(parents=True, exist_ok=True)
                
                for track in subtitle_tracks:
                    for format_type in formats:
                        try:
                            # 转换格式
                            if track.format != format_type:
                                content = self.format_converter.convert_subtitle_track(track, format_type)
                            else:
                                # 如果已经是目标格式，重新生成以确保格式正确
                                content = self.format_converter.convert_subtitle_track(track, format_type)
                            
                            # 生成文件名
                            filename = self._generate_filename(
                                video_info, track, format_type, request.filename_template
                            )
                            
                            # 保存文件
                            file_path = output_dir / filename
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            
                            downloaded_files.append(str(file_path))
                            self.logger.info(f"Saved subtitle: {filename}")
                            
                        except Exception as e:
                            self.logger.error(f"Failed to save {format_type} subtitle for {track.language}: {str(e)}")
            
            # 8. 计算统计信息
            processing_time = asyncio.get_event_loop().time() - start_time
            total_segments = sum(len(track.segments) for track in subtitle_tracks)
            
            # 9. 创建结果
            result = DownloadResult(
                success=bool(subtitle_tracks),
                video_info=video_info,
                subtitle_tracks=subtitle_tracks,
                downloaded_files=downloaded_files,
                ai_generated=ai_generated,
                errors=[],
                processing_time=processing_time,
                total_segments=total_segments
            )
            
            if result.success:
                self.stats['successful_downloads'] += 1
            else:
                self.stats['failed_requests'] += 1
                result.errors = ["No subtitles found and AI generation disabled or failed"]
            
            self.stats['total_processing_time'] += processing_time
            
            self.logger.info(f"Download completed in {processing_time:.2f}s, "
                           f"found {len(subtitle_tracks)} tracks, "
                           f"saved {len(downloaded_files)} files")
            
            return result
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            processing_time = asyncio.get_event_loop().time() - start_time
            self.stats['total_processing_time'] += processing_time
            
            self.logger.error(f"Download failed: {str(e)}")
            
            return DownloadResult(
                success=False,
                video_info=None,
                subtitle_tracks=[],
                downloaded_files=[],
                ai_generated=False,
                errors=[str(e)],
                processing_time=processing_time,
                total_segments=0
            )
    
    def _get_extractor(self, url: str):
        """根据URL获取合适的提取器"""
        # 按优先级检查专用提取器
        priority_extractors = ['youtube', 'bilibili']
        
        for platform in priority_extractors:
            if platform in self.extractors:
                extractor = self.extractors[platform]
                if extractor.can_handle(url):
                    return extractor
        
        # 如果没有找到专用提取器，使用通用提取器
        if 'generic' in self.extractors:
            generic_extractor = self.extractors['generic']
            if generic_extractor.can_handle(url):
                return generic_extractor
        
        return None
    
    async def _download_audio_for_ai(self, url: str, video_info: VideoInfo) -> Optional[str]:
        """下载音频文件用于AI转录"""
        try:
            # 创建临时目录
            temp_dir = app_config.CACHE_DIR / "audio"
            temp_dir.mkdir(exist_ok=True, parents=True)
            
            # 生成临时文件名
            audio_filename = f"{video_info.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            audio_path = temp_dir / audio_filename
            
            # 使用enhanced_downloader下载音频
            download_result = await self.enhanced_downloader.download_audio_only(
                url, str(audio_path)
            )
            
            if download_result and os.path.exists(audio_path):
                return str(audio_path)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to download audio for AI: {str(e)}")
            return None
    
    def _generate_filename(self, video_info: VideoInfo, track: SubtitleTrack, 
                          format_type: str, template: str) -> str:
        """生成字幕文件名"""
        try:
            # 清理文件名中的非法字符
            safe_title = self._sanitize_filename(video_info.title)
            
            # 替换模板变量
            filename = template.format(
                title=safe_title,
                language=track.language,
                language_name=track.language_name.replace(' ', '_'),
                format=format_type,
                platform=video_info.platform,
                uploader=self._sanitize_filename(video_info.uploader),
                id=video_info.id,
                quality=track.quality,
                source=track.source
            )
            
            return filename
            
        except Exception as e:
            self.logger.warning(f"Failed to generate filename from template: {str(e)}")
            # 回退到简单格式
            safe_title = self._sanitize_filename(video_info.title)
            return f"{safe_title}_{track.language}.{format_type}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        # 移除或替换非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename.strip()
    
    async def batch_download(self, requests: List[DownloadRequest], 
                           max_concurrent: int = None) -> List[DownloadResult]:
        """批量下载字幕"""
        if max_concurrent is None:
            max_concurrent = app_config.MAX_CONCURRENT_DOWNLOADS
        
        self.logger.info(f"Starting batch download of {len(requests)} requests")
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(request):
            async with semaphore:
                return await self.download_subtitles(request)
        
        # 并发执行下载
        tasks = [download_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch download {i} failed: {str(result)}")
                processed_results.append(DownloadResult(
                    success=False,
                    video_info=None,
                    subtitle_tracks=[],
                    downloaded_files=[],
                    errors=[str(result)]
                ))
            else:
                processed_results.append(result)
        
        successful = sum(1 for r in processed_results if r.success)
        self.logger.info(f"Batch download completed: {successful}/{len(requests)} successful")
        
        return processed_results
    
    async def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """获取视频信息"""
        try:
            extractor = self._get_extractor(url)
            if extractor:
                return await extractor.extract_video_info(url)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get video info: {str(e)}")
            return None
    
    async def list_available_subtitles(self, url: str) -> Dict[str, Any]:
        """列出可用的字幕"""
        try:
            extractor = self._get_extractor(url)
            if not extractor:
                return {'error': 'Unsupported platform'}
            
            video_info = await extractor.extract_video_info(url)
            
            return {
                'video_info': video_info.to_dict(),
                'available_subtitles': video_info.available_subtitles,
                'automatic_captions': video_info.automatic_captions,
                'supported_formats': subtitle_config.SUPPORTED_FORMATS,
                'ai_models_available': self.ai_generator.get_available_models()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to list available subtitles: {str(e)}")
            return {'error': str(e)}
    
    def get_supported_platforms(self) -> Dict[str, Dict]:
        """获取支持的平台信息"""
        return subtitle_config.PLATFORM_CONFIGS
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言"""
        return subtitle_config.SUPPORTED_LANGUAGES
    
    def get_supported_formats(self) -> Dict[str, Dict]:
        """获取支持的格式"""
        return self.format_converter.get_supported_formats()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_downloads'] / stats['total_requests']
            stats['average_processing_time'] = stats['total_processing_time'] / stats['total_requests']
        else:
            stats['success_rate'] = 0.0
            stats['average_processing_time'] = 0.0
        
        return stats
    
    async def cleanup_cache(self, max_age_days: int = 7):
        """清理缓存文件"""
        try:
            cache_dir = app_config.CACHE_DIR
            if not cache_dir.exists():
                return
            
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            
            deleted_count = 0
            for file_path in cache_dir.rglob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except OSError:
                            pass
            
            self.logger.info(f"Cleaned up {deleted_count} cache files older than {max_age_days} days")
            
        except Exception as e:
            self.logger.error(f"Cache cleanup failed: {str(e)}")
    
    async def validate_url(self, url: str) -> Dict[str, Any]:
        """验证URL是否受支持"""
        try:
            extractor = self._get_extractor(url)
            if not extractor:
                return {
                    'valid': False,
                    'error': 'Unsupported platform',
                    'supported_platforms': list(self.get_supported_platforms().keys())
                }
            
            # 尝试获取基本信息来验证URL
            try:
                video_info = await extractor.extract_video_info(url)
                return {
                    'valid': True,
                    'platform': video_info.platform,
                    'title': video_info.title,
                    'duration': video_info.duration,
                    'has_subtitles': bool(video_info.available_subtitles or video_info.automatic_captions)
                }
            except Exception as e:
                return {
                    'valid': False,
                    'error': f'Failed to access video: {str(e)}'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }