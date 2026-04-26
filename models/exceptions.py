class TaskValidationExcept(Exception):
    """Базовое исключение"""
    def __init__(self, message: str, attrib: str = None):
        self.message = message
        self.attrib = attrib
        super().__init__(f'{self.message}: {self.attrib}' if attrib else message)

class InvalidPriorityError(TaskValidationExcept):
    """Исключение при неверном приоритете"""
    pass

class InvalidStatusError(TaskValidationExcept):
    """Исключение при неверном статусе"""
    pass

class InvalidDescriptionError(TaskValidationExcept):
    """Исключение при неверном описании"""
    pass

class InvalidIDError(TaskValidationExcept):
    """Исключение при неверном идентификаторе"""
    pass