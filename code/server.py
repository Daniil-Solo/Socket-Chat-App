import os
import socket
import threading
import time

from utils import from_bytes_to_message, from_dict_to_bytes, MsgInfo
from storage import Storage

IP = ""
PORT = 52531
SAVING_DIR = os.path.join(os.getcwd(), '../saves')
BUF_SIZE = 1024
TIMEOUT = 0.1


class Server:
    def __init__(self, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.bind((ip, port))
        self.msgs_of_client = Storage(SAVING_DIR)
        self.clients = dict()
        print("Сервер настроился!")

    def start(self):
        """
        Основной цикл обработки входящих сообщений
        """
        print("Сервер запущен!")
        while True:
            data, client = self.socket.recvfrom(1024)
            time.sleep(TIMEOUT)
            msg = from_bytes_to_message(data)
            print('Сервер получил сообщение от', client, ": ", msg.data[:100], '...')
            self.handle_new_message(msg, client)

    def handle_new_message(self, message: MsgInfo, client: tuple):
        """
        Обработка нового сообщения
        """
        if message.type != 'h':
            if message.user not in self.clients:
                self.clients[message.user] = client
                self.msgs_of_client[message.user] = message.data
            elif message.user not in self.msgs_of_client:
                self.msgs_of_client[message.user] = message.data
            else:
                self.msgs_of_client.add(message.user, message.data)

        if message.is_end:
            threading.Thread(target=self.send_message, args=(message, )).start()

    def send_message(self, message: MsgInfo):
        """
        Отправка сообщения всем клиентам чата
        """
        for username in [user for user in self.clients.keys() if user != message.user]:
            client = self.clients[username]
            limit = self.calculate_limit(username)
            with open(self.msgs_of_client[message.user], 'rb') as f: # отправляем порционно файл сообщения
                file_part = f.read(limit)
                while file_part:
                    data = from_dict_to_bytes({
                        'user': message.user,
                        'data': file_part,
                        'is_end': 0,
                        'type': 't' if message.type == 't' else 'f'
                    })
                    self.socket.sendto(data, client)
                    time.sleep(0.1)
                    file_part = f.read(limit)
            if message.type == 't':             # для текста отправляем еще одно сообщение, обозначающее конец текста
                data = from_dict_to_bytes({
                    'user': message.user,
                    'data': '',
                    'is_end': 1,
                    'type': 't'
                })
                self.socket.sendto(data, client)
            else:                           # для файла отправляем сообщение с именем файла, обозначающее конец файла
                data = from_dict_to_bytes({
                    'user': message.user,
                    'data': message.data,
                    'is_end': 1,
                    'type': 'h'
                })
                self.socket.sendto(data, client)
            print("Сервер отправил сообщение!")
        del self.msgs_of_client[message.user]

    @staticmethod
    def calculate_limit(username: str) -> int:
        """
        Подсчет максимальной длины контентной части,
        исходя из имени пользователя
        5 вычитается для надежности
        """
        data = from_dict_to_bytes({
            'user': username,
            'data':  b"",
            'is_end': 1,
            'type': "t"
        })
        return BUF_SIZE - len(data) - 5


if __name__ == "__main__":
    server = Server(IP, PORT)
    server.start()
