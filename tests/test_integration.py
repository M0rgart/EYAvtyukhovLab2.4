import pytest
import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, call
from src.old_main import main
from src.processor import TaskProcessor
from src.sources import FileTaskSource, GeneratorTaskSource, APITaskSource
from models.task import Task as ModelTask
import src.old_main as main_module


class TestFileCreation:
    """Тесты для функции create_file"""

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.dump')
    def test_create_file_structure(self, mock_json_dump, mock_file):
        """Тест создания файла с правильной структурой"""
        main_module.create_file()

        mock_file.assert_called_once_with("sample_tasks.json", "w", encoding="utf-8")

        args, kwargs = mock_json_dump.call_args
        data = args[0]

        assert len(data) == 3
        assert data[0]["id"] == "file_1"
        assert data[0]["payload"]["type"] == "calculation"
        assert data[1]["id"] == "file_2"
        assert data[2].get("id") is None
        assert data[2]["payload"]["type"] == "no_id"

        assert kwargs.get('indent') == 2

    @patch('builtins.print')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.dump')
    def test_create_file_print_message(self, mock_json_dump, mock_file, mock_print):
        """Тест вывода сообщения о создании файла"""
        main_module.create_file()

        mock_print.assert_called_once_with("Создан файл sample_tasks.json")


class TestMainFunction:
    """Интеграционные тесты для функции main"""

    @patch('src.main.create_file')
    @patch('src.main.TaskProcessor')
    @patch('src.main.FileTaskSource')
    @patch('src.main.GeneratorTaskSource')
    @patch('src.main.APITaskSource')
    @patch('src.main.setup_logging')
    @patch('builtins.print')
    def test_main_successful_execution(
            self, mock_print, mock_setup, mock_api, mock_gen, mock_file,
            mock_processor_class, mock_create_file
    ):
        """Тест успешного выполнения main функции"""
        mock_file_instance = MagicMock()
        mock_file_instance.__str__.return_value = "FileTaskSource(path=sample_tasks.json)"
        mock_file.return_value = mock_file_instance

        mock_gen_instance = MagicMock()
        mock_gen_instance.__str__.return_value = "GeneratorTaskSource(count=3, pref=gen)"
        mock_gen.return_value = mock_gen_instance

        mock_api_instance = MagicMock()
        mock_api_instance.__str__.return_value = "APITaskSource(endpoint=https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
        mock_api.return_value = mock_api_instance

        mock_processor_lab1 = MagicMock()
        mock_processor_lab1.add_source.return_value = True
        mock_processor_lab1.get_sorce_count.return_value = 3

        mock_processor_integration = MagicMock()
        mock_processor_integration.add_source.return_value = True
        mock_processor_integration.get_sorce_count.return_value = 1
        mock_processor_integration.process_all.return_value = []

        mock_processor_class.side_effect = [mock_processor_lab1, mock_processor_integration]

        mock_task1 = MagicMock(spec=ModelTask)
        mock_task1.__str__.return_value = "Task(id=1, payload=task1)"
        mock_task1.status = "pending"
        mock_task1.priority_name = "Medium"
        mock_task1.is_ready = True

        mock_task2 = MagicMock(spec=ModelTask)
        mock_task2.__str__.return_value = "Task(id=2, payload=task2)"
        mock_task2.status = "running"
        mock_task2.priority_name = "High"
        mock_task2.is_ready = True

        mock_task3 = MagicMock(spec=ModelTask)
        mock_task3.__str__.return_value = "Task(id=3, payload=task3)"
        mock_task3.status = "pending"
        mock_task3.priority_name = "Low"
        mock_task3.is_ready = True

        mock_processor_lab1.process_all.return_value = [mock_task1, mock_task2, mock_task3]

        main()

        mock_setup.assert_called_once()
        mock_create_file.assert_called_once()

        assert mock_processor_class.call_count == 2

        mock_file.assert_called_once_with('sample_tasks.json')
        mock_gen.assert_called_once_with(count=3, pref='gen')
        mock_api.assert_called_once_with(end='https://www.youtube.com/watch?v=dQw4w9WgXcQ')

        assert mock_processor_lab1.add_source.call_count == 3
        mock_processor_lab1.process_all.assert_called_once()

        assert mock_processor_integration.add_source.call_count == 1
        mock_processor_integration.process_all.assert_called_once()

    @patch('src.main.create_file')
    @patch('src.main.TaskProcessor')
    @patch('src.main.FileTaskSource')
    @patch('src.main.GeneratorTaskSource')
    @patch('src.main.APITaskSource')
    @patch('src.main.setup_logging')
    @patch('builtins.print')
    def test_main_with_failed_source_addition(
            self, mock_print, mock_setup, mock_api, mock_gen, mock_file,
            mock_processor_class, mock_create_file
    ):
        """Тест main когда некоторые источники не добавляются"""
        mock_file_instance = MagicMock()
        mock_file_instance.__str__.return_value = "FileTaskSource(path=sample_tasks.json)"
        mock_file.return_value = mock_file_instance

        mock_gen_instance = MagicMock()
        mock_gen_instance.__str__.return_value = "GeneratorTaskSource(count=3, pref=gen)"
        mock_gen.return_value = mock_gen_instance

        mock_api_instance = MagicMock()
        mock_api_instance.__str__.return_value = "APITaskSource(endpoint=https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
        mock_api.return_value = mock_api_instance

        mock_processor_lab1 = MagicMock()

        def add_source_side_effect_lab1(source):
            source_str = str(source)
            if "FileTaskSource" in source_str:
                return True
            elif "GeneratorTaskSource" in source_str:
                return False
            elif "APITaskSource" in source_str:
                return True
            return False

        mock_processor_lab1.add_source.side_effect = add_source_side_effect_lab1
        mock_processor_lab1.get_sorce_count.return_value = 2

        mock_processor_integration = MagicMock()
        mock_processor_integration.add_source.return_value = True
        mock_processor_integration.get_sorce_count.return_value = 1
        mock_processor_integration.process_all.return_value = []

        mock_processor_class.side_effect = [mock_processor_lab1, mock_processor_integration]

        mock_task = MagicMock(spec=ModelTask)
        mock_task.__str__.return_value = "Task(id=1, payload=task1)"
        mock_task.status = "pending"
        mock_task.priority_name = "Low"
        mock_task.is_ready = True

        mock_processor_lab1.process_all.return_value = [mock_task]

        main()

        assert mock_processor_class.call_count == 2
        assert mock_processor_lab1.add_source.call_count == 3
        assert mock_processor_integration.add_source.call_count == 1

        mock_processor_lab1.process_all.assert_called_once()
        mock_processor_integration.process_all.assert_called_once()


