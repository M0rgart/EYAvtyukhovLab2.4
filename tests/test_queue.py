"""
Тесты для очереди задач TaskQueue (ЛР3)
Покрытие: >80%
"""

import pytest
import logging
import time
from unittest.mock import patch, MagicMock
from models.queue import TaskQueue
from models.task import Task
from models.exceptions import InvalidStatusError

# Отключаем логирование во время тестов
logging.disable(logging.CRITICAL)


class TestTaskQueueInit:
    """Тесты инициализации очереди"""

    def test_init_empty(self):
        """Тест создания пустой очереди"""
        queue = TaskQueue()
        assert queue.size() == 0
        assert queue.is_empty() is True
        assert len(queue) == 0
        assert bool(queue) is False

    def test_init_with_tasks(self):
        """Тест создания очереди с начальными задачами"""
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
        ]
        queue = TaskQueue(tasks)
        assert queue.size() == 2
        assert queue.is_empty() is False
        assert bool(queue) is True

    def test_init_empty_list(self):
        """Тест создания очереди с пустым списком"""
        queue = TaskQueue([])
        assert queue.size() == 0
        assert queue.is_empty() is True

    def test_repr(self):
        """Тест строкового представления"""
        queue = TaskQueue()
        assert repr(queue) == "TaskQueue(size=0)"

        task = Task(id="1", description="Test", priority=1)
        queue.push(task)
        assert repr(queue) == "TaskQueue(size=1)"

    def test_str_empty(self):
        """Тест строкового представления пустой очереди"""
        queue = TaskQueue()
        assert str(queue) == "TaskQueue(empty)"

    def test_str_non_empty(self):
        """Тест строкового представления непустой очереди"""
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
        ]
        queue = TaskQueue(tasks)
        assert "TaskQueue(2 tasks:" in str(queue)


class TestTaskQueueBasicOperations:
    """Тесты базовых операций с очередью"""

    def test_push(self):
        """Тест добавления задачи"""
        queue = TaskQueue()
        task = Task(id="test1", description="Test task", priority=2)

        queue.push(task)

        assert queue.size() == 1
        assert queue.peek() == task

    def test_push_multiple(self):
        """Тест добавления нескольких задач"""
        queue = TaskQueue()
        task1 = Task(id="1", description="Task 1", priority=1)
        task2 = Task(id="2", description="Task 2", priority=2)
        task3 = Task(id="3", description="Task 3", priority=3)

        queue.push(task1)
        queue.push(task2)
        queue.push(task3)

        assert queue.size() == 3
        assert queue.peek() == task1

    def test_pop(self):
        """Тест извлечения задачи"""
        queue = TaskQueue()
        task = Task(id="test1", description="Test task", priority=2)
        queue.push(task)

        popped = queue.pop()

        assert popped == task
        assert queue.size() == 0
        assert queue.is_empty() is True

    def test_pop_from_empty_queue(self):
        """Тест извлечения из пустой очереди"""
        queue = TaskQueue()
        popped = queue.pop()
        assert popped is None
        assert queue.size() == 0

    def test_pop_order_fifo(self):
        """Тест порядка FIFO (первым пришёл - первым ушёл)"""
        queue = TaskQueue()
        task1 = Task(id="1", description="First", priority=1)
        task2 = Task(id="2", description="Second", priority=2)
        task3 = Task(id="3", description="Third", priority=3)

        queue.push(task1)
        queue.push(task2)
        queue.push(task3)

        assert queue.pop() == task1
        assert queue.pop() == task2
        assert queue.pop() == task3
        assert queue.pop() is None

    def test_peek(self):
        """Тест просмотра первой задачи без извлечения"""
        queue = TaskQueue()
        task = Task(id="test1", description="Test task", priority=2)
        queue.push(task)

        peeked = queue.peek()

        assert peeked == task
        assert queue.size() == 1

    def test_peek_empty_queue(self):
        """Тест peek на пустой очереди"""
        queue = TaskQueue()
        assert queue.peek() is None

    def test_clear(self):
        """Тест очистки очереди"""
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
            Task(id="3", description="Task 3", priority=3),
        ]
        queue = TaskQueue(tasks)
        assert queue.size() == 3

        queue.clear()
        assert queue.size() == 0
        assert queue.is_empty() is True

    def test_extend(self):
        """Тест добавления нескольких задач"""
        queue = TaskQueue()
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
        ]

        queue.extend(tasks)

        assert queue.size() == 2
        assert queue.peek() == tasks[0]

    def test_to_list(self):
        """Тест преобразования в список"""
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
        ]
        queue = TaskQueue(tasks)

        task_list = queue.to_list()

        assert task_list == tasks
        assert task_list is not tasks

    def test_copy(self):
        """Тест копирования очереди"""
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
        ]
        queue = TaskQueue(tasks)

        copied = queue.copy()

        assert copied.size() == queue.size()
        assert copied.to_list() == queue.to_list()
        assert copied is not queue


