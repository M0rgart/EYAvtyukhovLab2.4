import time
from typing import Any, Optional
import logging
from .exceptions import (
    InvalidPriorityError,
    InvalidStatusError,
    InvalidDescriptionError
)

logger = logging.getLogger(__name__)


class ValidatedString:
    """
    Data descriptor для валидации строковых атрибутов
    """

    def __init__(self, min_len: int = 1, max_len: int = 255, nullable: bool = False,
                 error_class: Exception = InvalidDescriptionError):
        self.min_len = min_len
        self.max_len = max_len
        self.nullable = nullable
        self.error_class = error_class
        self.data = {}

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.data.get(id(obj), "" if not self.nullable else None)

    def __set__(self, obj, value):
        if value is None:
            if self.nullable:
                self.data[id(obj)] = None
                logger.debug(f"Установленно значение None для {self}")
                return
            else:
                raise self.error_class(f"Значение не может быть None", str(self))

        if not isinstance(value, str):
            raise self.error_class(f"Значение должно быть строкой,"
                                   f"получен {type(value).__name__}", str(self))

        if len(value) < self.min_len:
            raise self.error_class(f"Строка слишком короткая (мин. {self.max_len})", str(self))

        if len(value) > self.max_len:
            raise self.error_class(f"Строка слишком длинная (макс. {self.max_len})", str(self))

        self.data[id(obj)] = value.strip()
        logger.debug(f"Установлено значение '{value}' для {self}")

    def __delete__(self, obj):
        """Запрет на удаление атрибута"""
        raise AttributeError(f"Нельзя удалить атрибут {self}")

    def __repr__(self):
        return f"ValidatedString(min={self.min_len}, max={self.max_len})"


class PositiveInteger:
    """Data descriptor для положительных чисел"""
    def __init__(self, min_value: int = 0, max_value: int = 100,
                 error_class: Exception = InvalidPriorityError):
        self.min_value = min_value
        self.max_value = max_value
        self.error_class = error_class
        self.data = {}

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.data.get(id(obj), self.min_value)

    def __set__(self, obj, value: Any):
        if not isinstance(value, (int, float)):
            raise self.error_class(f'Значение должно быть числом, получен {type(value).__name__}')

        int_value = int(value)
        if int_value < self.min_value:
            raise self.error_class(f"Значение меньше минимального {self.min_value}")
        if int_value > self.max_value:
            raise self.error_class(f"Значение больше максимального {self.max_value}")

        self.data[id(obj)] = int_value
        logger.debug(f"Установленно значение {int_value} для {self}")

    def __delete__(self, obj):
        raise AttributeError(f"Нельзя удалить атрибут {self}")


class PriorityDescriptor(PositiveInteger):
    """Спец. дескриптор для приоритета (с переопределением уровней)"""
    LVL = {
        1: "Low",
        2: "Medium",
        3: "High",
        4: "Critical"
    }

    def __init__(self):
        super().__init__(min_value=1, max_value=4, error_class=InvalidPriorityError)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = super().__get__(obj, objtype)
        return {
            'value': value,
            'name': self.LVL.get(value, 'Unknown')
        }


class StatusDescriptor:
    """Non-data descriptor для статуса задачи"""
    STATUSES = ['pending', 'running', 'completed', 'canceled']
    TRANSITIONS = {
        'pending': ['running', 'canceled'],
        'running': ['completed', 'canceled'],
        'completed': [],
        'canceled': []
    }

    def __init__(self, default: str = 'pending'):
        self.default = default
        self.data = {}

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.data.get(id(obj), self.default)

    def __set_name__(self, owner, name):
        self.name = name

    def transition(self, old: str, new: str):
        if new not in self.STATUSES:
            raise InvalidStatusError(f'Неверный статус {new}. Допустимые: {self.STATUSES}')

        if old not in self.TRANSITIONS:
            return

        if new not in self.TRANSITIONS[old] and old != new:
            raise InvalidStatusError(f'Недопустимый переход статуса: {old} -> {new}')


class TimestampDescriptor:
    """Data descriptor для временных меток"""
    def __init__(self, auto: bool = True):
        self.auto = auto
        self.data = {}

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if id(obj) not in self.data and self.auto:
            self.__set__(obj, None)
        return self.data.get(id(obj))

    def __set__(self, obj, value: Optional[float]):
        if value is None and self.auto:
            value = time.time()

        if value is not None and not isinstance(value, (int, float)):
            raise TypeError(f'Временная метка должна быть числом, получено: {type(value).__name__}')

        self.data[id(obj)] = value
        logger.debug(f"Установленна временная метка {value}")

    def __delete__(self, obj):
        if self.auto:
            raise AttributeError('Нельзя удалить временную метку')
        del self.data[id(obj)]


class DataDescriptor:
    """Non-data descriptor для доступа в payload"""
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        logger.debug(f"DataDescriptor.__get__ вызван для {obj}")
        return getattr(obj, '_payload', {})

    def __set_name__(self, owner, name):
        self.name = name