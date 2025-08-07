import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import config from './config';
import { VideoInfo, TaskStatus, ApiResponse } from './types';

const API_BASE = config.API_BASE_URL;

function App() {
  const [url, setUrl] = useState('');
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [currentTask, setCurrentTask] = useState<TaskStatus | null>(null);
  const [loading, setLoading] = useState(false);
  
  // 配置选项
  const [languages, setLanguages] = useState(['zh-CN', 'en']);
  const [formats, setFormats] = useState(['srt', 'txt', 'raw']);
  const [useAI, setUseAI] = useState(true);
  const [downloadVideo, setDownloadVideo] = useState(false);

  const getVideoInfo = async () => {
    if (!url.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post<ApiResponse<VideoInfo>>(`${API_BASE}/video/info`, { url });
      if (response.data.success && response.data.data) {
        setVideoInfo(response.data.data);
      } else {
        throw new Error(response.data.error || '获取视频信息失败');
      }
    } catch (error: any) {
      console.error('Error fetching video info:', error);
      alert(error.response?.data?.detail || error.message || '获取视频信息失败');
    }
    setLoading(false);
  };

  const startDownload = async () => {
    setLoading(true);
    try {
      const response = await axios.post<{task_id: string}>(`${API_BASE}/download/start`, {
        url,
        languages,
        formats,
        use_ai: useAI,
        download_video: downloadVideo
      });
      
      const taskId = response.data.task_id;
      setCurrentTask({ 
        task_id: taskId, 
        status: 'started', 
        progress: 0, 
        message: '开始处理...',
        results: {}
      });
      
      // 轮询任务状态
      pollTaskStatus(taskId);
      
    } catch (error: any) {
      console.error('Error starting download:', error);
      alert(error.response?.data?.detail || error.message || '启动下载失败');
    }
    setLoading(false);
  };

  const pollTaskStatus = async (taskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get<ApiResponse<TaskStatus>>(`${API_BASE}/task/${taskId}`);
        const taskData = response.data.data;
        setCurrentTask(taskData);
        
        if (taskData.status === 'completed' || taskData.status === 
'error') {
          clearInterval(pollInterval);
        }
      } catch (error: any) {
        console.error('Error polling task status:', error);
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  const downloadFile = (filename: string) => {
    window.open(`${API_BASE}/download/file/${filename}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
          🎬 视频字幕下载器
        </h1>
        
        {/* URL 输入区域 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            视频链接
          </label>
          <div className="flex gap-4">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="输入 YouTube、B站等视频链接..."
              className="flex-1 px-3 py-2 border border-gray-300 
rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={getVideoInfo}
              disabled={loading || !url.trim()}
              className="px-6 py-2 bg-blue-500 text-white rounded-md 
hover:bg-blue-600 disabled:opacity-50"
            >
              获取信息
            </button>
          </div>
        </div>

        {/* 视频信息显示 */}
        {videoInfo && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">视频信息</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p><strong>标题:</strong> {videoInfo.title}</p>
                <p><strong>作者:</strong> {videoInfo.uploader}</p>
              </div>
              <div>
                <p><strong>时长:</strong> {Math.floor(videoInfo.duration / 
60)}:{(videoInfo.duration % 60).toFixed(0).padStart(2, '0')}</p>
                <p><strong>现有字幕:</strong> {videoInfo.has_subtitles ? 
'有' : '无'}</p>
              </div>
            </div>
            {videoInfo.available_subtitles.length > 0 && (
              <p className="mt-2"><strong>可用语言:</strong> 
{videoInfo.available_subtitles.join(', ')}</p>
            )}
          </div>
        )}

        {/* 下载配置 */}
        {videoInfo && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">下载配置</h2>
            
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 
mb-2">
                  字幕语言
                </label>
                <div className="space-y-2">
                  {['zh-CN', 'zh', 'en', 'ja', 'ko'].map(lang => (
                    <label key={lang} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={languages.includes(lang)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setLanguages([...languages, lang]);
                          } else {
                            setLanguages(languages.filter(l => l !== 
lang));
                          }
                        }}
                        className="mr-2"
                      />
                      {lang}
                    </label>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 
mb-2">
                  输出格式
                </label>
                <div className="space-y-2">
                  {['srt', 'txt', 'raw'].map(format => (
                    <label key={format} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formats.includes(format)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormats([...formats, format]);
                          } else {
                            setFormats(formats.filter(f => f !== format));
                          }
                        }}
                        className="mr-2"
                      />
                      {format.toUpperCase()}
                    </label>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="mt-4 space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={useAI}
                  onChange={(e) => setUseAI(e.target.checked)}
                  className="mr-2"
                />
                启用 AI 字幕生成（无现有字幕时）
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={downloadVideo}
                  onChange={(e) => setDownloadVideo(e.target.checked)}
                  className="mr-2"
                />
                下载完整视频（带字幕）
              </label>
            </div>
            
            <button
              onClick={startDownload}
              disabled={loading}
              className="mt-6 w-full py-3 bg-green-500 text-white 
rounded-md hover:bg-green-600 disabled:opacity-50 font-semibold"
            >
              开始下载
            </button>
          </div>
        )}

        {/* 任务进度 */}
        {currentTask && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">下载进度</h2>
            
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 
mb-1">
                <span>{currentTask.message}</span>
                <span>{currentTask.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all 
duration-300"
                  style={{ width: `${currentTask.progress}%` }}
                ></div>
              </div>
            </div>
            
            <p className="text-sm text-gray-600">
              状态: <span className={`font-semibold ${
                currentTask.status === 'completed' ? 'text-green-600' :
                currentTask.status === 'error' ? 'text-red-600' : 
'text-blue-600'
              }`}>{currentTask.status}</span>
            </p>
            
            {/* 下载结果 */}
            {currentTask.status === 'completed' && currentTask.results && 
(
              <div className="mt-6">
                <h3 className="font-semibold mb-3">下载结果</h3>
                
                {currentTask.results.existing_subtitles && 
Object.keys(currentTask.results.existing_subtitles).length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium mb-2">现有字幕:</h4>
                    <div className="space-y-2">
                      
{Object.entries(currentTask.results.existing_subtitles).map(([lang, file]: 
[string, any]) => (
                        <button
                          key={lang}
                          onClick={() => 
downloadFile(file.split('/').pop())}
                          className="block w-full text-left p-2 bg-gray-50 
hover:bg-gray-100 rounded border"
                        >
                          📄 {lang} 字幕
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                
                {currentTask.results.ai_subtitles && (
                  <div className="mb-4">
                    <h4 className="font-medium mb-2">AI 生成字幕 
({currentTask.results.ai_subtitles.language}):</h4>
                    <div className="space-y-2">
                      
{Object.entries(currentTask.results.ai_subtitles.formats).map(([format, 
file]: [string, any]) => (
                        <button
                          key={format}
                          onClick={() => 
downloadFile(file.split('/').pop())}
                          className="block w-full text-left p-2 bg-gray-50 
hover:bg-gray-100 rounded border"
                        >
                          📄 {format.toUpperCase()} 格式
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                
                {currentTask.results.video_file && (
                  <div>
                    <h4 className="font-medium mb-2">完整视频:</h4>
                    <button
                      onClick={() => 
downloadFile(currentTask.results.video_file.split('/').pop())}
                      className="block w-full text-left p-2 bg-blue-50 
hover:bg-blue-100 rounded border border-blue-200"
                    >
                      🎬 带字幕的完整视频
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
