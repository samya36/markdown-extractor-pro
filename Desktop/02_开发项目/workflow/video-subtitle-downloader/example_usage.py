#!/usr/bin/env python3
"""
通用字幕下载器使用示例
Universal Subtitle Downloader Usage Examples
"""

import asyncio
import logging
from pathlib import Path

# 导入通用字幕下载器组件
from universal_subtitle_downloader import (
    UniversalSubtitleDownloader,
    DownloadRequest,
    get_supported_platforms,
    get_supported_formats
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def example_basic_download():
    """基础下载示例"""
    print("=" * 50)
    print("基础下载示例")
    print("=" * 50)
    
    async with UniversalSubtitleDownloader() as downloader:
        # 创建下载请求
        request = DownloadRequest(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll 示例
            languages=['en', 'zh-CN'],
            formats=['srt', 'vtt']
        )
        
        # 执行下载
        result = await downloader.download_subtitles(request)
        
        if result.success:
            print(f"✅ 成功下载: {result.video_info.title}")
            print(f"   字幕轨道: {len(result.subtitle_tracks)}")
            print(f"   文件数量: {len(result.downloaded_files)}")
        else:
            print(f"❌ 下载失败: {result.errors}")

async def example_ai_generation():
    """AI字幕生成示例"""
    print("=" * 50)
    print("AI字幕生成示例")
    print("=" * 50)
    
    async with UniversalSubtitleDownloader() as downloader:
        request = DownloadRequest(
            url="https://example.com/video-without-subtitles.mp4",
            languages=['zh-CN'],
            formats=['srt', 'json'],
            enable_ai_fallback=True,
            ai_model="base",
            ai_model_type="whisper"
        )
        
        result = await downloader.download_subtitles(request)
        
        if result.success:
            print(f"✅ AI生成成功: {result.video_info.title}")
            print(f"   是否AI生成: {result.ai_generated}")
            print(f"   总段落数: {result.total_segments}")
        else:
            print(f"❌ AI生成失败: {result.errors}")

async def example_bilibili_download():
    """哔哩哔哩下载示例"""
    print("=" * 50)
    print("哔哩哔哩下载示例")
    print("=" * 50)
    
    async with UniversalSubtitleDownloader() as downloader:
        request = DownloadRequest(
            url="https://www.bilibili.com/video/BV1xx411c7mu",
            languages=['zh-CN', 'zh'],
            formats=['srt', 'ass']
        )
        
        result = await downloader.download_subtitles(request)
        
        if result.success:
            print(f"✅ B站下载成功: {result.video_info.title}")
            for track in result.subtitle_tracks:
                print(f"   语言: {track.language_name} ({track.format})")
        else:
            print(f"❌ B站下载失败: {result.errors}")

async def example_batch_download():
    """批量下载示例"""
    print("=" * 50)
    print("批量下载示例")
    print("=" * 50)
    
    async with UniversalSubtitleDownloader() as downloader:
        # 准备多个下载请求
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.bilibili.com/video/BV1xx411c7mu",
            # 可以添加更多URL
        ]
        
        requests = []
        for url in urls:
            request = DownloadRequest(
                url=url,
                languages=['zh-CN', 'en'],
                formats=['srt'],
                enable_ai_fallback=True
            )
            requests.append(request)
        
        # 执行批量下载
        results = await downloader.batch_download(requests, max_concurrent=2)
        
        successful = sum(1 for r in results if r.success)
        print(f"批量下载完成: {successful}/{len(results)} 成功")

async def example_translation():
    """字幕翻译示例"""
    print("=" * 50)
    print("字幕翻译示例")
    print("=" * 50)
    
    async with UniversalSubtitleDownloader() as downloader:
        request = DownloadRequest(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            languages=['en'],
            formats=['srt'],
            enable_translation=True,
            translation_target='zh-CN'
        )
        
        result = await downloader.download_subtitles(request)
        
        if result.success:
            print(f"✅ 翻译成功: {result.video_info.title}")
            for track in result.subtitle_tracks:
                print(f"   语言: {track.language_name} (来源: {track.source})")
        else:
            print(f"❌ 翻译失败: {result.errors}")

async def example_video_info():
    """视频信息获取示例"""
    print("=" * 50)
    print("视频信息获取示例")
    print("=" * 50)
    
    async with UniversalSubtitleDownloader() as downloader:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # 获取视频信息
        video_info = await downloader.get_video_info(url)
        
        if video_info:
            print(f"标题: {video_info.title}")
            print(f"时长: {video_info.duration}秒")
            print(f"作者: {video_info.uploader}")
            print(f"平台: {video_info.platform}")
            print(f"可用字幕: {video_info.available_subtitles}")
            print(f"自动字幕: {video_info.automatic_captions}")
        
        # 列出可用字幕
        subtitle_info = await downloader.list_available_subtitles(url)
        print(f"\n详细字幕信息:")
        print(f"手动字幕: {subtitle_info.get('available_subtitles', [])}")
        print(f"自动字幕: {subtitle_info.get('automatic_captions', [])}")

async def example_format_conversion():
    """格式转换示例"""
    print("=" * 50)
    print("格式转换示例")
    print("=" * 50)
    
    async with UniversalSubtitleDownloader() as downloader:
        request = DownloadRequest(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            languages=['en'],
            formats=['srt', 'vtt', 'ass', 'json', 'csv']  # 多种格式
        )
        
        result = await downloader.download_subtitles(request)
        
        if result.success:
            print(f"✅ 格式转换成功: {result.video_info.title}")
            print(f"生成的文件:")
            for file_path in result.downloaded_files:
                file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
                print(f"   📁 {Path(file_path).name} ({file_size} bytes)")
        else:
            print(f"❌ 格式转换失败: {result.errors}")

def show_system_info():
    """显示系统信息"""
    print("=" * 50)
    print("系统支持信息")
    print("=" * 50)
    
    print("支持的平台:")
    platforms = get_supported_platforms()
    for platform in platforms:
        print(f"   ✓ {platform}")
    
    print("\n支持的格式:")
    formats = get_supported_formats()
    for fmt in formats:
        print(f"   ✓ {fmt}")
    
    print(f"\n总共支持 {len(platforms)} 个平台，{len(formats)} 种格式")

async def main():
    """主函数 - 运行所有示例"""
    print("通用字幕下载器使用示例")
    print("Universal Subtitle Downloader Examples")
    
    # 显示系统信息
    show_system_info()
    
    try:
        # 运行各种示例
        await example_video_info()
        await example_basic_download()
        await example_format_conversion()
        # await example_ai_generation()  # 需要音频文件，跳过
        # await example_bilibili_download()  # 需要具体的B站视频
        # await example_translation()  # 需要翻译服务配置
        # await example_batch_download()  # 较耗时，跳过
        
        print("\n=" * 50)
        print("所有示例执行完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 示例执行错误: {str(e)}")
        logger.exception("Example execution failed")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())