class TestTaskQueueIteration:
    """Тесты итерации по очереди"""

    def test_iteration_over_empty_queue(self):
        """Тест итерации по пустой очереди"""
        queue = TaskQueue()
        tasks = list(queue)
        assert tasks == []

    def test_iteration_over_queue(self):
        """Тест итерации по очереди"""
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
            Task(id="3", description="Task 3", priority=3),
        ]
        queue = TaskQueue(tasks)

        result = list(queue)

        assert result == tasks

    def test_iteration_preserves_queue(self):
        """Тест что итерация не изменяет очередь"""
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
        ]
        queue = TaskQueue(tasks)

        for _ in queue:
            pass

        assert queue.size() == 2
        assert queue.peek() == tasks[0]

    def test_repeated_iteration(self):
        """Тест повторного обхода очереди"""
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
        ]
        queue = TaskQueue(tasks)

        first_pass = list(queue)
        second_pass = list(queue)

        assert first_pass == tasks
        assert second_pass == tasks
        assert first_pass is not second_pass

    def test_multiple_for_loops(self):
        """Тест использования в нескольких циклах for"""
        tasks = [
            Task(id="1", description="Task 1", priority=1),
            Task(id="2", description="Task 2", priority=2),
        ]
        queue = TaskQueue(tasks)

        count1 = 0
        for _ in queue:
            count1 += 1

        count2 = 0
        for _ in queue:
            count2 += 1

        assert count1 == 2
        assert count2 == 2


