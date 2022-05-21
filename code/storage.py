import os


class Storage:
    """
    Хранит в формате ключ-значение: имя пользователя и путь до файла,
    в котором находятся сообщения от этого пользователя
    Сохраняемые файлы имеют расширение .bin, считывание и запись
    происходят в бинарном режиме.
    """
    def __init__(self, saving_dir):
        if not os.path.exists(saving_dir):
            os.mkdir(saving_dir)
        self.saving_dir = saving_dir
        self.storage = dict()

    def __iter__(self):
        for key in self.storage:
            yield key

    def __len__(self):
        return len(self.storage)

    def __setitem__(self, key, value):
        self.storage[key] = os.path.join(self.saving_dir, f"{key}.bin")
        with open(self.storage[key], 'wb') as f:
            f.write(value)

    def __getitem__(self, key):
        return self.storage[key]

    def __delitem__(self, key):
        if os.path.isfile(self.storage[key]):
            os.remove(self.storage[key])
        del self.storage[key]

    def add(self, key: str, data: bytes):
        with open(self.storage[key], 'ab') as f:
            f.write(data)
