import logging, sys
from datetime import datetime


def setup_logging(level=logging.INFO):
    '''
    функция настройки логов.
    Создает файл логово и выводит его название (между запусками
    файл отличается)
    Изменяет отобажения логов
    :param level: уровень логирования
    '''
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    filename = f'task_sources_{datetime.now().strftime("%Y%m%d-%H%M%S")}.log'
    file_handler = logging.FileHandler(filename, encoding='utf-8')
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.info(f"Логировани настроенно. Уровень: {logging.getLevelName(level)}")
    logging.info(f"Лог-файл: {filename}")