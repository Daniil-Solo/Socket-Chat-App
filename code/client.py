import os.path
import socket
import threading
import time

from utils import from_dict_to_bytes, from_bytes_to_message, MsgInfo
from storage import Storage


SERVER_PORT = 52531
BUF_SIZE = 1024
KEY_PHRASE = 'GIVE ME YOUR ADDRESS'
SAVING_DIR = os.path.join(os.getcwd(), '../my_saves')


class Client:
    def __init__(self, username):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.settimeout(0.1)
        self.server_address = None
        self.msgs_of_client = Storage(SAVING_DIR)
        self.username = username
        self.limit = self.calculate_limit()

    def calculate_limit(self) -> int:
        """
        Подсчет максимальной длины контентной части
        5 вычитается для надежности
        """
        data = from_dict_to_bytes({
            'user': self.username,
            'data':  "",
            'is_end': 1,
            'type': "t"
        })
        return BUF_SIZE - len(data) - 5

    def get_server_address(self):
        """
        Получение адреса сервера
        """
        self.socket.sendto(KEY_PHRASE.encode(), ('<broadcast>', SERVER_PORT))
        while True:
            try:
                data, server = self.socket.recvfrom(BUF_SIZE)
                if data:
                    self.server_address = server
                    break
            except socket.timeout:
                continue

    def start(self):
        """
        Запуск цикла обработки сообщений
        """
        self.get_server_address()
        threading.Thread(target=self.loop).start()

    def loop(self):
        """
        Цикл обработки сообщений
        """
        while True:
            try:
                data, server = self.socket.recvfrom(BUF_SIZE)
            except socket.timeout:
                continue
            msg = from_bytes_to_message(data)
            self.handle_new_message(msg)

    def handle_new_message(self, message: MsgInfo):
        """
        Обработка нового сообщения
        """
        if message.type != 'h':
            if message.user not in self.msgs_of_client:
                self.msgs_of_client[message.user] = message.data
            else:
                self.msgs_of_client.add(message.user, message.data)

        if message.is_end:
            self.print_message(message)

    def print_message(self, message: MsgInfo):
        """
        Печать целого сообщения в чат клиента
        """
        print(message.user, ":")
        if message.type == 't':
            with open(self.msgs_of_client[message.user], 'rb') as f:
                bin_string = f.read(BUF_SIZE)
                while bin_string:
                    text_string = bin_string.decode()
                    print(text_string)
                    bin_string = f.read(BUF_SIZE)
        elif message.type == 'h':
            filepath = self.msgs_of_client[message.user]
            os.rename(filepath, os.path.join(SAVING_DIR, message.data.decode()))
            print("Файл", message.data)
        del self.msgs_of_client[message.user]

    def send_text(self, text: str):
        """
        Отправка текстового сообщения
        """
        i = 0
        while i <= len(text):
            data = from_dict_to_bytes({
                'user': self.username,
                'data': text[i: i + self.limit],
                'is_end': 1 if i + self.limit > len(text) else 0,
                'type': 't'
            })
            i += self.limit
            self.socket.sendto(data, self.server_address)
            time.sleep(0.1)

    def send_file(self, filepath: str):
        """
        Отправка файла
        """
        with open(filepath, 'rb') as f:
            file_part = f.read(self.limit)
            while file_part:
                data = from_dict_to_bytes({
                    'user': self.username,
                    'data': file_part,
                    'is_end': 0,
                    'type': 'f'
                })
                self.socket.sendto(data, self.server_address)
                file_part = f.read(self.limit)
        data = from_dict_to_bytes({
            'user': self.username,
            'data': os.path.basename(filepath),
            'is_end': 1,
            'type': 'h'
        })
        self.socket.sendto(data, self.server_address)


if __name__ == "__main__":
    client = Client("User")
    client.start()