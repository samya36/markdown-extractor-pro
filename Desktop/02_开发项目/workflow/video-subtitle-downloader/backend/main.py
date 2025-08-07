import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from downloader import VideoSubtitleDownloader

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

app = FastAPI(title="视频字幕下载器 API")

# CORS 配置 - 生产环境应限制具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 仅允许前端域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # 仅允许需要的HTTP方法
    allow_headers=["*"],
)

# 全局下载器实例
downloader = VideoSubtitleDownloader()

class VideoRequest(BaseModel):
    url: str
    languages: list = ["zh-CN", "en"]

@app.get("/")
async def root():
    logger.info("Health check endpoint accessed")
    return {
        "message": "视频字幕下载器 API", 
        "status": "running",
        "timestamp": datetime.now().isoformat()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
