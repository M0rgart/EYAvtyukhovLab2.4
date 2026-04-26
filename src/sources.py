import logging
import json, random, string
from .contracts import Task, TaskSource
from typing import List, Generator


logger = logging.getLogger(__name__)


class FileTaskSource:
    '''
    Источник задач, собирает данные из JSON
    Реализует интерфейс TaskSource и собирает задача из JSON-файла
    На вход получает путь JSON-файлу
    '''
    def __init__(self, path: str):
        '''
        Инициализаия задач из указанного файла
        :param path:
        '''
        self.path = path
        logger.info(f"Создан FileTaskSource с фалом {path}")

    def _generate_id(self) -> str:
        '''
        Генератор случайного идентификатора для задач.
        '''
        return "".join(random.choices(string.ascii_letters + string.digits, k=8))

    def get_tasks(self) -> List[Task]:
        '''
        Читает Json-файл, парсит его и создает объекты Task для каждого элемента.
        Генерирует id и создает пустой словарь при отсутсвии id и payload соответственно
        Возвращает список задач
        '''
        try:
            with open(self.path, 'r', encoding="utf-8") as f:
                data = json.load(f)

            tasks = []
            for item in data:
                task = Task(id=item.get('id', self._generate_id()),
                            payload=item.get('payload', {}))
                tasks.append(task)

            logger.info(f"Загружено {len(tasks)} задач из файла {self.path}")
            return tasks

        except FileNotFoundError:
            logger.error(f"Файл {self.path} не найден")
            raise FileNotFoundError(f"Файл {self.path} не найден")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {self.path}: {e}")
            raise json.JSONDecodeError(f"Ошибка парсинга JSON в файле {self.path}: {e.msg}", e.doc, e.pos)
        except Exception as e:
            logger.error(f"Не предвиденная ошибка: {e}")
            raise

    def __repr__(self):
        return f"FileTaskSource(path={self.path})"


class GeneratorTaskSource:
    '''
    Источник задач, генерирующий тестовые данные.
    Создает указанное количество задач со случайными данными
    '''
    def __init__(self, count: int=10, pref: str='gen'):
        '''
        Инициалищация.
        :param count: Количество генерируемых задач. По умолчанию 10
        :param pref: Префикс для идентификатора задач. По умолчанию gen
        '''
        self.count = count
        self.pref = pref
        logger.info(f"Создан GeneratorTaskSource (count={self.count}, pref={self.pref})")

    def get_tasks(self) -> List[Task]:
        '''
        Генерирует и возвращает список задач с последовательными id и
        случайным payload
        :return: список сгенерированных задач
        '''
        tasks = []
        for i in range(self.count):
            task = Task(
                id=f'{self.pref}_{i+1}',
                payload={
                    'number': i+1,
                    'data': random.randint(1, 100000),
                    'timestamp': f"2026-02{i+1:02d}"
                }
            )
            tasks.append(task)

        logger.info(f"Сгенерированно {len(tasks)} задач")
        return tasks

    def __repr__(self):
        return f"GeneratorTaskSource(count={self.count}, pref={self.pref})"


class APITaskSource:
    '''
    Источник задач, имитирует работу с API.
    Эмулирует получение задач из API, генерирует мок-данные для тестирования
    '''
    def __init__(self, end: str='https://www.youtube.com/watch?v=dQw4w9WgXcQ'):
        '''
        Инициализация.
        :param end: Эндпоинт APIю По умолчанию демонстрационный URL
        '''
        self.end = end
        self._tasks = self._generate_mock_tasks()
        logger.info(f"Создан APITaskSource с эндпоинтом {self.end}")

    def get_tasks(self) -> List[Task]:
        '''
        Возвращает список задач, имитируя API-запрос
        Логирует запрос и возвращает копию внутреннего списка задач
        :return: копия внутреннго списка задач
        '''
        logger.debug(f'Выполняется запрос к {self.end}')
        logger.info(f'Получено {len(self._tasks)} задач из API')
        return self._tasks.copy()

    def _generate_mock_tasks(self) -> List[Task]:
        '''
        Генератор мок-данных для эмуляции API-ответа
        5 тестовых задач со случайными темами, уровнями сложности и количеством очков
        :return: список сгенерированных задач
        '''
        tasks = []
        for i in range(5):
            task = Task(
                id=f"api_{i+1}",
                payload={
                    'topic': random.choice(["1", "2", "3", "4", "5"]),
                    'dif': random.choice(['low', 'medium', 'high']),
                    'points': random.randint(10, 100)
                }
            )
            tasks.append(task)
        return tasks

    def __repr__(self):
        return f"APITaskSource(endpoint={self.end})"
