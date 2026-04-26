import logging
import asyncio
from typing import Protocol, Any, Dict, runtime_checkable
from abc import abstractmethod

import random

from models.task import Task as DomainTask
logger = logging.getLogger(__name__)


@runtime_checkable
class TaskHandler(Protocol):
    @abstractmethod
    async def handle(self, task: DomainTask) -> Dict[str, Any]:
        ...

    @property
    def name(self) -> str:
        ...


class BaseHandler:
    """Это база. Base"""
    def __init__(self, name: str = None):
        self._name = name or self.__class__.__name__

    @property
    def name(self) -> str:
        return self._name


class PrintHandler(BaseHandler):
    """Простой обработчик (выводит информацию о задачи)"""
    async def handle(self, task: DomainTask) -> Dict[str, Any]:
        logger.info(f'[{self.name}]. Обработка задачи {task.id}')
        print(f'Задача: {task.id}, {task.description}, Приоритет: {task.priority_name}')

        await asyncio.sleep(0.1)

        return {
            'status': 'success',
            'handler': self.name,
            'task_id': task.id,
            'message': f'Задача {task.id} обработана'
        }


class PriorityHandler(BaseHandler):
    async def handle(self, task: DomainTask) -> Dict[str, Any]:
        priority_value = task.priority['value']
        logger.info(f"{self.name} Обработка задачи {task.id} с приоритетом {priority_value}")

        delay  = 0.2 * (5 - priority_value) #элита опять лучше :(
        await asyncio.sleep(delay)

        res = {
            'status': 'success',
            'handler': self.name,
            'task_id': task.id,
            'priority': priority_value,
            'priority_name': task.priority_name,
            'processing_time': delay,
        }

        if priority_value >= 3:
            res['urgent'] = True
            logger.debug(f'[{self.name}] Высокоприоритетная задача {task.id}')

        return res


class FailingHandler(BaseHandler):
    """Так себе обработчик (ящеры никогда не падают)"""
    def __init__(self, fail_rait: float = 0.3, name: str = None):
        super().__init__(name)
        self.fail_rait = fail_rait

    async def handle(self, task: DomainTask) -> Dict[str, Any]:
        logger.info(f'[{self.name}] обработка задачи {task.id}')
        await asyncio.sleep(0.05)
        if random.random() < self.fail_rait:
            raise ValueError(f'Случайная ошибка при обработке задачи {task.id}')

        return {
            'status': 'success',
            'handler': self.name,
            'task_id': task.id,
        }