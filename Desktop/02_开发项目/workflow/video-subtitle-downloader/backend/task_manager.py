import asyncio
import uuid
import logging
from typing import Dict, Optional, Callable, Any
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    task_id: str
    task_type: str
    status: TaskStatus
    progress: float
    message: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key in ['created_at', 'started_at', 'completed_at']:
            if data[key]:
                data[key] = data[key].isoformat()
        # Convert enum to string
        data['status'] = self.status.value
        return data

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = 3
        self._lock = asyncio.Lock()
        
        logger.info("TaskManager initialized")
    
    def create_task(self, task_type: str, message: str = "Task created") -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            progress=0.0,
            message=message,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        logger.info(f"Created task {task_id} of type {task_type}")
        return task_id
    
    async def run_task(self, task_id: str, task_func: Callable, *args, **kwargs) -> bool:
        """运行任务"""
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        task = self.tasks[task_id]
        
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            logger.warning(f"Max concurrent tasks reached, task {task_id} will wait")
            task.message = "Waiting for available slot..."
            return False
        
        async with self._lock:
            if task_id in self.running_tasks:
                logger.warning(f"Task {task_id} is already running")
                return False
            
            # 创建异步任务
            async_task = asyncio.create_task(self._execute_task(task_id, task_func, *args, **kwargs))
            self.running_tasks[task_id] = async_task
        
        return True
    
    async def _execute_task(self, task_id: str, task_func: Callable, *args, **kwargs):
        """执行任务的内部方法"""
        task = self.tasks[task_id]
        
        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.message = "Task started"
            task.progress = 0.0
            
            logger.info(f"Starting task {task_id}")
            
            # 创建进度回调函数
            def progress_callback(progress: float, message: str = ""):
                task.progress = min(100.0, max(0.0, progress))
                if message:
                    task.message = message
                logger.debug(f"Task {task_id} progress: {progress}% - {message}")
            
            # 执行任务函数
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(progress_callback, *args, **kwargs)
            else:
                # 对于同步函数，在线程池中运行
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, task_func, progress_callback, *args, **kwargs)
            
            # 任务完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100.0
            task.result = result
            task.message = "Task completed successfully"
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            # 任务失败
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            task.message = f"Task failed: {str(e)}"
            
            logger.error(f"Task {task_id} failed: {str(e)}")
            
        finally:
            # 清理运行中的任务
            async with self._lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def get_task_dict(self, task_id: str) -> Optional[Dict]:
        """获取任务信息（字典格式）"""
        task = self.get_task(task_id)
        return task.to_dict() if task else None
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Dict]:
        """列出所有任务"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [task for task in tasks if task.status == status]
        
        return [task.to_dict() for task in sorted(tasks, key=lambda t: t.created_at, reverse=True)]
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # 如果任务正在运行，尝试取消
        if task_id in self.running_tasks:
            async_task = self.running_tasks[task_id]
            async_task.cancel()
            
            try:
                await async_task
            except asyncio.CancelledError:
                pass
            
            async with self._lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
        
        # 更新任务状态
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        task.message = "Task cancelled"
        
        logger.info(f"Task {task_id} cancelled")
        return True
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        old_task_ids = []
        for task_id, task in self.tasks.items():
            if task.created_at.timestamp() < cutoff_time and task_id not in self.running_tasks:
                old_task_ids.append(task_id)
        
        for task_id in old_task_ids:
            del self.tasks[task_id]
        
        if old_task_ids:
            logger.info(f"Cleaned up {len(old_task_ids)} old tasks")
    
    def get_stats(self) -> Dict:
        """获取任务统计信息"""
        total = len(self.tasks)
        status_counts = {}
        
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_tasks': total,
            'running_tasks': len(self.running_tasks),
            'max_concurrent': self.max_concurrent_tasks,
            'status_breakdown': status_counts
        }

# 全局任务管理器实例
task_manager = TaskManager()