export interface VideoInfo {
  title: string;
  duration: number;
  uploader: string;
  view_count?: number;
  has_subtitles: boolean;
  available_subtitles: string[];
  automatic_captions: string[];
}

export interface TaskStatus {
  task_id: string;
  task_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  message: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result?: {
    existing_subtitles?: Record<string, string>;
    ai_subtitles?: {
      language: string;
      formats: Record<string, string>;
    };
    video_info?: VideoInfo;
    download_paths?: string[];
  };
  error?: string;
}

export interface VideoRequest {
  url: string;
  languages?: string[];
}

export interface DownloadRequest extends VideoRequest {
  formats: string[];
  use_ai: boolean;
  download_video: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ProxyRequest {
  proxy_url: string;
}

export interface TaskStats {
  total_tasks: number;
  running_tasks: number;
  max_concurrent: number;
  status_breakdown: Record<string, number>;
}

export interface SystemStats {
  tasks: TaskStats;
  download_files: number;
  download_dir: string;
}

export const TaskStatusColors = {
  pending: 'text-yellow-600',
  running: 'text-blue-600', 
  completed: 'text-green-600',
  failed: 'text-red-600',
  cancelled: 'text-gray-600'
};

export const TaskStatusLabels = {
  pending: '等待中',
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消'
};