import pytest
import json
import logging
from unittest.mock import mock_open, patch, MagicMock
from src.sources import FileTaskSource, GeneratorTaskSource, APITaskSource
from src.contracts import Task


class TestFileTaskSource:
    """Тесты для FileTaskSource"""

    def test_init(self, caplog):
        """Тест инициализации"""
        with caplog.at_level(logging.INFO):
            source = FileTaskSource("test.json")

        assert source.path == "test.json"
        assert "Создан FileTaskSource с фалом test.json" in caplog.text

    def test_repr(self):
        """Тест строкового представления"""
        source = FileTaskSource("data.json")
        assert repr(source) == "FileTaskSource(path=data.json)"

    @patch('builtins.open', new_callable=mock_open, read_data='[{"id": "1", "payload": {"x": 1}}]')
    def test_get_tasks_success(self, mock_file, caplog):
        """Тест успешного получения задач из файла"""
        source = FileTaskSource("test.json")

        with caplog.at_level(logging.INFO):
            tasks = source.get_tasks()

        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == {"x": 1}
        assert isinstance(tasks[0], Task)
        assert f"Загружено 1 задач из файла test.json" in caplog.text
        mock_file.assert_called_once_with("test.json", 'r', encoding="utf-8")

    @patch('builtins.open', new_callable=mock_open, read_data='[{"payload": {"data": 42}}]')
    @patch('src.sources.FileTaskSource._generate_id', return_value="gen123")  # Исправлен путь импорта
    def test_get_tasks_with_missing_id(self, mock_generate_id, mock_file):
        """Тест генерации ID при его отсутствии"""
        source = FileTaskSource("test.json")

        tasks = source.get_tasks()

        assert len(tasks) == 1
        assert tasks[0].id == "gen123"
        assert tasks[0].payload == {"data": 42}
        mock_generate_id.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='[{"id": "1"}, {"id": "2", "payload": "test"}]')
    def test_get_tasks_multiple_items(self, mock_file):
        """Тест получения нескольких задач"""
        source = FileTaskSource("test.json")

        tasks = source.get_tasks()

        assert len(tasks) == 2
        assert tasks[0].id == "1"
        assert tasks[0].payload == {}
        assert tasks[1].id == "2"
        assert tasks[1].payload == "test"

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_get_tasks_file_not_found(self, mock_file, caplog):
        """Тест ошибки при отсутствии файла"""
        source = FileTaskSource("missing.json")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(FileNotFoundError, match="Файл missing.json не найден"):
                source.get_tasks()

        assert "Файл missing.json не найден" in caplog.text

    @patch('builtins.open', new_callable=mock_open, read_data='{"invalid": json')
    def test_get_tasks_json_decode_error(self, mock_file, caplog):
        """Тест ошибки при некорректном JSON"""
        source = FileTaskSource("bad.json")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(json.JSONDecodeError):
                source.get_tasks()

        assert "Ошибка парсинга JSON" in caplog.text

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load', side_effect=Exception("Unexpected error"))
    def test_get_tasks_unexpected_error(self, mock_json_load, mock_file, caplog):
        """Тест неожиданной ошибки"""
        source = FileTaskSource("test.json")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception, match="Unexpected error"):
                source.get_tasks()

        assert "Не предвиденная ошибка: Unexpected error" in caplog.text

    @patch('random.choices', return_value=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
    def test_generate_id(self, mock_choices):
        """Тест генерации ID"""
        source = FileTaskSource("test.json")
        task_id = source._generate_id()

        assert task_id == "abcdefgh"
        mock_choices.assert_called_once()


class TestGeneratorTaskSource:
    """Тесты для GeneratorTaskSource"""

    def test_init_default(self, caplog):
        """Тест инициализации с параметрами по умолчанию"""
        with caplog.at_level(logging.INFO):
            source = GeneratorTaskSource()

        assert source.count == 10
        assert source.pref == 'gen'
        assert "Создан GeneratorTaskSource (count=10, pref=gen)" in caplog.text

    def test_init_custom(self):
        """Тест инициализации с пользовательскими параметрами"""
        source = GeneratorTaskSource(count=5, pref='test')

        assert source.count == 5
        assert source.pref == 'test'

    def test_repr(self):
        """Тест строкового представления"""
        source = GeneratorTaskSource(count=3, pref='abc')
        assert repr(source) == "GeneratorTaskSource(count=3, pref=abc)"

    @patch('random.randint', return_value=42)
    def test_get_tasks_default_count(self, mock_randint, caplog):
        """Тест получения задач с count по умолчанию"""
        source = GeneratorTaskSource()

        with caplog.at_level(logging.INFO):
            tasks = source.get_tasks()

        assert len(tasks) == 10
        assert isinstance(tasks[0], Task)
        assert tasks[0].id == "gen_1"
        assert tasks[0].payload['number'] == 1
        assert tasks[0].payload['data'] == 42
        assert tasks[0].payload['timestamp'] == "2026-0201"

        assert tasks[9].id == "gen_10"
        assert tasks[9].payload['number'] == 10
        assert tasks[9].payload['timestamp'] == "2026-0210"

        assert f"Сгенерированно 10 задач" in caplog.text
        assert mock_randint.call_count == 10

    @patch('random.randint', return_value=100)
    def test_get_tasks_custom_count_and_pref(self, mock_randint):
        """Тест получения задач с пользовательскими параметрами"""
        source = GeneratorTaskSource(count=3, pref='custom')

        tasks = source.get_tasks()

        assert len(tasks) == 3
        assert tasks[0].id == "custom_1"
        assert tasks[1].id == "custom_2"
        assert tasks[2].id == "custom_3"

        for task in tasks:
            assert task.payload['data'] == 100

    def test_get_tasks_zero_count(self):
        """Тест получения задач с count = 0"""
        source = GeneratorTaskSource(count=0)

        tasks = source.get_tasks()

        assert len(tasks) == 0

    def test_get_tasks_payload_structure(self):
        """Тест структуры payload задач"""
        source = GeneratorTaskSource(count=2)

        tasks = source.get_tasks()

        for i, task in enumerate(tasks, 1):
            assert 'number' in task.payload
            assert task.payload['number'] == i
            assert 'data' in task.payload
            assert isinstance(task.payload['data'], int)
            assert 'timestamp' in task.payload
            assert task.payload['timestamp'].startswith("2026-02")


class TestAPITaskSource:
    """Тесты для APITaskSource"""

    def test_init_default(self, caplog):
        """Тест инициализации с эндпоинтом по умолчанию"""
        with caplog.at_level(logging.INFO):
            source = APITaskSource()

        assert source.end == 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        assert "Создан APITaskSource с эндпоинтом" in caplog.text
        assert len(source._tasks) == 5

    def test_init_custom_endpoint(self):
        """Тест инициализации с пользовательским эндпоинтом"""
        source = APITaskSource(end='https://api.example.com')

        assert source.end == 'https://api.example.com'
        assert len(source._tasks) == 5

    def test_repr(self):
        """Тест строкового представления"""
        source = APITaskSource(end='https://test.api')
        assert repr(source) == "APITaskSource(endpoint=https://test.api)"

    @patch('random.choice', side_effect=['1', 'medium', '3', 'high', '5'] * 3)
    @patch('random.randint', return_value=50)
    def test_get_tasks(self, mock_randint, mock_choice, caplog):
        """Тест получения задач из API"""
        source = APITaskSource()

        with caplog.at_level(logging.INFO):
            tasks = source.get_tasks()

        assert len(tasks) == 5
        assert isinstance(tasks[0], Task)


        for i, task in enumerate(tasks, 1):
            assert task.id == f"api_{i}"
            assert 'topic' in task.payload
            assert 'dif' in task.payload
            assert 'points' in task.payload
            assert task.payload['points'] == 50

        assert f"Получено 5 задач из API" in caplog.text

    @patch('random.choice', return_value='test')
    @patch('random.randint', return_value=75)
    def test_get_tasks_returns_copy(self, mock_randint, mock_choice):
        """Тест что get_tasks возвращает копию, а не оригинал"""
        source = APITaskSource()

        tasks1 = source.get_tasks()
        tasks2 = source.get_tasks()

        assert tasks1 is not tasks2
        assert tasks1 == tasks2

        tasks1.append(Task(id="extra", payload={}))
        assert len(source.get_tasks()) == 5

    def test_generate_mock_tasks_variety(self):
        """Тест разнообразия генерируемых задач"""
        source1 = APITaskSource()
        source2 = APITaskSource()

        tasks1 = source1.get_tasks()
        tasks2 = source2.get_tasks()

        assert len(tasks1) == 5
        assert len(tasks2) == 5

        for task in tasks1:
            assert task.payload['dif'] in ['low', 'medium', 'high']
            assert 10 <= task.payload['points'] <= 100

    def test_get_tasks_logging_debug(self, caplog):
        """Тест debug логирования при запросе к API"""
        source = APITaskSource()

        with caplog.at_level(logging.DEBUG):
            source.get_tasks()

        assert "Выполняется запрос к" in caplog.text
        assert source.end in caplog.text