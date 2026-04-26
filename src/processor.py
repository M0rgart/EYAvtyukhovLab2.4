from typing import List
import logging
from .contracts import Task, TaskSource, check_task_source


logger = logging.getLogger(__name__)


class TaskProcessor:
    '''
    Обработчик задач, управляющий их источниками.
    1) добавление задач
    2) обработка всех задач из добавленных источников
    3) получений количества источников

    sources - список источников задач
    '''
    def __init__(self):
        '''
        инициализация, создание пустого списка источников задач, логирует этот процесс
        '''
        self.sources = []
        logger.info('создан TaskProcessor')

    def add_source(self, source: TaskSource) -> bool:
        '''
        Добавляет источник задач в процессор.
        Проверяет его на соответствие котнтракту TaskSource
        При успехе добавляется, результат логируется
        :param source: источник задач для добавления
        :return: True при добавлении, иначе False
        '''
        if check_task_source(source):
            self.sources.append(source)
            logger.info(f'Источник {source} добавлен')
            return True
        else:
            logger.error(f'Источник {source} не соответствует контракту')
            return False

    def process_all(self) -> List[Task]:
        '''
        Обработка всех задач из всех источников
        Последовательно пробегает все источники и все задачи в них, собирая в общий
        список. В случае ошибки переходит к другому источнику.
        Процесс логируется.
        :return: список всех задач из всех источников
        '''
        all_tasks = []


        for i, source in enumerate(self.sources, 1):
            logger.info(f'Обработка источника {i}/{len(self.sources)}: {source}')

            try:
                tasks = source.get_tasks()
                logger.info(f'Получено {len(tasks)} задача из источника {source}')
                for task in tasks:
                    logger.debug(f'Задача: {task}')
                all_tasks.extend(tasks)
            except Exception as e:
                logger.error(f'Ошибка при получении задач: {e}')
                continue

        logger.info(f'Всего получено задач: {len(all_tasks)}')
        return all_tasks

    def get_sorce_count(self) -> int:
        '''
        Возвращает количество добавленных источников задач
        '''
        return len(self.sources)