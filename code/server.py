import os
import socket
import threading
import time

from utils import calculate_limit
from storage import Storage
from configs import BUF_SIZE, KEY_PHRASE, SERVER_PORT as PORT, TIMEOUT

IP = ""
SAVING_DIR = os.path.join(os.getcwd(), './saves')


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
        data, client = None, None
        print("Сервер запущен!")
        while True:
            try:
                data, client = self.socket.recvfrom(BUF_SIZE)
            except socket.error:
                pass
            else:
                try:
                    if data[: len(KEY_PHRASE)].decode() == KEY_PHRASE:
                        username = data[len(KEY_PHRASE):].decode()
                        self.clients[client] = username
                        print('Сервер отправил свой адрес клиенту: ', client)
                        self.socket.sendto(KEY_PHRASE.encode(), client)
                        continue
                    else:
                        self.handle_new_data(data, client)
                except UnicodeDecodeError:
                    self.handle_new_data(data, client)

    def handle_new_data(self, data: bytes, client: tuple):
        """
        Обработка нового сообщения
        """
        try:
            if data[:1].decode() == 't':
                self.send_message(data, client,)
            elif data[:4].decode() == 'FEND':
                self.send_message(data, client, filename=data[4:].decode())
            else:
                username = self.clients[client]
                if username not in self.msgs_of_client:
                    self.msgs_of_client[username] = data
                else:
                    self.msgs_of_client.add(username, data)
        except UnicodeDecodeError:
            username = self.clients[client]
            if username not in self.msgs_of_client:
                self.msgs_of_client[username] = data
            else:
                self.msgs_of_client.add(username, data)

    def send_message(self, data: bytes, client: tuple, filename=None):
        """
        Отправка сообщения всем клиентам чата
        """
        username = self.clients[client]
        clients_for_message = [c for c in self.clients.keys() if c != client]
        if not filename:
            new_data = (username + ': ').encode() + data[1:]
            for some_client in clients_for_message:
                self.socket.sendto(new_data, some_client)
        else:
            new_data = (username + 'FILE').encode()
            for some_client in clients_for_message:
                self.socket.sendto(new_data, some_client)
            with open(self.msgs_of_client[username], 'rb') as f:
                limit = calculate_limit(username)
                file_part = f.read(limit)
                while file_part:
                    for some_client in clients_for_message:
                        self.socket.sendto(file_part, some_client)
                        time.sleep(TIMEOUT)
                    file_part = f.read(limit)
            new_data = ('FEND' + filename).encode()
            for some_client in clients_for_message:
                self.socket.sendto(new_data, some_client)
            del self.msgs_of_client[username]


if __name__ == "__main__":
    server = Server(IP, PORT)
    server.start()
