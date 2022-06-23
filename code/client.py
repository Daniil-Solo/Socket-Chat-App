import os.path
import socket
import time

from utils import calculate_limit
from storage import Storage
from configs import BUF_SIZE, KEY_PHRASE, SERVER_PORT, TIMEOUT, TIMEOUT_UDP, SERVER_TCP_PORT


SAVING_DIR = os.path.join(os.getcwd(), 'my_saves')


class Client:
    def __init__(self, username, lock):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__socket.settimeout(TIMEOUT)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_address = None
        self.__msgs_of_client = Storage(SAVING_DIR)
        self.__username = username
        self.__limit = calculate_limit(self.__username)
        self.connected = True
        self.data = None
        self.lock = lock

    def get_server_address(self):
        """
        Получение адреса сервера
        """
        self.__socket.sendto(KEY_PHRASE.encode(), ('<broadcast>', SERVER_PORT))
        time.sleep(TIMEOUT_UDP)
        while True:
            data, server = self.__socket.recvfrom(BUF_SIZE)
            if data:
                self.server_address = server
                break
        self.__socket.close()
        print((self.server_address[0], SERVER_TCP_PORT))
        self.server_socket.connect((self.server_address[0], SERVER_TCP_PORT))
        self.server_socket.send(self.__username.encode())

    def set_data(self, data):
        """
        Инициализация хранилища новых сообщений для графического интерфейса
        """
        self.data = data

    def loop(self):
        """
        Цикл обработки сообщений
        """
        while self.connected:
            data = self.server_socket.recv(BUF_SIZE)
            self.__handle_new_data(data)
        self.server_socket.close()

    def __handle_new_data(self, data: bytes):
        """
        Обработка нового сообщения
        """
        message = data.decode()
        if message.startswith('FILE'):
            _, file_size, username, file_name = message.split('#')
            file_size = int(file_size)
            file_path = os.path.join(SAVING_DIR, file_name)
            total = 0
            try:
                with open(file_path, 'wb') as f:
                    while total < file_size:
                        data = self.server_socket.recv(BUF_SIZE)
                        total = total + len(data)
                        f.write(data)
            except FileExistsError as ex:
                print(ex)
            self.print_message(username + ' отправил файл ' + file_name)
        else:
            self.print_message(data.decode())

    def print_message(self, text: str):
        """
        Печать целого сообщения в чате клиента
        """
        self.lock.acquire()
        self.data['text'].append(text)
        self.lock.release()

    def send_text(self, text: str):
        """
        Отправка текстового сообщения
        """
        data = ('TEXT' + '#' + text).encode()
        self.server_socket.send(data)

    def send_file(self, filepath: str, progressbar):
        """
        Отправка файла
        """
        file_size = os.path.getsize(filepath)
        add_part_size = self.__limit / file_size * 100
        sent_size = 0
        data = ('FILE' + '#' + str(file_size) + '#' + os.path.basename(filepath)).encode()
        self.server_socket.send(data)
        time.sleep(TIMEOUT)
        with open(filepath, 'rb') as f:
            file_part = f.read(self.__limit)
            while file_part:
                self.server_socket.send(file_part)
                time.sleep(TIMEOUT)
                file_part = f.read(self.__limit)
                sent_size += add_part_size
                progressbar[0] = int(sent_size)