"""
Тесты для асинхронного исполнителя задач (ЛР4) - исправленная версия
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock

from src.async_executor import AsyncTaskExecutor
from src.handler import PrintHandler, PriorityHandler, FailingHandler
from models.task import Task as DomainTask


@pytest.fixture
def sample_task():
    return DomainTask(
        id="TEST_001",
        description="Тестовая задача",
        priority=2,
        status="pending"
    )


@pytest.fixture
def sample_tasks():
    return [
        DomainTask(id=f"TEST_{i}", description=f"Задача {i}", priority=(i % 4) + 1, status="pending")
        for i in range(5)
    ]


class TestAsyncExecutor:
    """Синхронные тесты для AsyncTaskExecutor"""

    def test_initialization(self):
        """Тест инициализации исполнителя"""
        executor = AsyncTaskExecutor(max_workers=3)

        assert executor._max_workers == 3
        assert executor._running is False
        assert executor._queue.qsize() == 0
        assert executor.success_count == 0
        assert executor.error_count == 0

    def test_register_handler(self):
        """Тест регистрации обработчиков"""
        executor = AsyncTaskExecutor()

        handler1 = PrintHandler()
        handler2 = PriorityHandler()

        executor.register_handler(handler1, make_default=True)
        executor.register_handler(handler2)

        assert handler1.name in executor._handlers
        assert handler2.name in executor._handlers
        assert executor._default_handler == handler1

    def test_unregister_handler(self):
        """Тест удаления обработчика"""
        executor = AsyncTaskExecutor()

        handler = PrintHandler()
        executor.register_handler(handler, make_default=True)

        assert executor.unregister_handler(handler.name) is True
        assert handler.name not in executor._handlers
        assert executor._default_handler is None

        assert executor.unregister_handler(handler.name) is False

    def test_add_tasks_sync(self, sample_tasks):
        """Тест синхронного добавления задач"""
        executor = AsyncTaskExecutor()

        executor.add_tasks_sync(sample_tasks)

        assert executor._queue.qsize() == 5

    def test_get_stats(self, sample_tasks):
        """Тест получения статистики"""
        executor = AsyncTaskExecutor(max_workers=2)

        handler = PrintHandler()
        executor.register_handler(handler, make_default=True)
        executor.add_tasks_sync(sample_tasks[:3])

        stats = executor.get_stats()
        assert stats["queue_size"] == 3
        assert stats["handlers_registered"] == [handler.name]
        assert stats["max_workers"] == 2
        assert stats["is_running"] is False


class TestAsyncExecutorAsync:
    """Асинхронные тесты для AsyncTaskExecutor"""

    @pytest.mark.asyncio
    async def test_add_task(self, sample_task):
        """Тест добавления задачи в очередь"""
        executor = AsyncTaskExecutor()

        await executor.add_task(sample_task)

        assert executor._queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_add_tasks(self, sample_tasks):
        """Тест добавления нескольких задач"""
        executor = AsyncTaskExecutor()

        await executor.add_tasks(sample_tasks)

        assert executor._queue.qsize() == 5

    @pytest.mark.asyncio
    async def test_start_without_handlers(self):
        """Тест запуска без обработчиков"""
        executor = AsyncTaskExecutor()

        with pytest.raises(RuntimeError, match="Нет обработчиков"):
            await executor.start()

    @pytest.mark.asyncio
    async def test_start_without_default_handler(self):
        """Тест запуска без обработчика по умолчанию"""
        executor = AsyncTaskExecutor()
        executor.register_handler(PrintHandler(), make_default=False)

        with pytest.raises(RuntimeError, match="Нет обработчика по умолчанию"):
            await executor.start()

    @pytest.mark.asyncio
    async def test_basic_processing(self, sample_tasks):
        """Тест базовой обработки задач"""
        executor = AsyncTaskExecutor(max_workers=2)
        executor.register_handler(PrintHandler(), make_default=True)

        executor.add_tasks_sync(sample_tasks[:3])

        async with executor:
            await asyncio.sleep(0.5)

        assert executor.success_count == 3
        assert executor.error_count == 0
        assert len(executor.results) == 3

    @pytest.mark.asyncio
    async def test_with_priority_handler(self, sample_tasks):
        """Тест обработки с PriorityHandler"""
        executor = AsyncTaskExecutor(max_workers=4)
        executor.register_handler(PriorityHandler(), make_default=True)

        tasks = sample_tasks[:4]
        executor.add_tasks_sync(tasks)

        async with executor:
            await asyncio.sleep(1.0)

        assert executor.success_count == 4, f"Expected 4, got {executor.success_count}"
        for result in executor.results:
            assert "processing_time" in result

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Тест обработки ошибок"""
        executor = AsyncTaskExecutor(max_workers=1)

        class AlwaysFailingHandler:
            name = "fail_handler"

            async def handle(self, task):
                raise ValueError("Тестовая ошибка")

        executor.register_handler(AlwaysFailingHandler(), make_default=True)

        task = DomainTask(id="FAIL_001", description="Failing task", priority=1, status="pending")
        executor.add_tasks_sync([task])

        async with executor:
            await asyncio.sleep(0.3)

        assert executor.success_count == 0
        assert executor.error_count == 1

    @pytest.mark.asyncio
    async def test_stats_while_running(self, sample_tasks):
        """Тест получения статистики во время работы"""
        executor = AsyncTaskExecutor(max_workers=2)

        handler = PrintHandler()
        executor.register_handler(handler, make_default=True)
        executor.add_tasks_sync(sample_tasks[:3])

        async with executor:
            await asyncio.sleep(0.1)
            stats_running = executor.get_stats()
            assert stats_running["is_running"] is True
            await asyncio.sleep(0.3)

        assert executor.success_count == 3

    @pytest.mark.asyncio
    async def test_stop_with_timeout(self):
        """Тест остановки с таймаутом"""
        executor = AsyncTaskExecutor(max_workers=1)

        class SlowHandler:
            name = "slow"

            async def handle(self, task):
                await asyncio.sleep(0.5)
                return {"task_id": task.id}

        executor.register_handler(SlowHandler(), make_default=True)

        task = DomainTask(id="SLOW_001", description="Slow task", priority=1, status="pending")
        executor.add_tasks_sync([task])

        await executor.start()
        await asyncio.sleep(0.1)

        await executor.stop(timeout=0.2)

        assert len(executor._workers) == 0
        assert executor._running is False

    @pytest.mark.asyncio
    async def test_context_manager(self, sample_tasks):
        """Тест использования async with контекстного менеджера"""
        executor = AsyncTaskExecutor(max_workers=2)
        executor.register_handler(PrintHandler(), make_default=True)
        executor.add_tasks_sync(sample_tasks[:3])

        async with executor:
            assert executor._running is True
            await asyncio.sleep(0.3)

        assert executor._running is False
        assert executor.success_count == 3

    @pytest.mark.asyncio
    async def test_failing_handler_rate(self):
        """Тест обработчика с вероятностью ошибки"""
        executor = AsyncTaskExecutor(max_workers=2)

        failing = FailingHandler(fail_rate=1.0, name="always_fail")
        executor.register_handler(failing, make_default=True)

        tasks = [
            DomainTask(id=f"FAIL_{i}", description=f"Fail {i}", priority=1, status="pending")
            for i in range(5)
        ]

        executor.add_tasks_sync(tasks)

        async with executor:
            await asyncio.sleep(0.5)

        assert executor.success_count == 0
        assert executor.error_count == 5