class TestTaskQueueFilters:
    """Тесты ленивых фильтров"""

    def setup_method(self):
        """Подготовка тестовых данных"""
        self.tasks = [
            Task(id="1", description="Pending Low", priority=1, status="pending"),
            Task(id="2", description="Pending Medium", priority=2, status="pending"),
            Task(id="3", description="Running High", priority=3, status="running"),
            Task(id="4", description="Completed Critical", priority=4, status="completed"),
            Task(id="5", description="Pending High", priority=3, status="pending"),
            Task(id="6", description="Running Medium", priority=2, status="running"),
            Task(id="7", description="Canceled Low", priority=1, status="canceled"),
        ]
        self.queue = TaskQueue(self.tasks)

    def test_filter_by_status_pending(self):
        """Тест фильтрации по статусу pending"""
        result = list(self.queue.filter_by_status("pending"))
        assert len(result) == 3
        assert all(t.status == "pending" for t in result)
        assert [t.id for t in result] == ["1", "2", "5"]

    def test_filter_by_status_running(self):
        """Тест фильтрации по статусу running"""
        result = list(self.queue.filter_by_status("running"))
        assert len(result) == 2
        assert all(t.status == "running" for t in result)
        assert [t.id for t in result] == ["3", "6"]

    def test_filter_by_status_completed(self):
        """Тест фильтрации по статусу completed"""
        result = list(self.queue.filter_by_status("completed"))
        assert len(result) == 1
        assert result[0].id == "4"

    def test_filter_by_status_canceled(self):
        """Тест фильтрации по статусу canceled"""
        result = list(self.queue.filter_by_status("canceled"))
        assert len(result) == 1
        assert result[0].id == "7"

    def test_filter_by_status_invalid(self):
        """Тест фильтрации с неверным статусом"""
        queue = TaskQueue()
        with pytest.raises(InvalidStatusError, match="Неверный статус invalid"):
            list(queue.filter_by_status("invalid"))

    def test_filter_by_priority_range(self):
        """Тест фильтрации по диапазону приоритета"""
        result = list(self.queue.filter_by_priority(2, 3))
        assert len(result) == 4
        for task in result:
            priority_value = task.priority['value'] if isinstance(task.priority, dict) else task.priority
            assert 2 <= priority_value <= 3

    def test_filter_by_priority_min_only(self):
        """Тест фильтрации по минимальному приоритету"""
        result = list(self.queue.filter_by_priority(min_priority=3))
        # Приоритет 3: задачи 3 и 5, приоритет 4: задача 4 -> всего 3
        assert len(result) == 3
        for task in result:
            priority_value = task.priority['value'] if isinstance(task.priority, dict) else task.priority
            assert priority_value >= 3

    def test_filter_by_priority_max_only(self):
        """Тест фильтрации по максимальному приоритету"""
        result = list(self.queue.filter_by_priority(max_priority=2))
        # Приоритет 1: задачи 1 и 7, приоритет 2: задачи 2 и 6 -> всего 4
        assert len(result) == 4
        for task in result:
            priority_value = task.priority['value'] if isinstance(task.priority, dict) else task.priority
            assert priority_value <= 2

    def test_filter_by_priority_single_value(self):
        """Тест фильтрации по одному значению приоритета"""
        result = list(self.queue.filter_by_priority(2, 2))
        assert len(result) == 2
        for task in result:
            priority_value = task.priority['value'] if isinstance(task.priority, dict) else task.priority
            assert priority_value == 2

    def test_filter_by_priority_invalid_min(self):
        """Тест фильтрации с неверным min_priority"""
        queue = TaskQueue()
        with pytest.raises(ValueError, match="min_priority должен быть от 1 до 4"):
            list(queue.filter_by_priority(min_priority=0))

    def test_filter_by_priority_invalid_max(self):
        """Тест фильтрации с неверным max_priority"""
        queue = TaskQueue()
        with pytest.raises(ValueError, match="max_priority должен быть от 1 до 4"):
            list(queue.filter_by_priority(max_priority=5))

    def test_filter_by_priority_reversed_range(self):
        """Тест фильтрации с перевёрнутым диапазоном"""
        queue = TaskQueue()
        with pytest.raises(ValueError, match="min_priority.*>.*max_priority"):
            list(queue.filter_by_priority(4, 2))

    def test_custom_filter_by(self):
        """Тест пользовательского фильтра filter_by"""
        result = list(self.queue.filter_by(lambda t: t.is_ready))
        # is_ready = status not in ['completed', 'canceled']
        # Задачи с статусами pending или running: 1,2,3,5,6
        assert len(result) == 5
        assert all(t.is_ready for t in result)

    def test_custom_filter_by_complex(self):
        """Тест сложного пользовательского фильтра"""
        result = list(self.queue.filter_by(
            lambda t: t.priority['value'] >= 3 and t.status == "pending"
        ))
        # Задача 5: priority=3, status=pending; задача 3 имеет status=running
        assert len(result) == 1
        assert result[0].id == "5"

    def test_filter_returns_iterator(self):
        """Тест что фильтры возвращают итератор, а не список"""
        result = self.queue.filter_by_status("pending")
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')
        assert not isinstance(result, list)

    def test_filter_lazy_evaluation(self):
        """Тест ленивости вычислений"""
        filtered = self.queue.filter_by_status("pending")
        self.queue.push(Task(id="8", description="New pending", priority=2, status="pending"))
        result = list(filtered)
        assert any(t.id == "8" for t in result)


class TestTaskQueueLargeData:
    """Тесты эффективной работы с большими объёмами данных"""

    def test_large_queue_memory_efficient(self):
        """Тест что очередь эффективно использует память"""
        queue = TaskQueue()

        for i in range(1000):
            queue.push(Task(id=f"T{i}", description=f"Task {i}", priority=(i % 4) + 1))

        assert queue.size() == 1000

    def test_filter_lazy_no_copy(self):
        """Тест что фильтрация не создаёт копию очереди"""
        queue = TaskQueue()
        for i in range(1000):
            queue.push(Task(id=f"T{i}", description=f"Task {i}", priority=(i % 4) + 1))

        filtered = queue.filter_by_status("pending")
        assert filtered is not None

        count = 0
        for _ in filtered:
            count += 1
        assert count > 0

    def test_chained_filters(self):
        """Тест цепочек фильтров"""
        queue = TaskQueue()
        for i in range(100):
            queue.push(Task(
                id=f"T{i}",
                description=f"Task {i}",
                priority=(i % 4) + 1,
                status="pending" if i % 2 == 0 else "running"
            ))

        count = 0
        for task in queue.filter_by_status("pending"):
            priority_value = task.priority['value'] if isinstance(task.priority, dict) else task.priority
            if priority_value >= 3:
                count += 1

        assert count > 0