class TestRealIntegration:
    """Реальные интеграционные тесты (работают с файловой системой)"""

    @pytest.fixture
    def temp_json_file(self):
        data = [
            {"id": "real1", "payload": {"value": 100}},
            {"id": "real2", "payload": {"text": "hello"}}
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name

        yield temp_path

        os.unlink(temp_path)

    def test_file_task_source_real_file(self, temp_json_file):
        """Тест FileTaskSource с реальным файлом"""
        source = FileTaskSource(temp_json_file)
        tasks = source.get_tasks()

        assert len(tasks) == 2
        assert tasks[0].id == "real1"
        assert tasks[0].payload == {"value": 100}
        assert tasks[1].id == "real2"
        assert tasks[1].payload == {"text": "hello"}

    def test_processor_with_real_sources(self, temp_json_file):
        """Тест процессора с реальными источниками"""
        processor = TaskProcessor()

        file_source = FileTaskSource(temp_json_file)
        gen_source = GeneratorTaskSource(count=2, pref='test')

        processor.add_source(file_source)
        processor.add_source(gen_source)

        assert processor.get_sorce_count() == 2

        tasks = processor.process_all()

        assert len(tasks) == 4

        assert tasks[0].id == "real1"
        assert tasks[1].id == "real2"
        assert tasks[2].id == "test_1"
        assert tasks[3].id == "test_2"

    def test_generator_source_deterministic_with_patch(self):
        """Тест генератора с патчем random для детерминированного поведения"""
        with patch('random.randint', return_value=999):
            source = GeneratorTaskSource(count=2, pref='det')
            tasks = source.get_tasks()

        assert tasks[0].payload['data'] == 999
        assert tasks[1].payload['data'] == 999

    def test_api_source_creation(self):
        """Тест создания API источника"""
        source = APITaskSource(end="https://test-api.example.com")
        assert source.end == "https://test-api.example.com"
        tasks = source.get_tasks()
        assert len(tasks) == 5
        assert tasks[0].id == "api_1"