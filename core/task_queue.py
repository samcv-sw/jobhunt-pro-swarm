# ──────────────────────────────────────────────────────────────────────────────
# task_queue.py - Async Task Queue Management
# Manages background jobs using procrastinate (PostgreSQL-backed)
# ──────────────────────────────────────────────────────────────────────────────

import logging
import asyncio
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


class TaskResult:
    """Result of task execution."""
    
    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        attempts: int = 1,
    ):
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error
        self.started_at = started_at
        self.completed_at = completed_at
        self.attempts = attempts
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "attempts": self.attempts,
        }


class TaskQueue:
    """Task queue manager for background jobs."""
    
    def __init__(self):
        self._tasks: Dict[str, TaskResult] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._retry_config = {
            "max_retries": 3,
            "backoff_base": 2,  # Exponential backoff multiplier
            "initial_delay": 5,  # seconds
        }
    
    async def enqueue(
        self,
        task_id: str,
        func: Callable,
        *args,
        delay: int = 0,
        max_retries: int = 3,
        **kwargs
    ) -> TaskResult:
        """Add task to queue."""
        try:
            logger.info(f"Enqueuing task: {task_id}")
            
            # If delay specified, schedule for later
            if delay > 0:
                status = TaskStatus.SCHEDULED
                logger.info(f"Task {task_id} scheduled in {delay}s")
            else:
                status = TaskStatus.PENDING
            
            result = TaskResult(
                task_id=task_id,
                status=status,
                attempts=0,
            )
            self._tasks[task_id] = result
            
            # If no delay, execute immediately
            if delay == 0:
                await self._execute_task(task_id, func, args, kwargs, max_retries)
            else:
                # Schedule for later
                asyncio.create_task(
                    self._scheduled_execution(task_id, func, args, kwargs, delay, max_retries)
                )
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_id}: {e}")
            result = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e),
            )
            self._tasks[task_id] = result
            return result
    
    async def _execute_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple,
        kwargs: dict,
        max_retries: int,
    ) -> None:
        """Execute a task with retry logic."""
        result = self._tasks.get(task_id)
        if not result:
            return
        
        for attempt in range(max_retries + 1):
            try:
                result.attempts = attempt + 1
                result.status = TaskStatus.RUNNING
                result.started_at = datetime.utcnow()
                
                logger.info(f"Executing task {task_id} (attempt {attempt + 1}/{max_retries + 1})")
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    task_result = await func(*args, **kwargs)
                else:
                    task_result = func(*args, **kwargs)
                
                # Mark as completed
                result.status = TaskStatus.COMPLETED
                result.result = task_result
                result.completed_at = datetime.utcnow()
                
                logger.info(
                    f"Task {task_id} completed in {result.duration_seconds:.2f}s"
                )
                
                # Call success callbacks
                await self._trigger_callbacks(task_id, "success", result)
                return
            
            except Exception as e:
                result.error = str(e)
                logger.error(f"Task {task_id} failed (attempt {attempt + 1}): {e}")
                
                # Retry if not last attempt
                if attempt < max_retries:
                    delay = self._retry_config["initial_delay"] * (
                        self._retry_config["backoff_base"] ** attempt
                    )
                    logger.info(f"Retrying task {task_id} in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    result.status = TaskStatus.FAILED
                    result.completed_at = datetime.utcnow()
                    
                    # Call error callbacks
                    await self._trigger_callbacks(task_id, "error", result)
    
    async def _scheduled_execution(
        self,
        task_id: str,
        func: Callable,
        args: tuple,
        kwargs: dict,
        delay: int,
        max_retries: int,
    ) -> None:
        """Execute task after delay."""
        await asyncio.sleep(delay)
        self._tasks[task_id].status = TaskStatus.PENDING
        await self._execute_task(task_id, func, args, kwargs, max_retries)
    
    def get_task(self, task_id: str) -> Optional[TaskResult]:
        """Get task result."""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskResult]:
        """Get all tasks, optionally filtered by status."""
        if status:
            return [t for t in self._tasks.values() if t.status == status]
        return list(self._tasks.values())
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self._tasks.get(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.SCHEDULED]:
            task.status = TaskStatus.CANCELLED
            logger.info(f"Task {task_id} cancelled")
            return True
        return False
    
    def register_callback(
        self,
        task_id: str,
        event: str,  # "success" or "error"
        callback: Callable,
    ) -> None:
        """Register callback for task events."""
        if task_id not in self._callbacks:
            self._callbacks[task_id] = []
        self._callbacks[task_id].append((event, callback))
    
    async def _trigger_callbacks(
        self,
        task_id: str,
        event: str,
        result: TaskResult,
    ) -> None:
        """Trigger registered callbacks."""
        if task_id not in self._callbacks:
            return
        
        for event_type, callback in self._callbacks[task_id]:
            if event_type == event:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(result)
                    else:
                        callback(result)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def get_stats(self) -> dict:
        """Get queue statistics."""
        tasks = self._tasks.values()
        
        return {
            "total_tasks": len(tasks),
            "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "scheduled": sum(1 for t in tasks if t.status == TaskStatus.SCHEDULED),
            "cancelled": sum(1 for t in tasks if t.status == TaskStatus.CANCELLED),
            "avg_duration_seconds": self._calculate_avg_duration(tasks),
        }
    
    @staticmethod
    def _calculate_avg_duration(tasks) -> float:
        """Calculate average task duration."""
        completed = [t for t in tasks if t.duration_seconds is not None]
        if not completed:
            return 0
        return sum(t.duration_seconds for t in completed) / len(completed)
    
    def clear(self) -> None:
        """Clear all tasks."""
        self._tasks.clear()
        self._callbacks.clear()
        logger.info("Task queue cleared")


# Global task queue instance
task_queue = TaskQueue()


# Example background tasks
async def send_email_async(to: str, subject: str, body: str) -> dict:
    """Example async email task."""
    logger.info(f"Sending email to {to}")
    await asyncio.sleep(1)  # Simulate email sending
    return {"email_sent": to, "subject": subject}


async def generate_report_async(report_id: int) -> dict:
    """Example async report generation."""
    logger.info(f"Generating report {report_id}")
    await asyncio.sleep(2)  # Simulate report generation
    return {"report_id": report_id, "status": "generated"}


async def process_batch_async(batch_id: str, items: list) -> dict:
    """Example async batch processing."""
    logger.info(f"Processing batch {batch_id}")
    for item in items:
        await asyncio.sleep(0.1)  # Simulate processing
    return {"batch_id": batch_id, "processed_items": len(items)}


# Usage in FastAPI:
# 
# @app.post("/api/tasks/send-email")
# async def send_email(email_request: EmailRequest):
#     result = await task_queue.enqueue(
#         task_id=f"email_{uuid.uuid4()}",
#         func=send_email_async,
#         to=email_request.to,
#         subject=email_request.subject,
#         body=email_request.body,
#     )
#     return {"task_id": result.task_id, "status": result.status.value}
#
# @app.get("/api/tasks/{task_id}")
# async def get_task_status(task_id: str):
#     result = task_queue.get_task(task_id)
#     if result:
#         return result.to_dict()
#     return {"error": "Task not found"}