class TestTaskQueueEdgeCases:
    """Тесты граничных случаев"""

    def test_empty_queue_filter(self):
        """Тест фильтрации пустой очереди"""
        queue = TaskQueue()
        result = list(queue.filter_by_status("pending"))
        assert result == []

        result = list(queue.filter_by_priority(1, 4))
        assert result == []

    def test_single_task_queue(self):
        """Тест очереди с одной задачей"""
        task = Task(id="single", description="Single task", priority=3)
        queue = TaskQueue([task])

        assert queue.size() == 1
        assert queue.peek() == task
        assert queue.pop() == task
        assert queue.is_empty() is True

    def test_push_after_pop(self):
        """Тест добавления после извлечения"""
        queue = TaskQueue()
        task1 = Task(id="1", description="Task 1", priority=1)
        task2 = Task(id="2", description="Task 2", priority=2)

        queue.push(task1)
        assert queue.pop() == task1
        queue.push(task2)
        assert queue.peek() == task2
        assert queue.size() == 1

    def test_queue_with_duplicate_tasks(self):
        """Тест очереди с дублирующимися задачами"""
        task1 = Task(id="same", description="Same ID", priority=1)
        task2 = Task(id="same", description="Same ID", priority=1)

        queue = TaskQueue([task1, task2])
        assert queue.size() == 2
        assert queue.pop() == task1
        assert queue.pop() == task2

    def test_iteration_after_clear(self):
        """Тест итерации после очистки"""
        queue = TaskQueue([Task(id="1", description="Task", priority=1)])
        queue.clear()
        result = list(queue)
        assert result == []


class TestTaskQueueIntegration:
    """Интеграционные тесты с реальными задачами"""

    def test_with_complex_tasks(self):
        """Тест с комплексными задачами"""
        tasks = [
            Task(
                id="INT_1",
                description="Интеграционная задача 1",
                priority=4,
                status="pending",
                payload={"complex": {"nested": "data"}}
            ),
            Task(
                id="INT_2",
                description="Интеграционная задача 2",
                priority=2,
                status="running",
                payload={"array": [1, 2, 3]}
            ),
        ]
        queue = TaskQueue(tasks)

        assert queue.size() == 2
        assert queue.peek().id == "INT_1"
        assert queue.peek().payload["complex"]["nested"] == "data"

        popped = queue.pop()
        assert popped.id == "INT_1"
        assert popped.priority_name == "Critical"

        remaining = queue.pop()
        assert remaining.id == "INT_2"
        assert remaining.status == "running"

    def test_status_transition_after_queue_operations(self):
        """Тест изменения статуса задач после операций с очередью"""
        task = Task(id="STATUS", description="Status test", priority=2, status="pending")
        queue = TaskQueue([task])

        retrieved = queue.pop()
        assert retrieved.status == "pending"

        retrieved.upd_status("running")
        assert retrieved.status == "running"

        queue.push(retrieved)
        assert queue.peek().status == "running"

    def test_filter_by_age(self):
        """Тест фильтрации по возрасту задачи"""
        import time
        queue = TaskQueue()

        # Создаём старую задачу
        old_task = Task(id="old", description="Old task", priority=1)
        # Получаем дескриптор и напрямую устанавливаем значение в его data
        desc = Task.__dict__['created_at']
        expected_time = time.time() - 3600
        desc.data[id(old_task)] = expected_time

        print(f"expected_time: {expected_time}")
        print(f"desc.data[id(old_task)]: {desc.data[id(old_task)]}")
        print(f"old_task.created_at: {old_task.created_at}")
        print(f"old_task.age: {old_task.age}")

        # Создаём новую задачу
        new_task = Task(id="new", description="New task", priority=1)
        print(f"new_task.created_at: {new_task.created_at}")
        print(f"new_task.age: {new_task.age}")

        queue.push(old_task)
        queue.push(new_task)

        old_tasks = list(queue.filter_by(lambda t: t.age > 1800))
        print(f"old_tasks: {[t.id for t in old_tasks]}")
        assert len(old_tasks) == 1
        assert old_tasks[0].id == "old"