import logging
from models.descriptors import ValidatedString, PriorityDescriptor, TimestampDescriptor, StatusDescriptor, \
    DataDescriptor
from models.exceptions import InvalidIDError, InvalidStatusError
from typing import Any, Dict
import datetime, time


logger = logging.getLogger(__name__)


class Task:
    """
    Модель задачи с валидацией через дескрипторы
    Атрибуты:
        id: уникальный идентификатор задачи
        description: описание задачи
        priority: приоритет задачи с именованными уровнями
        status: статус задачи с проверкой перехода
        created_at: время создания (автоматически)
        payload: произвольные данные задачи

    Вычисляет:
        is_ready: готовность к выполнению
        age: возраст задачи
        priority_name: название уровня приоритета
        is_completed: завершена ли задача
    """


    id = ValidatedString(min_len=1, max_len=50, nullable=False,
                         error_class=InvalidIDError)
    description = ValidatedString(min_len=3, max_len=500, nullable=False)
    priority = PriorityDescriptor()
    created_at = TimestampDescriptor(auto=True)
    status = StatusDescriptor()
    payload = DataDescriptor()

    def __init__(self, id: str, description: str,
                 priority: int = 2, status: str = 'pending',
                 payload: Any = None):
        self.id = id
        self.description = description
        self.priority = priority
        if status not in StatusDescriptor.STATUSES:
            raise InvalidStatusError(f"Неверный начальный статус: {status}")
        self.__dict__['status'] = status
        self._payload = payload or {}
        logger.info(f"Создана задача {id}: {description[:50]}...")

    def __setattr__(self, name: str, value: Any):
        """Перехват установки атрибутов для логирования"""
        logger.debug(f"Установка атрибута {name} = {value}")
        super().__setattr__(name, value)

    def __repr__(self):
        return (f"Task(id='{self.id}',"
                f"priority={self.priority['value']},"
                f"status='{self.status}')")

    def __str__(self) -> str:
        return (f'Задача #{self.id}: {self.description[:50]}...'
                f'[{self.priority_name}, {self.status}]')

    @property
    def is_ready(self) -> bool:
        """Вычисляет готова ли задача"""
        return self.status not in ['completed', 'canceled']

    @property
    def age(self) -> float:
        'Возраст задачи в секундах'
        if self.created_at is None:
            return 0.0
        return time.time() - self.created_at

    @property
    def age_formatted(self) -> str:
        '''Форматированное представление возраста задачи'''
        age_sec = self.age
        if age_sec < 60:
            return f"{age_sec} сек."
        elif age_sec < 3600:
            return f"{age_sec/60:.1f} мин."
        else:
            return f"{age_sec/3600:.1f} ч."

    @property
    def priority_name(self) -> str:
        '''Название уровня приоритета'''
        return self.priority['name']

    @property
    def is_completed(self) -> bool:
        """Проверка завершенности задачи"""
        return self.status == 'completed'

    def upd_status(self, new: str) -> bool:
        """
        Обновление статуса с проверкой перехода
        Параметры: new - новый статус
        Вернет: True при изменении статуса, иначе - False
        """
        old = self.status

        status_desc = getattr(self.__class__, 'status')
        status_desc.transition(old, new)

        if old != new:
            self.__dict__['status'] = new
            logger.info(f'Статус задачи {self.id} изменен: {old} -> {new}')
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        '''Экспорт задачи в словарь'''
        return {
            'id': self.id,
            'description': self.description,
            'priority': self.priority['value'],
            'priority_name': self.priority_name,
            'status': self.status,
            'created_at': self.created_at,
            'created_at_iso': datetime.fromtimestamp(self.created_at).isoformat()
            if self.created_at else None,
            'age_seconds': self.age,
            'age_formatted': self.age_formatted,
            'is_ready': self.is_ready,
            'is_completed': self.is_completed,
            'payload': self.payload
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        '''Создание задачи из словаря'''
        task = cls(
            id=data['id'],
            description=data['description'],
            priority=data.get('priority', 2),
            status=data.get('status', 'pending'),
            payload=data.get('payload', {})
        )

        if 'created_at' in data and data['created_at']:
            task.created_at = data['created_at']

        return task


#разница между data и non-data дескрипторами
if __name__ == '__main__':
    task = Task(id='TASK-007', description='test', priority=3)

    print("Демонстрация работы дескрипторов")
    print(f"Задача: {task}")
    print(f"Приоритет (data descriptor): {task.priority}")
    print(f"Статус (non-data descriptor): {task.status}")
    print(f"Готовность (property): {task.is_ready}")
    print(f"Возраст (property): {task.age_formatted}")

    # Изменяем статус
    print("\n=== Изменение статуса ===")
    task.upd_status('running')
    print(f"Новый статус: {task.status}")

    # Пробуем недопустимый переход
    try:
        task.upd_status('pending')  # Нельзя вернуться в pending
    except InvalidStatusError as e:
        print(f"Ошибка: {e}")

    # Демонстрация разницы descriptors
    print("\n=== Data vs Non-data descriptors ===")
    print("Data descriptor (priority):")
    print(f"  - Есть __set__ и __get__")
    print(f"  - Значение хранится в дескрипторе: {task.priority}")

    print("\nNon-data descriptor (status):")
    print(f"  - Только __get__")
    print(f"  - Значение в __dict__: {task.__dict__['status']}")
    print(f"  - Доступ через дескриптор: {task.status}")

    # Демонстрация property
    print("\n=== Property ===")
    print(f"is_ready: {task.is_ready}")
    print(f"age_formatted: {task.age_formatted}")