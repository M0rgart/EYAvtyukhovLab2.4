import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


logger = logging.getLogger(__name__)


@dataclass
class Task:
    '''
    Представляет задачу для обработки.

    Атрибуты:
    id - уникальный идентификатор задача
    payload - данные задачи произвольного типа
    '''
    id: int
    payload: any

    def __repr__(self):
        return f"Task(id={self.id}, payload={self.payload})"


@runtime_checkable
class TaskSource(Protocol):
    '''
    Определяет интерфейс для источников задача
    Методы:
    get_tasks - метод для получения списка задач
    __repr__ - метод для строкового представления

    Поддерживает проверку во время выполнения через runtime_checkable
    '''
    def get_tasks(self) -> list[Task]:
        pass

    def __repr__(self) -> str:
        pass


def check_task_source(task: any) -> bool:
    '''
    Проверяет, является ли объект источником задача, а именно:
    1) является ли он TaskSource
    2) имеет ли метод get_tasks
    Результат логируется
    :param: task - проверяемый объект
    :return: True, если объект TaskSource иначе False
    '''
    if isinstance(task, TaskSource):
        logger.info(f"Объект {task} является TaskSource")
    else:
        logger.warning(f"Объект {task} не является TaskSource")

    if hasattr(task, "get_tasks"):
        logger.info(f"Объект {task} имеет атрибут get_tasks")
    else:
        logger.warning(f"Объект {task} не имеет атрибута get_tasks")

    return isinstance(task, TaskSource)