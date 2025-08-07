import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import os

from enhanced_downloader import EnhancedVideoSubtitleDownloader
from task_manager import task_manager, TaskStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="增强版视频字幕下载器 API")

# CORS 配置 - 生产环境应限制具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 仅允许前端域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # 添加DELETE方法
    allow_headers=["*"],
)

# 全局下载器实例
downloader = EnhancedVideoSubtitleDownloader()

class VideoRequest(BaseModel):
    url: str
    languages: List[str] = ["zh-CN", "en"]

class DownloadRequest(BaseModel):
    url: str
    languages: List[str] = ["zh-CN", "en"]
    formats: List[str] = ["srt", "txt"]
    use_ai: bool = True
    download_video: bool = False

class ProxyRequest(BaseModel):
    proxy_url: str

@app.get("/")
async def root():
    logger.info("Health check endpoint accessed")
    return {
        "message": "增强版视频字幕下载器 API", 
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": ["YouTube访问限制绕过", "代理支持", "AI字幕生成", "任务队列管理"]
    }

@app.post("/api/video/info")
async def get_video_info(request: VideoRequest):
    logger.info(f"Video info request for URL: {request.url}")
    try:
        info = downloader.get_video_info(request.url)
        logger.info(f"Successfully retrieved info for: {info.get('title', 'Unknown')}")
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Failed to get video info for {request.url}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download/start")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """开始字幕下载任务"""
    logger.info(f"Download request for URL: {request.url}")
    
    try:
        # 创建任务
        task_id = task_manager.create_task("subtitle_download", "Preparing download...")
        
        # 在后台运行下载任务
        success = await task_manager.run_task(
            task_id,
            download_subtitles_task,
            request.url,
            request.languages,
            request.formats,
            request.use_ai,
            request.download_video
        )
        
        if not success:
            raise HTTPException(status_code=503, detail="Server is busy, please try again later")
        
        return {"success": True, "task_id": task_id}
        
    except Exception as e:
        logger.error(f"Failed to start download for {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task_data = task_manager.get_task_dict(task_id)
    
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"success": True, "data": task_data}

@app.delete("/api/task/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    success = await task_manager.cancel_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"success": True, "message": "Task cancelled"}

@app.get("/api/tasks")
async def list_tasks(status: Optional[str] = None):
    """列出所有任务"""
    try:
        task_status = None
        if status:
            task_status = TaskStatus(status)
        
        tasks = task_manager.list_tasks(task_status)
        return {"success": True, "data": tasks}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

@app.get("/api/download/file/{filename}")
async def download_file(filename: str):
    """下载生成的文件"""
    file_path = Path(downloader.download_dir) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.post("/api/proxy/add")
async def add_proxy(request: ProxyRequest):
    """添加代理服务器"""
    logger.info(f"Adding proxy: {request.proxy_url}")
    
    success = downloader.add_proxy(request.proxy_url)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid proxy URL")
    
    return {"success": True, "message": "Proxy added successfully"}

@app.post("/api/proxy/test")
async def test_proxy(request: ProxyRequest):
    """测试代理连接"""
    logger.info(f"Testing proxy: {request.proxy_url}")
    
    success = downloader.test_proxy(request.proxy_url)
    
    return {
        "success": True, 
        "working": success,
        "message": "Proxy is working" if success else "Proxy connection failed"
    }

@app.get("/api/sites")
async def get_supported_sites():
    """获取支持的网站列表"""
    sites = downloader.get_supported_sites()
    return {"success": True, "data": sites}

@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    task_stats = task_manager.get_stats()
    
    # 获取下载目录信息
    download_dir = Path(downloader.download_dir)
    file_count = len(list(download_dir.glob('*'))) if download_dir.exists() else 0
    
    return {
        "success": True,
        "data": {
            "tasks": task_stats,
            "download_files": file_count,
            "download_dir": str(download_dir)
        }
    }

def download_subtitles_task(progress_callback, url: str, languages: List[str], formats: List[str], use_ai: bool, download_video: bool):
    """字幕下载任务函数"""
    try:
        progress_callback(10, "Initializing download...")
        
        # 如果不使用AI，移除AI相关格式
        if not use_ai:
            formats = [f for f in formats if f != 'raw']
        
        progress_callback(20, "Starting subtitle extraction...")
        
        # 执行下载
        result = downloader.download_subtitles(url, languages, formats)
        
        progress_callback(80, "Processing downloaded files...")
        
        # 如果需要下载完整视频
        if download_video:
            progress_callback(90, "Downloading video file...")
            # TODO: 实现视频下载功能
        
        progress_callback(100, "Download completed")
        
        return result
        
    except Exception as e:
        logger.error(f"Download task failed: {str(e)}")
        raise e

# 启动时清理旧任务
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("Starting Enhanced Video Subtitle Downloader API")
    
    # 清理超过24小时的旧任务
    task_manager.cleanup_old_tasks(24)
    
    logger.info("API started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)