from configs import BUF_SIZE, MAGIC_VALUE


def calculate_limit(username: str) -> int:
    """
    Подсчет максимальной длины контентной части исходя из имени пользователя
    """
    return BUF_SIZE - len(username) - MAGIC_VALUE
