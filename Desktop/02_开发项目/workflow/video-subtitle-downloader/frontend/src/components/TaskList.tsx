import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../config';
import { TaskStatus, TaskStatusColors, TaskStatusLabels, ApiResponse } from '../types';

const API_BASE = config.API_BASE_URL;

interface TaskListProps {
  currentTask?: TaskStatus | null;
  onTaskSelect?: (task: TaskStatus) => void;
}

const TaskList: React.FC<TaskListProps> = ({ currentTask, onTaskSelect }) => {
  const [tasks, setTasks] = useState<TaskStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<string>('all');

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const statusParam = filter === 'all' ? '' : filter;
      const response = await axios.get<ApiResponse<TaskStatus[]>>(`${API_BASE}/tasks${statusParam ? `?status=${statusParam}` : ''}`);
      
      if (response.data.success && response.data.data) {
        setTasks(response.data.data);
      }
    } catch (error: any) {
      console.error('Error fetching tasks:', error);
    }
    setLoading(false);
  };

  const cancelTask = async (taskId: string) => {
    try {
      const response = await axios.delete<ApiResponse>(`${API_BASE}/task/${taskId}`);
      
      if (response.data.success) {
        fetchTasks(); // 刷新任务列表
        alert('任务已取消');
      }
    } catch (error: any) {
      console.error('Error cancelling task:', error);
      alert(error.response?.data?.detail || '取消任务失败');
    }
  };

  useEffect(() => {
    fetchTasks();
    // 每5秒刷新一次任务列表
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, [filter]);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const formatDuration = (startStr?: string, endStr?: string) => {
    if (!startStr || !endStr) return '';
    
    const start = new Date(startStr);
    const end = new Date(endStr);
    const duration = end.getTime() - start.getTime();
    
    if (duration < 1000) return '<1秒';
    if (duration < 60000) return `${Math.round(duration / 1000)}秒`;
    return `${Math.round(duration / 60000)}分钟`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'running': return '🔄';
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'cancelled': return '🚫';
      default: return '❓';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">📋 任务管理</h2>
        <div className="flex gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="all">全部任务</option>
            <option value="pending">等待中</option>
            <option value="running">运行中</option>
            <option value="completed">已完成</option>
            <option value="failed">失败</option>
            <option value="cancelled">已取消</option>
          </select>
          <button
            onClick={fetchTasks}
            disabled={loading}
            className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 text-sm"
          >
            {loading ? '刷新中...' : '刷新'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p className="text-gray-500">加载中...</p>
        </div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>暂无任务</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {tasks.map((task) => (
            <div
              key={task.task_id}
              className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                currentTask?.task_id === task.task_id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
              onClick={() => onTaskSelect?.(task)}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{getStatusIcon(task.status)}</span>
                  <span className={`font-medium ${TaskStatusColors[task.status as keyof typeof TaskStatusColors]}`}>
                    {TaskStatusLabels[task.status as keyof typeof TaskStatusLabels]}
                  </span>
                  <span className="text-xs text-gray-500">
                    #{task.task_id.slice(-8)}
                  </span>
                </div>
                
                {task.status === 'running' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      cancelTask(task.task_id);
                    }}
                    className="text-red-500 hover:text-red-700 text-sm"
                  >
                    取消
                  </button>
                )}
              </div>

              <div className="text-sm text-gray-600 mb-2">
                {task.message}
              </div>

              {task.status === 'running' && (
                <div className="mb-2">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>进度</span>
                    <span>{task.progress.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${task.progress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <div className="text-xs text-gray-500 space-y-1">
                <div>创建：{formatDate(task.created_at)}</div>
                {task.started_at && (
                  <div>开始：{formatDate(task.started_at)}</div>
                )}
                {task.completed_at && (
                  <div>
                    完成：{formatDate(task.completed_at)}
                    {task.started_at && (
                      <span className="ml-2">
                        (耗时: {formatDuration(task.started_at, task.completed_at)})
                      </span>
                    )}
                  </div>
                )}
              </div>

              {task.error && (
                <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                  错误: {task.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TaskList;