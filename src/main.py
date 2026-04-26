import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.logger_config import setup_logging
from src.contracts import check_task_source
from src.sources import FileTaskSource, GeneratorTaskSource, APITaskSource
from src.processor import TaskProcessor
from src.handler import PrintHandler, PriorityHandler, FailingHandler
from src.async_executor import AsyncTaskExecutor
from models.task import Task
from models.queue import TaskQueue


async def demonstrate_async_executor():
    logger = logging.getLogger(__name__)

    logger.info("Создание источников задач")
    create_file()
    sources = [
        FileTaskSource("sample_tasks.json"),
        GeneratorTaskSource(count=5, pref="demo"),
        APITaskSource()
    ]

    logger.info("Получение задач из источников")
    processor = TaskProcessor()
    for source in sources:
        if processor.add_source(source):
            logger.debug(f"Добавлен источник: {source}")
        else:
            logger.warning(f"Не удалось добавить источник: {source}")

    tasks_raw = processor.process_all()
    logger.info(f"Получено сырых задач: {len(tasks_raw)}")

    logger.info("Преобразование в доменные задачи")
    domain_tasks = []
    for i, raw_task in enumerate(tasks_raw):
        priority = (i % 4) + 1
        status = "pending"

        task = Task(
            id=raw_task.id if isinstance(raw_task.id, str) else f"T{raw_task.id}",
            description=f"Задача из источника: {raw_task.payload.get('description', 'Нет описания')[:50]}",
            priority=priority,
            status=status,
            payload={"source_id": raw_task.id, "original_payload": raw_task.payload}
        )
        domain_tasks.append(task)

    domain_tasks.extend([
        Task(id="MANUAL_1", description="Ручная задача - низкий приоритет", priority=1, status="pending"),
        Task(id="MANUAL_2", description="Ручная задача - средний приоритет", priority=2, status="pending"),
        Task(id="MANUAL_3", description="Ручная задача - высокий приоритет", priority=3, status="pending"),
        Task(id="MANUAL_4", description="Ручная задача - критический приоритет", priority=4, status="pending"),
    ])

    logger.info(f"Создано доменных задач: {len(domain_tasks)}")
    logger.debug(f"Первые 5 задач: {[(t.id, t.priority_name) for t in domain_tasks[:5]]}")

    logger.info("Демонстрация 1: Базовый асинхронный исполнитель")

    executor = AsyncTaskExecutor(max_workers=3)
    executor.register_handler(PrintHandler(), make_default=True)
    executor.register_handler(PriorityHandler(name="priority_handler"))

    logger.debug(f"Зарегистрированные обработчики: {list(executor._handlers.keys())}")

    executor.add_tasks_sync(domain_tasks[:8])

    async with executor:
        logger.info("Запуск асинхронного исполнителя")
        await asyncio.sleep(0.5)
        stats = executor.get_stats()
        logger.info(f"Статистика: {stats}")

    logger.info(
        f"Результаты: успешно={executor.success_count}, ошибок={executor.error_count}, всего={executor.success_count + executor.error_count}")

    logger.info("Демонстрация 2: Обработчики с разной логикой")

    executor2 = AsyncTaskExecutor(max_workers=4)
    executor2.register_handler(PriorityHandler(name="high_priority_handler"), make_default=True)
    executor2.register_handler(PrintHandler(name="printer"))

    test_tasks = [
        Task(id="LOW_1", description="Низкий приоритет", priority=1, status="pending"),
        Task(id="LOW_2", description="Низкий приоритет 2", priority=1, status="pending"),
        Task(id="MED_1", description="Средний приоритет", priority=2, status="pending"),
        Task(id="HIGH_1", description="Высокий приоритет", priority=3, status="pending"),
        Task(id="HIGH_2", description="Высокий приоритет 2", priority=3, status="pending"),
        Task(id="CRIT_1", description="Критический приоритет", priority=4, status="pending"),
    ]

    executor2.add_tasks_sync(test_tasks)

    async with executor2:
        await asyncio.sleep(1.0)

    logger.info(f"Обработано задач с разными приоритетами: {len(executor2.results)}")
    for result in executor2.results[:3]:
        logger.debug(f"Результат {result['task_id']}: {result.get('status')} (обработчик: {result['handler']})")

    logger.info("Демонстрация 3: Обработка ошибок")

    executor3 = AsyncTaskExecutor(max_workers=2)
    failing_handler = FailingHandler(fail_rate=0.5, name="flaky_handler")
    executor3.register_handler(failing_handler, make_default=True)

    error_tasks = [
        Task(id=f"ERR_{i}", description=f"Тестовая задача {i}", priority=(i % 4) + 1, status="pending")
        for i in range(10)
    ]

    executor3.add_tasks_sync(error_tasks)
    logger.info(f"Добавлено {len(error_tasks)} задач с вероятностью ошибки 50%")

    async with executor3:
        await asyncio.sleep(1.5)

    error_rate = executor3.error_count / (executor3.success_count + executor3.error_count) * 100 if (
                                                                                                                executor3.success_count + executor3.error_count) > 0 else 0
    logger.info(
        f"Статистика ошибок: успешно={executor3.success_count}, ошибок={executor3.error_count}, процент ошибок={error_rate:.1f}%")

    logger.info("Демонстрация 4: Интеграция с очередью задач")

    sync_queue = TaskQueue(domain_tasks[8:12] if len(domain_tasks) > 12 else domain_tasks)
    logger.info(f"Создана очередь с {sync_queue.size()} задачами")

    executor4 = AsyncTaskExecutor(max_workers=2)
    executor4.register_handler(PrintHandler(name="integrator"), make_default=True)

    for task in sync_queue:
        executor4.add_tasks_sync([task])

    logger.info(f"Перенесено задач в асинхронный исполнитель: {sync_queue.size()}")

    async with executor4:
        await asyncio.sleep(0.8)

    logger.info(
        f"Интеграция завершена: обработано={executor4.success_count + executor4.error_count}, успешно={executor4.success_count}")

    return executor.get_stats()


def create_file():
    import json
    logger = logging.getLogger(__name__)

    sample_data = [
        {
            "id": "async_file_1",
            "payload": {
                "type": "calculation",
                "value": 42,
                "description": "Вычислить сумму"
            }
        },
        {
            "id": "async_file_2",
            "payload": {
                "type": "validation",
                "data": [1, 2, 3],
                "description": "Проверить данные"
            }
        }
    ]

    with open("sample_tasks.json", "w", encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)

    logger.info("Создан файл sample_tasks.json")


async def main():
    setup_logging(logging.WARNING)
    logger = logging.getLogger(__name__)

    logger.warning("Запуск платформы обработки задач (ЛР1-4)")

    try:
        await demonstrate_async_executor()
        logger.warning("Все демонстрации успешно завершены")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())