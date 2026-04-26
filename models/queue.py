import logging
from typing import Iterator, List, Optional, Callable, Any
from collections import deque

from models.task import Task
from models.exceptions import InvalidStatusError
from models.descriptors import StatusDescriptor

logger = logging.getLogger(__name__)


class TaskQueue:
    """
    Очередь задач с поддержкой итераций, фильтрацией и ленивыми фильтрами.

    Атрибуты:
        _tasks: хранилище задач
        _iter_indexЖ: индекс (для итерации и повторного обхода)
    """

    def __init__(self, tasks: Optional[List[Task]] = None):
        """Инициализация очереди"""
        self._tasks = deque(tasks if tasks else [])
        self._iter_index = 0
        logger.info(f"Создана TaskQueue с {len(self._tasks)} задачами")

    def push(self, task: Task) -> None:
        """Добавить задачу в конец очереди"""
        self._tasks.append(task)
        logger.debug(f"Задача {task.id} добавлена в очередь. Всего задач {len(self._tasks)}")

    def pop(self) -> Optional[Task]:
        """Возвращает задачу из начала очереди (удаляет ее из очереди)"""
        if not self._tasks:
            logger.debug('Попытка pop из пустой очереди')
            return None
        task = self._tasks.popleft()
        logger.debug(f'Задача {task.id} извлечена из очереди. Осталось {len(self._tasks)} задач')
        return task

    def peek(self) -> Optional[Task]:
        """Возвращает задачу из начала очерди (не извлекает ее)"""
        if not self._tasks:
            return None
        return self._tasks[0]

    def size(self) -> int:
        """Возвращает количество задач в очереди"""
        return len(self._tasks)

    def is_empty(self) -> bool:
        """Возвращает True если очередь пустая"""
        return len(self._tasks) == 0

    def clear(self) -> None:
        """Очищает очередь"""
        cnt = len(self._tasks)
        self._tasks.clear()
        logger.info(f'Очередь очищена. Удалено {cnt} задач')

    def __len__(self) -> int:
        """Возвращает размер очереди"""
        return self.size()

    def __bool__(self) -> bool:
        """Возвращает True если очередь не пустая"""
        return not self.is_empty()

    def __iter__(self) -> Iterator[Task]:
        """Возвращает итератор для очереди. Поддерживает повторный обход"""
        self._iter_index = 0
        return self

    def __next__(self) -> Task:
        '''Возвращает след. элемент при итерации'''
        if self._iter_index >= len(self._tasks):
            raise StopIteration
        task = self._tasks[self._iter_index]
        self._iter_index += 1
        return task

    def __repr__(self) -> str:
        return f'TaskQueue(size={len(self._tasks)})'

    def __str__(self) -> str:
        if self.is_empty():
            return 'TaskQueue(empty)'
        return f'TaskQueue({len(self._tasks)} tasks: {list(self._tasks)[:3]})'

    def filter_by_status(self, status: str) -> Iterator[Task]:
        """Ленивый фильтр по статусу"""
        if status not in StatusDescriptor.STATUSES:
            raise InvalidStatusError(f'Неверный статус {status}. Допустимые: {StatusDescriptor.STATUSES}')
        logger.debug(f'Ленивая фильтрация по статусу: {status}')
        for task in self._tasks:
            if task.status == status:
                yield task

    def filter_by_priority(self, min_priority: int = 1, max_priority: int = 4) -> Iterator[Task]:
        """Ленивый фильтр по приоритету"""
        if not 1 <= min_priority <= 4:
            raise ValueError(f'min_priority должен быть от 1 до 4, получен: {min_priority}')
        if not 1 <= max_priority <= 4:
            raise ValueError(f'max_priority должен быть от 1 до 4, получен: {max_priority}')
        if min_priority > max_priority:
            raise ValueError(f'min_priority ({min_priority}) > max_priority ({max_priority})')

        logger.debug(f"Ленивая фильтрация по приоритету. min_priority={min_priority}, max_priority={max_priority}")
        for task in self._tasks:
            priority = task.priority['value'] if isinstance(task.priority, dict) else task.priority
            if min_priority <= priority <= max_priority:
                yield task

    def filter_by(self, predicate: Callable[[Task], bool]) -> Iterator[Task]:
        """Ленивая фильтрация с пользовательски предикатом (функция для проверки задач)"""
        logger.debug(f'Ленивая фильтрация с предикатом {predicate}')
        for task in self._tasks:
            if predicate(task):
                yield task

    def extend(self, tasks: List[Task]) -> None:
        """Добавить список задач в очередь"""
        for task in tasks:
            self._tasks.append(task)
        logger.info(f"Добавлено {len(tasks)} задач в очередь. Всего: {len(self._tasks)}")

    def to_list(self) -> List[Task]:
        """Преобразует очередь в список (работает с небольшой очередью)"""
        return list(self._tasks)

    def copy(self) -> 'TaskQueue':
        """Создание копии очереди"""
        return TaskQueue(list(self._tasks))
