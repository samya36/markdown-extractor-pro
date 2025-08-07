#!/usr/bin/env python3
"""
通用字幕下载器命令行界面
"""

import asyncio
import argparse
import sys
import json
import logging
from pathlib import Path
from typing import List, Optional

from .universal_downloader import UniversalSubtitleDownloader, DownloadRequest
from .config import subtitle_config, app_config, env_config

def setup_logging(level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(app_config.LOGS_DIR / 'subtitle_downloader.log')
        ]
    )

def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="通用视频字幕下载器 - 支持多平台和多格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s https://www.youtube.com/watch?v=dQw4w9WgXcQ
  %(prog)s https://www.bilibili.com/video/BV1xx411c7mu --languages zh-CN en
  %(prog)s https://example.com/video.mp4 --ai-fallback --ai-model base
  %(prog)s --batch urls.txt --output-dir ./downloads
        """
    )
    
    # 基本选项
    parser.add_argument(
        'url',
        nargs='?',
        help='视频URL（或使用--batch指定文件）'
    )
    
    parser.add_argument(
        '--batch',
        type=str,
        help='批量下载，指定包含URL列表的文件'
    )
    
    # 语言选项
    parser.add_argument(
        '--languages', '-l',
        nargs='+',
        default=['zh-CN', 'en'],
        help='字幕语言代码列表（默认: zh-CN en）'
    )
    
    # 格式选项
    parser.add_argument(
        '--formats', '-f',
        nargs='+',
        choices=subtitle_config.SUPPORTED_FORMATS,
        default=['srt'],
        help='输出格式列表（默认: srt）'
    )
    
    # AI选项
    parser.add_argument(
        '--ai-fallback',
        action='store_true',
        help='启用AI字幕生成作为回退'
    )
    
    parser.add_argument(
        '--ai-model',
        choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
        default='base',
        help='AI模型选择（默认: base）'
    )
    
    parser.add_argument(
        '--ai-model-type',
        choices=['whisper', 'speech_recognition'],
        default='whisper',
        help='AI模型类型（默认: whisper）'
    )
    
    # 翻译选项
    parser.add_argument(
        '--translate',
        action='store_true',
        help='启用字幕翻译'
    )
    
    parser.add_argument(
        '--translate-to',
        default='zh-CN',
        help='翻译目标语言（默认: zh-CN）'
    )
    
    # 输出选项
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='',
        help='输出目录（默认: downloads/）'
    )
    
    parser.add_argument(
        '--filename-template',
        default='{title}_{language}.{format}',
        help='文件名模板（默认: {title}_{language}.{format}）'
    )
    
    # 质量选项
    parser.add_argument(
        '--quality',
        choices=['best', 'worst', 'medium'],
        default='best',
        help='字幕质量过滤（默认: best）'
    )
    
    # 并发选项
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=3,
        help='最大并发下载数（默认: 3）'
    )
    
    # 信息选项
    parser.add_argument(
        '--info-only',
        action='store_true',
        help='只显示视频信息，不下载字幕'
    )
    
    parser.add_argument(
        '--list-subtitles',
        action='store_true',
        help='列出可用字幕，不下载'
    )
    
    parser.add_argument(
        '--list-formats',
        action='store_true',
        help='列出支持的格式'
    )
    
    parser.add_argument(
        '--list-languages',
        action='store_true',
        help='列出支持的语言'
    )
    
    # 调试选项
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='安静模式'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别（默认: INFO）'
    )
    
    return parser

async def download_single(downloader: UniversalSubtitleDownloader, args) -> bool:
    """下载单个视频的字幕"""
    try:
        # 创建下载请求
        request = DownloadRequest(
            url=args.url,
            languages=args.languages,
            formats=args.formats,
            enable_ai_fallback=args.ai_fallback,
            ai_model=args.ai_model,
            ai_model_type=args.ai_model_type,
            output_dir=args.output_dir,
            filename_template=args.filename_template,
            quality_filter=args.quality,
            enable_translation=args.translate,
            translation_target=args.translate_to
        )
        
        # 执行下载
        result = await downloader.download_subtitles(request)
        
        if result.success:
            print(f"✅ 成功下载字幕: {result.video_info.title}")
            print(f"   找到 {len(result.subtitle_tracks)} 个字幕轨道")
            print(f"   保存了 {len(result.downloaded_files)} 个文件")
            print(f"   处理时间: {result.processing_time:.2f}秒")
            
            if result.ai_generated:
                print(f"   使用了AI生成字幕")
            
            for file_path in result.downloaded_files:
                print(f"   📁 {file_path}")
            
            return True
        else:
            print(f"❌ 字幕下载失败: {args.url}")
            for error in result.errors or []:
                print(f"   错误: {error}")
            return False
            
    except Exception as e:
        print(f"❌ 下载失败: {str(e)}")
        return False

async def download_batch(downloader: UniversalSubtitleDownloader, args) -> bool:
    """批量下载字幕"""
    try:
        # 读取URL文件
        batch_file = Path(args.batch)
        if not batch_file.exists():
            print(f"❌ 批量文件不存在: {args.batch}")
            return False
        
        urls = []
        with open(batch_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
        
        if not urls:
            print(f"❌ 批量文件中没有找到有效URL")
            return False
        
        print(f"📝 找到 {len(urls)} 个URL，开始批量下载...")
        
        # 创建下载请求列表
        requests = []
        for url in urls:
            request = DownloadRequest(
                url=url,
                languages=args.languages,
                formats=args.formats,
                enable_ai_fallback=args.ai_fallback,
                ai_model=args.ai_model,
                ai_model_type=args.ai_model_type,
                output_dir=args.output_dir,
                filename_template=args.filename_template,
                quality_filter=args.quality,
                enable_translation=args.translate,
                translation_target=args.translate_to
            )
            requests.append(request)
        
        # 执行批量下载
        results = await downloader.batch_download(requests, args.max_concurrent)
        
        # 统计结果
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_files = sum(len(r.downloaded_files) for r in results)
        
        print(f"\n📊 批量下载完成:")
        print(f"   成功: {successful}/{len(results)}")
        print(f"   失败: {failed}")
        print(f"   总文件: {total_files}")
        
        # 显示失败的URL
        if failed > 0:
            print(f"\n❌ 失败的下载:")
            for i, result in enumerate(results):
                if not result.success:
                    print(f"   {urls[i]}: {result.errors[0] if result.errors else 'Unknown error'}")
        
        return successful > 0
        
    except Exception as e:
        print(f"❌ 批量下载失败: {str(e)}")
        return False

async def show_video_info(downloader: UniversalSubtitleDownloader, url: str):
    """显示视频信息"""
    try:
        video_info = await downloader.get_video_info(url)
        if video_info:
            print(f"\n📹 视频信息:")
            print(f"   标题: {video_info.title}")
            print(f"   时长: {video_info.duration}秒")
            print(f"   作者: {video_info.uploader}")
            print(f"   平台: {video_info.platform}")
            print(f"   观看数: {video_info.view_count}")
            print(f"   上传日期: {video_info.upload_date}")
            print(f"   描述: {video_info.description[:100]}...")
        else:
            print("❌ 无法获取视频信息")
    except Exception as e:
        print(f"❌ 获取视频信息失败: {str(e)}")

async def show_available_subtitles(downloader: UniversalSubtitleDownloader, url: str):
    """显示可用字幕"""
    try:
        info = await downloader.list_available_subtitles(url)
        
        if 'error' in info:
            print(f"❌ 错误: {info['error']}")
            return
        
        print(f"\n📋 可用字幕:")
        
        available = info.get('available_subtitles', [])
        automatic = info.get('automatic_captions', [])
        
        if available:
            print(f"   手动字幕: {', '.join(available)}")
        
        if automatic:
            print(f"   自动字幕: {', '.join(automatic)}")
        
        if not available and not automatic:
            print(f"   没有找到可用字幕")
            
        ai_models = info.get('ai_models_available', {})
        if ai_models:
            print(f"\n🤖 可用AI模型:")
            for model_type, model_info in ai_models.items():
                if model_info.get('available'):
                    print(f"   {model_type}: {model_info.get('description', '')}")
        
    except Exception as e:
        print(f"❌ 获取字幕信息失败: {str(e)}")

def show_supported_info():
    """显示支持的格式和语言"""
    print(f"\n📋 支持的输出格式:")
    for fmt in subtitle_config.SUPPORTED_FORMATS:
        print(f"   {fmt}")
    
    print(f"\n🌍 支持的语言 (部分):")
    common_languages = {
        'zh-CN': '简体中文',
        'zh-TW': '繁体中文',
        'en': '英语',
        'ja': '日语',
        'ko': '韩语',
        'es': '西班牙语',
        'fr': '法语',
        'de': '德语',
        'ru': '俄语',
    }
    
    for code, name in common_languages.items():
        print(f"   {code}: {name}")
    
    print(f"\n   ... 总共支持 {len(subtitle_config.SUPPORTED_LANGUAGES)} 种语言")

async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = 'ERROR' if args.quiet else args.log_level
    if args.debug:
        log_level = 'DEBUG'
    
    setup_logging(log_level)
    
    # 处理信息显示命令
    if args.list_formats or args.list_languages:
        show_supported_info()
        return 0
    
    # 检查输入
    if not args.url and not args.batch:
        print("❌ 错误: 必须指定URL或批量文件")
        parser.print_help()
        return 1
    
    # 初始化下载器
    async with UniversalSubtitleDownloader() as downloader:
        
        # 处理信息查询
        if args.info_only or args.list_subtitles:
            if args.info_only:
                await show_video_info(downloader, args.url)
            
            if args.list_subtitles:
                await show_available_subtitles(downloader, args.url)
            
            return 0
        
        # 执行下载
        success = False
        
        if args.batch:
            success = await download_batch(downloader, args)
        elif args.url:
            success = await download_single(downloader, args)
        
        # 显示统计信息
        stats = downloader.get_stats()
        if stats['total_requests'] > 0:
            print(f"\n📊 总体统计:")
            print(f"   总请求: {stats['total_requests']}")
            print(f"   成功率: {stats['success_rate']:.1%}")
            print(f"   AI生成: {stats['ai_generated_count']}")
            print(f"   平均处理时间: {stats['average_processing_time']:.2f}秒")
        
        return 0 if success else 1

if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序错误: {str(e)}")
        sys.exit(1)