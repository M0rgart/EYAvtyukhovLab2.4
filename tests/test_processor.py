import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from src.processor import TaskProcessor
from src.contracts import Task


class TestTaskProcessor:
    """Тесты для класса TaskProcessor"""

    def test_init(self, caplog):
        """Тест инициализации процессора"""
        with caplog.at_level(logging.INFO):
            processor = TaskProcessor()

        assert processor.sources == []
        assert "создан TaskProcessor" in caplog.text

    def test_add_source_valid(self, caplog):
        """Тест добавления валидного источника"""
        processor = TaskProcessor()
        mock_source = Mock()
        mock_source.__repr__ = Mock(return_value="MockSource()")

        with patch('src.processor.check_task_source', return_value=True):
            with caplog.at_level(logging.INFO):
                result = processor.add_source(mock_source)

        assert result is True
        assert len(processor.sources) == 1
        assert processor.sources[0] == mock_source
        assert f"Источник MockSource() добавлен" in caplog.text

    def test_add_source_invalid(self, caplog):
        """Тест добавления невалидного источника"""
        processor = TaskProcessor()
        mock_source = Mock()
        mock_source.__repr__ = Mock(return_value="InvalidSource()")

        with patch('src.processor.check_task_source', return_value=False):
            with caplog.at_level(logging.ERROR):
                result = processor.add_source(mock_source)

        assert result is False
        assert len(processor.sources) == 0
        assert "не соответствует контракту" in caplog.text

    def test_get_source_count(self):
        """Тест получения количества источников"""
        processor = TaskProcessor()
        assert processor.get_sorce_count() == 0

        processor.sources = [Mock(), Mock()]
        assert processor.get_sorce_count() == 2

    def test_process_all_empty_sources(self, caplog):
        """Тест обработки при пустом списке источников"""
        processor = TaskProcessor()

        with caplog.at_level(logging.INFO):
            tasks = processor.process_all()

        assert tasks == []
        assert "Всего получено задач: 0" in caplog.text

    def test_process_all_single_source(self):
        """Тест обработки одного источника"""
        processor = TaskProcessor()

        mock_source = Mock()
        mock_tasks = [Task(id=1, payload="task1"), Task(id=2, payload="task2")]
        mock_source.get_tasks.return_value = mock_tasks
        mock_source.__repr__ = Mock(return_value="MockSource")

        processor.sources = [mock_source]

        tasks = processor.process_all()

        assert len(tasks) == 2
        assert tasks == mock_tasks
        mock_source.get_tasks.assert_called_once()

    def test_process_all_multiple_sources(self):
        """Тест обработки нескольких источников"""
        processor = TaskProcessor()

        mock_source1 = Mock()
        mock_source1.get_tasks.return_value = [Task(id=1, payload="a"), Task(id=2, payload="b")]
        mock_source1.__repr__ = Mock(return_value="Source1")

        mock_source2 = Mock()
        mock_source2.get_tasks.return_value = [Task(id=3, payload="c")]
        mock_source2.__repr__ = Mock(return_value="Source2")

        processor.sources = [mock_source1, mock_source2]

        tasks = processor.process_all()

        assert len(tasks) == 3
        assert tasks[0].id == 1
        assert tasks[1].id == 2
        assert tasks[2].id == 3

        mock_source1.get_tasks.assert_called_once()
        mock_source2.get_tasks.assert_called_once()

    def test_process_all_source_raises_exception(self, caplog):
        """Тест обработки при исключении в источнике"""
        processor = TaskProcessor()

        mock_source1 = Mock()
        mock_source1.get_tasks.return_value = [Task(id=1, payload="ok")]
        mock_source1.__repr__ = Mock(return_value="GoodSource")

        mock_source2 = Mock()
        mock_source2.get_tasks.side_effect = Exception("API Error")
        mock_source2.__repr__ = Mock(return_value="BadSource")

        mock_source3 = Mock()
        mock_source3.get_tasks.return_value = [Task(id=3, payload="also ok")]
        mock_source3.__repr__ = Mock(return_value="AnotherSource")

        processor.sources = [mock_source1, mock_source2, mock_source3]

        with caplog.at_level(logging.ERROR):
            tasks = processor.process_all()

        assert len(tasks) == 2
        assert tasks[0].id == 1
        assert tasks[1].id == 3
        assert "Ошибка при получении задач: API Error" in caplog.text

        mock_source1.get_tasks.assert_called_once()
        mock_source2.get_tasks.assert_called_once()
        mock_source3.get_tasks.assert_called_once()

    def test_process_all_logging(self, caplog):
        """Тест логирования при обработке"""
        processor = TaskProcessor()

        mock_source = Mock()
        mock_source.get_tasks.return_value = [Task(id=1, payload="test")]
        mock_source.__repr__ = Mock(return_value="TestSource")

        processor.sources = [mock_source]

        with caplog.at_level(logging.INFO):
            tasks = processor.process_all()

        assert "Обработка источника 1/1: TestSource" in caplog.text
        assert "Получено 1 задача из источника TestSource" in caplog.text
        assert "Всего получено задач: 1" in caplog.text

    def test_process_all_with_debug_logging(self, caplog):
        """Тест debug логирования задач"""
        processor = TaskProcessor()

        mock_source = Mock()
        mock_task = Task(id=42, payload={"key": "value"})
        mock_source.get_tasks.return_value = [mock_task]
        mock_source.__repr__ = Mock(return_value="TestSource")

        processor.sources = [mock_source]

        with caplog.at_level(logging.DEBUG):
            tasks = processor.process_all()

        assert "Задача: Task(id=42, payload={'key': 'value'})" in caplog.text