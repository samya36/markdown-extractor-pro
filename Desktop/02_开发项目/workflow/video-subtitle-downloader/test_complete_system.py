#!/usr/bin/env python3
from universal_downloader import UniversalDownloader
import asyncio

async def test_complete_download():
    downloader = UniversalDownloader()
    
    # 测试用例
    test_cases = [
        {
            "url": "https://www.bilibili.com/video/BV1GJ411x7h7",
            "languages": ["zh-CN", "en"],
            "formats": ["srt", "vtt", "txt"]
        },
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "languages": ["en", "zh-CN"],
            "formats": ["srt", "json"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}: {test_case['url']}")
        
        try:
            # 获取视频信息
            info = await downloader.get_video_info_async(test_case["url"])
            print(f"✅ 视频标题: {info['title']}")
            print(f"✅ 可用字幕: {info.get('available_subtitles', [])}")
            
            # 下载字幕
            results = await downloader.download_subtitles_async(
                test_case["url"],
                languages=test_case["languages"],
                formats=test_case["formats"]
            )
            
            print(f"✅ 下载结果: {len(results)} 个文件")
            for lang, files in results.items():
                print(f"   {lang}: {list(files.keys())}")
                
        except Exception as e:
            print(f"❌ 错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_complete_download())
