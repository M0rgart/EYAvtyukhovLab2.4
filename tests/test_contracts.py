import unittest
import logging
from typing import List
from src.contracts import Task, TaskSource, check_task_source


logging.disable(logging.CRITICAL)


class MockValidSource:
    """Корректный источник задач для тестов"""

    def get_tasks(self) -> List[Task]:
        return [Task(id="test1", payload="data")]


class MockInvalidSource:
    """Некорректный источник задач (нет метода get_tasks)"""

    def fetch(self) -> List[Task]:
        return [Task(id="test1", payload="data")]


class TestContracts(unittest.TestCase):

    def test_task_creation(self):
        """Тест создания задачи"""
        task = Task(id="123", payload={"key": "value"})
        self.assertEqual(task.id, "123")
        self.assertEqual(task.payload, {"key": "value"})

    def test_valid_source_contract(self):
        """Тест проверки корректного источника"""
        source = MockValidSource()
        self.assertTrue(check_task_source(source))
        self.assertTrue(isinstance(source, TaskSource))

    def test_invalid_source_contract(self):
        """Тест проверки некорректного источника"""
        source = MockInvalidSource()
        self.assertFalse(check_task_source(source))
        self.assertFalse(isinstance(source, TaskSource))

    def test_task_source_protocol_methods(self):
        """Тест наличия обязательных методов у протокола"""
        methods = dir(TaskSource)
        self.assertIn('get_tasks', methods)


if __name__ == '__main__':
    unittest.main()