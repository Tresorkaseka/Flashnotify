"""
Système de files d'attente pour le traitement asynchrone
"""
import asyncio
import threading
import time
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Coroutine
from dataclasses import dataclass, field
from enum import Enum
import uuid

from core.notification_system import AcademicNotifier, EmergencyType, Priority
from models import db, User, Notification, PerformanceMetric


class TaskStatus(Enum):
    """Statut des tâches dans la file d'attente"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class QueuedTask:
    """Tâche dans la file d'attente"""
    id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0  # 0 = basse, 1 = normale, 2 = haute


class NotificationTask:
    """Tâche spécialisée pour les notifications"""
    
    def __init__(self, user_id: int, title: str, body: str, emergency_type: str = "académique"):
        self.user_id = user_id
        self.title = title
        self.body = body
        self.emergency_type = emergency_type
        self.id = str(uuid.uuid4())
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'title': self.title,
            'body': self.body,
            'emergency_type': self.emergency_type,
            'id': self.id
        }
    
    @classmethod
    def from_dict(cls, data):
        task = cls(
            user_id=data['user_id'],
            title=data['title'],
            body=data['body'],
            emergency_type=data['emergency_type']
        )
        task.id = data.get('id', str(uuid.uuid4()))
        return task


class AsyncQueue:
    """File d'attente asynchrone"""
    
    def __init__(self, max_workers: int = 5):
        self.queue = asyncio.PriorityQueue()
        self.tasks: Dict[str, QueuedTask] = {}
        self.max_workers = max_workers
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.notifier = AcademicNotifier()
    
    async def start(self):
        """Démarre les workers"""
        if self.running:
            return
        
        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]
        logging.info(f"File d'attente asynchrone démarrée avec {self.max_workers} workers")
    
    async def stop(self):
        """Arrête les workers"""
        if not self.running:
            return
        
        self.running = False
        
        # Arrête les workers
        for worker in self.workers:
            worker.cancel()
        
        # Attend la fin des workers
        for worker in self.workers:
            try:
                await worker
            except asyncio.CancelledError:
                pass
        
        logging.info("File d'attente asynchrone arrêtée")
    
    async def _worker(self, worker_id: int):
        """Worker asynchrone"""
        while self.running:
            try:
                # Récupère une tâche de la file
                priority, task_id = await asyncio.wait_for(
                    self.queue.get(), 
                    timeout=1.0
                )
                
                if task_id not in self.tasks:
                    continue
                
                task = self.tasks[task_id]
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                logging.info(f"Worker {worker_id} exécute la tâche {task_id}")
                
                try:
                    # Exécute la tâche
                    task.result = await task.func(*task.args, **task.kwargs)
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    
                    logging.info(f"Worker {worker_id} a complété la tâche {task_id}")
                
                except Exception as e:
                    task.error = str(e)
                    task.retry_count += 1
                    
                    if task.retry_count < task.max_retries:
                        task.status = TaskStatus.RETRYING
                        # Remet la tâche en file avec une priorité plus élevée
                        await self.queue.put((-1, task_id))
                        logging.warning(f"Worker {worker_id} - Tâche {task_id} échouée, nouvelle tentative ({task.retry_count}/{task.max_retries})")
                    else:
                        task.status = TaskStatus.FAILED
                        task.completed_at = datetime.now()
                        logging.error(f"Worker {worker_id} - Tâche {task_id} échouée définitivement après {task.max_retries} tentatives")
                
                finally:
                    self.queue.task_done()
            
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Erreur worker {worker_id}: {e}")
    
    async def enqueue(self, func: Callable, *args, priority: int = 0, max_retries: int = 3, **kwargs) -> str:
        """Ajoute une tâche à la file"""
        task_id = str(uuid.uuid4())
        task = QueuedTask(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        await self.queue.put((-priority, task_id))  # Priorité inversée pour PriorityQueue
        
        logging.info(f"Tâche {task_id} ajoutée à la file avec priorité {priority}")
        return task_id
    