class TestPriorityHandler:
    """Тесты для PriorityHandler"""

    @pytest.mark.asyncio
    async def test_priority_handler_name(self):
        """Тест имени обработчика"""
        handler = PriorityHandler(name="custom_name")
        assert handler.name == "custom_name"

        handler2 = PriorityHandler()
        assert handler2.name == "PriorityHandler"

    @pytest.mark.asyncio
    async def test_priority_handler_handle(self):
        """Тест обработки задачи с приоритетом"""
        handler = PriorityHandler()
        task = DomainTask(id="PRIO_001", description="Priority test", priority=3, status="pending")

        result = await handler.handle(task)

        assert result["status"] == "success"
        assert result["priority"] == 3
        assert result["priority_name"] == "High"
        assert "processing_time" in result
        assert result.get("urgent") is True


class TestPrintHandler:
    """Тесты для PrintHandler"""

    @pytest.mark.asyncio
    async def test_print_handler_name(self):
        """Тест имени обработчика"""
        handler = PrintHandler(name="custom_printer")
        assert handler.name == "custom_printer"

        handler2 = PrintHandler()
        assert handler2.name == "PrintHandler"

    @pytest.mark.asyncio
    async def test_print_handler_handle(self):
        """Тест обработки задачи PrintHandler"""
        handler = PrintHandler()
        task = DomainTask(id="PRINT_001", description="Print test", priority=2, status="pending")

        result = await handler.handle(task)

        assert result["status"] == "success"
        assert result["task_id"] == "PRINT_001"
        assert "message" in result


class TestFailingHandler:
    """Тесты для FailingHandler"""

    @pytest.mark.asyncio
    async def test_failing_handler_success(self):
        """Тест успешной обработки (без ошибки)"""
        handler = FailingHandler(fail_rate=0.0, name="never_fail")
        task = DomainTask(id="OK_001", description="OK test", priority=1, status="pending")

        result = await handler.handle(task)

        assert result["status"] == "success"
        assert result["task_id"] == "OK_001"

    @pytest.mark.asyncio
    async def test_failing_handler_error(self):
        """Тест ошибочной обработки"""
        handler = FailingHandler(fail_rate=1.0, name="always_fail")
        task = DomainTask(id="ERR_001", description="Error test", priority=1, status="pending")

        with pytest.raises(ValueError, match="Случайная ошибка при обработке задачи ERR_001"):
            await handler.handle(task)

    @pytest.mark.asyncio
    async def test_failing_handler_name(self):
        """Тест имени обработчика"""
        handler = FailingHandler(fail_rate=0.5, name="flaky")
        assert handler.name == "flaky"

        handler2 = FailingHandler(fail_rate=0.5)
        assert handler2.name == "FailingHandler"