import asyncio
import logging
from typing import List, Dict, Any, Optional, Type
from contextlib import asynccontextmanager

from models.queue import TaskQueue
from models.task import Task as DomainTask
from .handler import TaskHandler
from .contracts import check_task_source
from .sources import FileTaskSource, GeneratorTaskSource, APITaskSource

logger = logging.getLogger(__name__)

class AsyncTaskExecutor:
    """Асинхронный исполнитель задач"""
    def __init__(self, max_workers: int = 5):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._handlers: Dict[str, TaskHandler] = {}
        self._default_handler: Optional[TaskHandler] = None
        self._max_workers = max_workers
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._results: List[Dict[str, Any]] = []
        self._error_count = 0
        self._success_count = 0

        logger.info(f'Создан AsyncTaskExecutor с max_workers={max_workers}')

    def register_handler(self, handler: TaskHandler, make_default: bool = False) -> None:
        self._handlers[handler.name] = handler
        if make_default:
            self._default_handler = handler
        logger.info(f"Зарегестрирован обработчик: {handler.name} (default={make_default})")

    def unregister_handler(self, name: str) -> bool:
        if name in self._handlers:
            if self._default_handler and self._default_handler.name == name:
                self._default_handler = None
            del self._handlers[name]
            logger.info(f"Удален обработчик: {name}")
            return True
        logger.warning(f"ОБработчик {name} не найден")
        return False

    async def add_task(self, task: DomainTask) -> None:
        await self._queue.put(task)
        logger.debug(f"Задача {task.id} добавлена в асинхронную очередь. Размер: {self._queue.qsize()}")

    async def add_tasks(self, tasks: List[DomainTask]) -> None:
        for task in tasks:
            await self.add_task(task)
        logger.info(f"Добавлено {len(tasks)} задач в очередь")

    def add_tasks_sync(self, tasks: List[DomainTask]) -> None:
        for task in tasks:
            self._queue.put_nowait(task)
        logger.info(f"Добавлено {len(tasks)} задач в синхронную очередь")

    @asynccontextmanager
    async def _task_context(self, task: DomainTask, handler: TaskHandler):
        """Контекстный менеджер для обработки задач (с логами и обработкой ошибок)"""
        start_time = asyncio.get_event_loop().time()
        try:
            yield
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.debug(f"Успешная обработка задачи {task.id} за {elapsed_time:.3f} сек")
        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Ошибка обработки задачи {task.id} послк {elapsed_time:.3f} сек {e}")
            raise

    async def _worker(self, worker_id: int) -> None:
        """Настоящий работяга, обрабатывает задачи из очереди"""
        logger.info(f"РАБочий {worker_id} запущен")

        while self._running:
            try:
                try:
                    task = await asyncio.wait_for(self._queue.get(), timeout=1)
                except asyncio.TimeoutError:
                    continue

                handler = self._handlers.get(task.priority_name.lower(), self._default_handler)

                if handler is None:
                    logger.error(f"Нет обработчика задачи {task.id} (приоритет: {task.priority_name})")
                    self._error_count += 1
                    self._queue.task_done()
                    continue

                async with self._task_context(task, handler):
                    res = await handler.handle(task)
                    res['worker_id'] = worker_id
                    self._results.append(res)
                    self._success_count += 1
                    logger.info(f"Воркер {worker_id}: задача {task.id} обработана успешно")

                self._queue.task_done()

            except asyncio.CancelledError:
                logger.info(f"РАБочий {worker_id} отменен")
                break
            except Exception as e:
                logger.error(f"РАБочий {worker_id}: критическая ошибка - {e}")
                self._error_count += 1
                self._queue.task_done()

            logger.info(f'РАБочий {worker_id} остановлен')

    async def start(self) -> None:
        """Запуск исполнителя (создание worker-ов)"""
        if self._running:
            logger.warning("Исполнитель уже запущен")
            return
        if not self._handlers:
            raise RuntimeError('Нет обработчиков')
        if self._default_handler is None:
            raise RuntimeError("Нет обработчика по умолчанию")

        self._running = True
        self._workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self._max_workers)
        ]
        logger.info(f"Исполнитель запущен с {self._max_workers} РАБочими")

    async def stop(self, timeout: float = 10) -> None:
        """
        Остановка исполнителя.
        Аргумент: timeout - время ожидания завершения текущих задач
        """
        if not self._running:
            return

        logger.info(f"Остановка исполнителя... (таймаут {timeout} сек)")

        self._running = False
        try:
            await asyncio.wait_for(self._queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Задачи не завершены за {timeout} секунд")
        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info(f"Исполитель остановлен. Успешно: {self._success_count}, Ошибо: {self._error_count}")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    @property
    def results(self) -> List[Dict[str, Any]]:
        return self._results.copy()

    @property
    def success_count(self) -> int:
        return self._success_count

    @property
    def error_count(self) -> int:
        return self._error_count

    def get_stats(self) -> Dict[str, Any]:
        return {
            'queue_size': self.queue_size,
            'success_count': self._success_count,
            'error_count': self._error_count,
            'total_processed': self._success_count + self._error_count,
            'handlers_registered': list(self._handlers.keys()),
            'default_handler': self._default_handler.name if self._default_handler else None,
            'max_workers': self._max_workers,
            'is_running': self._running
        }