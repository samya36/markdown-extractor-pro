import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../config';
import { SystemStats, ApiResponse } from '../types';

const API_BASE = config.API_BASE_URL;

const SystemStatsComponent: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [sites, setSites] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [statsResponse, sitesResponse] = await Promise.all([
        axios.get<ApiResponse<SystemStats>>(`${API_BASE}/stats`),
        axios.get<ApiResponse<string[]>>(`${API_BASE}/sites`)
      ]);

      if (statsResponse.data.success && statsResponse.data.data) {
        setStats(statsResponse.data.data);
      }

      if (sitesResponse.data.success && sitesResponse.data.data) {
        setSites(sitesResponse.data.data.slice(0, 20)); // 只显示前20个
      }
    } catch (error: any) {
      console.error('Error fetching stats:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchStats();
    // 每30秒刷新一次统计信息
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            <div className="h-3 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">📊 系统状态</h2>
        <button
          onClick={fetchStats}
          disabled={loading}
          className="px-3 py-1 bg-gray-500 text-white rounded-md hover:bg-gray-600 disabled:opacity-50 text-sm"
        >
          {loading ? '刷新中...' : '刷新'}
        </button>
      </div>

      {stats && (
        <div className="space-y-6">
          {/* 任务统计 */}
          <div>
            <h3 className="font-medium text-gray-700 mb-3">🔄 任务统计</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.tasks.total_tasks}
                </div>
                <div className="text-sm text-blue-700">总任务数</div>
              </div>
              <div className="bg-green-50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {stats.tasks.running_tasks}
                </div>
                <div className="text-sm text-green-700">运行中</div>
              </div>
              <div className="bg-purple-50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {stats.tasks.max_concurrent}
                </div>
                <div className="text-sm text-purple-700">最大并发</div>
              </div>
              <div className="bg-orange-50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {stats.download_files}
                </div>
                <div className="text-sm text-orange-700">下载文件数</div>
              </div>
            </div>
          </div>

          {/* 任务状态分布 */}
          {Object.keys(stats.tasks.status_breakdown).length > 0 && (
            <div>
              <h3 className="font-medium text-gray-700 mb-3">📈 任务状态分布</h3>
              <div className="space-y-2">
                {Object.entries(stats.tasks.status_breakdown).map(([status, count]) => (
                  <div key={status} className="flex justify-between items-center">
                    <span className="text-sm capitalize">{status}</span>
                    <div className="flex items-center">
                      <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{
                            width: `${stats.tasks.total_tasks > 0 ? (count / stats.tasks.total_tasks) * 100 : 0}%`
                          }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 支持的网站 */}
          {sites.length > 0 && (
            <div>
              <h3 className="font-medium text-gray-700 mb-3">🌐 支持的网站 (部分)</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {sites.map((site, index) => (
                  <div key={index} className="bg-gray-50 px-3 py-1 rounded text-gray-700">
                    {site}
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                显示前20个支持的网站，实际支持数百个视频平台
              </p>
            </div>
          )}

          {/* 存储信息 */}
          <div>
            <h3 className="font-medium text-gray-700 mb-3">💾 存储信息</h3>
            <div className="text-sm text-gray-600">
              <div>下载目录: <code className="bg-gray-100 px-2 py-1 rounded text-xs">{stats.download_dir}</code></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemStatsComponent;