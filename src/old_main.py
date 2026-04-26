import logging
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.logger_config import setup_logging
from src.sources import FileTaskSource, GeneratorTaskSource, APITaskSource
from src.processor import TaskProcessor
from src.contracts import check_task_source
from models.task import Task
from models.queue import TaskQueue
from models.exceptions import InvalidStatusError, InvalidIDError


def create_file():
    """Создает пример JSON файла с задачами"""
    import json

    sample_data = [
        {
            "id": "file_1",
            "payload": {
                "type": "calculation",
                "value": 42,
                "description": "Вычислить сумму"
            }
        },
        {
            "id": "file_2",
            "payload": {
                "type": "validation",
                "data": [1, 2, 3],
                "description": "Проверить данные"
            }
        },
        {
            "payload": {
                "type": "no_id",
                "description": "Задача без ID"
            }
        }
    ]

    with open("sample_tasks.json", "w", encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)

    print("Создан файл sample_tasks.json")


def demonstrate_lab1_sources():
    """Демонстрация работы источников задач (ЛР1)"""
    for _ in range(2):
        print()
    print("ЛАБОРАТОРНАЯ РАБОТА №1: ИСТОЧНИКИ ЗАДАЧ")

    processor = TaskProcessor()

    sources = [
        FileTaskSource("sample_tasks.json"),
        GeneratorTaskSource(count=3, pref="gen"),
        APITaskSource(end="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    ]

    for source in sources:
        if processor.add_source(source):
            print(f"Добавлен источник: {source}")
        else:
            print(f"Источник не прошел проверку: {source}")

    print(f"\nВсего источников: {processor.get_sorce_count()}")
    tasks = processor.process_all()

    print(f"\nПолучено задач: {len(tasks)}")
    for i, task in enumerate(tasks[:5], 1):
        print(f"    {i}. {task}")

    return tasks


def demonstrate_lab2_model():
    """Демонстрация работы модели задачи с дескрипторами (ЛР2)"""
    for _ in range(2):
        print()
    print("ЛАБОРАТОРНАЯ РАБОТА №2: МОДЕЛЬ ЗАДАЧИ С ДЕСКРИПТОРАМИ")

    # Создание задачи
    task = Task(
        id="TASK-001",
        description="Разработать модуль валидации",
        priority=3,
        status="pending",
        payload={"assignee": "ivanov", "deadline": "2024-02-01"}
    )

    print(f"1. СОЗДАНИЕ ЗАДАЧИ:")
    print(f"    {task}")
    print(f"    Приоритет: {task.priority} ({task.priority_name})")
    print(f"    Время создания: {time.ctime(task.created_at)}")

    # Демонстрация валидации
    print(f"\n2. ВАЛИДАЦИЯ АТРИБУТОВ:")
    try:
        Task(id="", description="test", priority=1)
    except InvalidIDError as e:
        print(f"    Перехвачена ошибка: {e}")

    # Изменение статуса
    print(f"\n3. УПРАВЛЕНИЕ СТАТУСОМ:")
    print(f"    Текущий статус: {task.status}")

    task.upd_status("running")
    print(f"    После upd_status('running'): {task.status}")

    task.upd_status("completed")
    print(f"    После upd_status('completed'): {task.status}")

    try:
        task.upd_status("pending")  # Нельзя вернуться
    except InvalidStatusError as e:
        print(f"    Некорректный переход перехвачен: {e}")

    # Вычисляемые свойства
    print(f"\n4. ВЫЧИСЛЯЕМЫЕ СВОЙСТВА:")
    print(f"    Готовность (is_ready): {task.is_ready}")
    print(f"    Завершена (is_completed): {task.is_completed}")
    print(f"    Возраст: {task.age_formatted}")

    # Data vs Non-data descriptors
    print(f"\n5. DATA VS NON-DATA DESCRIPTORS:")
    print(f"    Data descriptor (priority) - хранится в дескрипторе: {task.priority}")
    print(f"    Non-data descriptor (status) - в __dict__: {task.__dict__['status']}")

    return task


def demonstrate_lab3_queue():
    """Демонстрация работы очереди задач с итераторами и генераторами (ЛР3)"""
    for _ in range(2):
        print()
    print("ЛАБОРАТОРНАЯ РАБОТА №3: ОЧЕРЕДЬ ЗАДАЧ (ИТЕРАТОРЫ И ГЕНЕРАТОРЫ)")

    # Функция для создания свежих тестовых задач
    def create_test_tasks():
        return [
            Task(id="T1", description="Задача 1: Низкий приоритет", priority=1, status="pending"),
            Task(id="T2", description="Задача 2: Средний приоритет", priority=2, status="running"),
            Task(id="T3", description="Задача 3: Высокий приоритет", priority=3, status="pending"),
            Task(id="T4", description="Задача 4: Критический приоритет", priority=4, status="completed"),
            Task(id="T5", description="Задача 5: Средний приоритет", priority=2, status="pending"),
            Task(id="T6", description="Задача 6: Высокий приоритет", priority=3, status="running"),
            Task(id="T7", description="Задача 7: Низкий приоритет", priority=1, status="canceled"),
        ]

    # 1. СОЗДАНИЕ ТЕСТОВЫХ ЗАДАЧ
    print("1. СОЗДАНИЕ ТЕСТОВЫХ ЗАДАЧ:")
    tasks = create_test_tasks()
    for t in tasks:
        print(f"    {t.id}: {t.description[:30]}... (приор.{t.priority['value']}, {t.status})")

    # 2. СОЗДАНИЕ ОЧЕРЕДИ
    queue = TaskQueue(tasks)
    print(f"\n2. СОЗДАНИЕ ОЧЕРЕДИ:")
    print(f"    {queue}")
    print(f"    Размер очереди: {queue.size()}")
    print(f"    Пуста? {queue.is_empty()}")

    # 3. БАЗОВЫЕ ОПЕРАЦИИ С ОЧЕРЕДЬЮ
    print(f"\n3. БАЗОВЫЕ ОПЕРАЦИИ С ОЧЕРЕДЬЮ:")
    print(f"    peek(): {queue.peek().id if queue.peek() else None}")
    print(f"    pop(): {queue.pop().id}")
    print(f"    После pop, размер: {queue.size()}")
    print(f"    peek() после pop: {queue.peek().id if queue.peek() else None}")

    queue.push(Task(id="T8", description="Новая задача", priority=3, status="pending"))
    print(f"    После push(T8), размер: {queue.size()}")

    # 4. ИТЕРАЦИЯ ПО ОЧЕРЕДИ
    print(f"\n4. ИТЕРАЦИЯ ПО ОЧЕРЕДИ:")
    print("    Задачи в очереди:")
    for i, task in enumerate(queue, 1):
        print(f"    {i}. {task.id}: {task.status} (приор.{task.priority['value']})")

    # 5. ПОВТОРНЫЙ ОБХОД ОЧЕРЕДИ
    print(f"\n5. ПОВТОРНЫЙ ОБХОД ОЧЕРЕДИ:")
    print("    Первый проход:")
    for task in queue:
        print(f"     {task.id}")
    print("    Второй проход:")
    for task in queue:
        print(f"     {task.id}")

    # 6. ЛЕНИВЫЕ ФИЛЬТРЫ (используем свежую очередь)
    print(f"\n6. ЛЕНИВЫЕ ФИЛЬТРЫ (ГЕНЕРАТОРЫ):")
    fresh_queue = TaskQueue(create_test_tasks())

    print("    Задачи со статусом 'pending':")
    for task in fresh_queue.filter_by_status('pending'):
        print(f"     - {task.id} ({task.priority_name})")

    print("    Задачи со статусом 'running':")
    for task in fresh_queue.filter_by_status('running'):
        print(f"     - {task.id} ({task.priority_name})")

    print("    Задачи с высоким приоритетом (3-4):")
    for task in fresh_queue.filter_by_priority(min_priority=3, max_priority=4):
        print(f"     - {task.id} (приоритет {task.priority['value']})")

    print("    Задачи с низким приоритетом (1-2):")
    for task in fresh_queue.filter_by_priority(min_priority=1, max_priority=2):
        print(f"     - {task.id} (приоритет {task.priority['value']})")

    print("\n    Задачи, готовые к выполнению (is_ready=True):")
    for task in fresh_queue.filter_by(lambda t: t.is_ready):
        print(f"     - {task.id}: is_ready={task.is_ready}, статус={task.status}")

    # 7. ЭФФЕКТИВНОСТЬ С БОЛЬШИМИ ДАННЫМИ
    print(f"\n7. ЭФФЕКТИВНОСТЬ С БОЛЬШИМИ ДАННЫМИ:")
    print("    Создание очереди с 10000 задач...")
    large_queue = TaskQueue()
    for i in range(10000):
        large_queue.push(Task(
            id=f"BIG_{i}",
            description=f"Большая задача {i}",
            priority=(i % 4) + 1,
            status="pending" if i % 3 != 0 else "running"
        ))
    print(f"    Создана очередь с {large_queue.size()} задачами")

    print("    Ленивая фильтрация (без создания копии в памяти):")
    start = time.time()
    high_priority_count = 0
    for _ in large_queue.filter_by_priority(min_priority=3):
        high_priority_count += 1
    elapsed = time.time() - start
    print(f"    Найдено задач с высоким приоритетом: {high_priority_count}")
    print(f"    Время выполнения: {elapsed:.4f} сек.")

    print("\n    Демонстрация ленивости (фильтр не вычисляется до итерации):")
    filtered = large_queue.filter_by_status("pending")
    print("    filter_by_status('pending') вызван - память не выделена")
    print("    Добавляем ещё одну задачу...")
    large_queue.push(Task(id="LAST", description="Последняя задача", priority=4, status="pending"))
    count = 0
    for _ in filtered:
        count += 1
    print(f"    При итерации учтена добавленная задача: {count} задач в фильтре")

    # 8. ИСПОЛЬЗОВАНИЕ В СТАНДАРТНЫХ КОНСТРУКЦИЯХ PYTHON
    print(f"\n8. ИСПОЛЬЗОВАНИЕ В СТАНДАРТНЫХ КОНСТРУКЦИЯХ PYTHON:")
    demo_queue = TaskQueue(create_test_tasks())
    print(f"    len(queue): {len(demo_queue)}")
    print(f"    bool(queue): {bool(demo_queue)}")
    print(f"    list(queue): {[t.id for t in list(demo_queue)[:3]]}...")

    # 9. ДОПОЛНИТЕЛЬНЫЕ ОПЕРАЦИИ
    print(f"\n9. ДОПОЛНИТЕЛЬНЫЕ ОПЕРАЦИИ:")
    demo_queue = TaskQueue(create_test_tasks())
    copied_queue = demo_queue.copy()
    print(f"    Копия очереди: {copied_queue}")
    print(f"    Оригинал и копия - разные объекты (через is): {demo_queue is copied_queue}")

    demo_queue.clear()
    print(f"    После очистки оригинальной очереди: {demo_queue}")
    print(f"    Копия не изменилась: {copied_queue}")

    return queue


def demonstrate_integration():
    """Демонстрация интеграции ЛР1, ЛР2 и ЛР3"""
    for _ in range(2):
        print()
    print("ИНТЕГРАЦИЯ ЛР1, ЛР2 И ЛР3: ИСТОЧНИКИ + МОДЕЛЬ + ОЧЕРЕДЬ")

    class DomainTaskSource:
        def __init__(self, count=3):
            self.count = count

        def get_tasks(self):
            tasks = []
            for i in range(self.count):
                task = Task(
                    id=f"DOMAIN-{i + 1}",
                    description=f"Интегрированная задача {i + 1}",
                    priority=(i % 4) + 1,
                    status="pending" if i < 2 else "running",
                    payload={"source": "integration", "number": i + 1}
                )
                tasks.append(task)
            return tasks

        def __repr__(self):
            return f"DomainTaskSource(count={self.count})"

    source = DomainTaskSource()

    if check_task_source(source):
        print(f"Источник доменных задач прошел проверку контракта")

        processor = TaskProcessor()
        processor.add_source(source)

        tasks = processor.process_all()
        print(f"\nПолучено задач из процессора: {len(tasks)}")

        queue = TaskQueue(tasks)
        print(f"Задачи помещены в очередь: {queue}")

        print("\nОбработка задач из очереди:")
        for i, task in enumerate(queue, 1):
            print(f"\n  {i}. {task}")
            print(f"    Статус: {task.status}")
            print(f"    Приоритет: {task.priority_name}")
            print(f"    Готовность: {task.is_ready}")

            if task.is_ready and task.status == "pending":
                task.upd_status("running")
                print(f"    Статус изменён на: {task.status}")

        print("\nФильтрация очереди после обработки:")
        pending_tasks = list(queue.filter_by_status("pending"))
        running_tasks = list(queue.filter_by_status("running"))
        print(f"    Осталось pending: {[t.id for t in pending_tasks]}")
        print(f"    Осталось running: {[t.id for t in running_tasks]}")
    else:
        print("Источник не прошел проверку контракта")


def main():
    """Главная функция"""
    setup_logging(logging.WARNING)  # Используем WARNING для отключения информационных логов

    print(" ЛАБОРАТОРНЫЕ РАБОТЫ №1, №2, №3: ПЛАТФОРМА ОБРАБОТКИ ЗАДАЧ ")

    create_file()
    demonstrate_lab1_sources()
    demonstrate_lab2_model()
    demonstrate_lab3_queue()
    demonstrate_integration()


if __name__ == "__main__":
    main()