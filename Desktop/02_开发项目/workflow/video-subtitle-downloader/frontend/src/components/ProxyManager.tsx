import React, { useState } from 'react';
import axios from 'axios';
import config from '../config';
import { ProxyRequest, ApiResponse } from '../types';

const API_BASE = config.API_BASE_URL;

interface ProxyManagerProps {
  onProxyAdded?: () => void;
}

const ProxyManager: React.FC<ProxyManagerProps> = ({ onProxyAdded }) => {
  const [proxyUrl, setProxyUrl] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{working: boolean; message: string} | null>(null);

  const addProxy = async () => {
    if (!proxyUrl.trim()) return;

    setIsAdding(true);
    try {
      const response = await axios.post<ApiResponse>(`${API_BASE}/proxy/add`, {
        proxy_url: proxyUrl
      } as ProxyRequest);

      if (response.data.success) {
        alert('代理添加成功！');
        setProxyUrl('');
        onProxyAdded?.();
      } else {
        alert('代理添加失败：' + (response.data.error || '未知错误'));
      }
    } catch (error: any) {
      console.error('Error adding proxy:', error);
      alert(error.response?.data?.detail || error.message || '代理添加失败');
    }
    setIsAdding(false);
  };

  const testProxy = async () => {
    if (!proxyUrl.trim()) return;

    setIsTesting(true);
    setTestResult(null);
    
    try {
      const response = await axios.post<ApiResponse<{working: boolean; message: string}>>(`${API_BASE}/proxy/test`, {
        proxy_url: proxyUrl
      } as ProxyRequest);

      if (response.data.success && response.data.data) {
        setTestResult(response.data.data);
      }
    } catch (error: any) {
      console.error('Error testing proxy:', error);
      setTestResult({
        working: false,
        message: error.response?.data?.detail || error.message || '测试失败'
      });
    }
    setIsTesting(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">🔒 代理服务器管理</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            代理服务器地址
          </label>
          <input
            type="url"
            value={proxyUrl}
            onChange={(e) => setProxyUrl(e.target.value)}
            placeholder="http://proxy.example.com:8080 或 socks5://user:pass@proxy.com:1080"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            支持HTTP/HTTPS/SOCKS5代理，格式：协议://[用户名:密码@]主机:端口
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={testProxy}
            disabled={isTesting || !proxyUrl.trim()}
            className="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 disabled:opacity-50 font-medium"
          >
            {isTesting ? '测试中...' : '测试连接'}
          </button>
          
          <button
            onClick={addProxy}
            disabled={isAdding || !proxyUrl.trim()}
            className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 font-medium"
          >
            {isAdding ? '添加中...' : '添加代理'}
          </button>
        </div>

        {testResult && (
          <div className={`p-3 rounded-md ${
            testResult.working ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            <div className="flex items-center">
              <span className="mr-2">
                {testResult.working ? '✅' : '❌'}
              </span>
              <span>{testResult.message}</span>
            </div>
          </div>
        )}

        <div className="text-sm text-gray-600">
          <h3 className="font-medium mb-2">使用说明：</h3>
          <ul className="space-y-1 text-xs">
            <li>• 代理服务器用于绕过地理限制和访问限制</li>
            <li>• 建议使用高质量的代理以确保下载稳定性</li>
            <li>• 系统会自动轮换使用添加的代理服务器</li>
            <li>• 免费代理可能不稳定，付费代理通常更可靠</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ProxyManager;