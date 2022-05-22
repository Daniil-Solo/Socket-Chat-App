import os.path
import socket
import threading
import time

from code.utils import from_dict_to_bytes, from_bytes_to_message, MsgInfo, calculate_limit
from code.storage import Storage
from code.configs import BUF_SIZE, KEY_PHRASE, SERVER_PORT, TIMEOUT


SAVING_DIR = os.path.join(os.getcwd(), '../my_saves')


class Client:
    def __init__(self, username):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__socket.settimeout(0.1)
        self.__server_address = None
        self.__msgs_of_client = Storage(SAVING_DIR)
        self.__username = username
        self.__limit = calculate_limit(self.__username)
        self.connected = True

    def __get_server_address(self):
        """
        Получение адреса сервера
        """
        self.__socket.sendto(KEY_PHRASE.encode(), ('<broadcast>', SERVER_PORT))
        while True:
            data, server = self.__socket.recvfrom(BUF_SIZE)
            if data:
                self.__server_address = server
                break

    def start(self):
        """
        Запуск цикла обработки сообщений
        """
        self.__get_server_address()
        threading.Thread(target=self.__loop).start()

    def __loop(self):
        """
        Цикл обработки сообщений
        """
        while self.connected:
            try:
                data, server = self.__socket.recvfrom(BUF_SIZE)
            except socket.timeout:
                continue
            msg = from_bytes_to_message(data)
            self.__handle_new_message(msg)

    def __handle_new_message(self, message: MsgInfo):
        """
        Обработка нового сообщения
        """
        if message.type != 'h':
            if message.user not in self.__msgs_of_client:
                self.__msgs_of_client[message.user] = message.data
            else:
                self.__msgs_of_client.add(message.user, message.data)

        if message.is_end:
            self.print_message(message)

    def print_message(self, message: MsgInfo):
        """
        Печать целого сообщения в чат клиента
        """
        print(message.user, ":")
        if message.type == 't':
            with open(self.__msgs_of_client[message.user], 'rb') as f:
                bin_string = f.read(BUF_SIZE)
                while bin_string:
                    text_string = bin_string.decode()
                    print(text_string)
                    bin_string = f.read(BUF_SIZE)
        elif message.type == 'h':
            filepath = self.__msgs_of_client[message.user]
            os.rename(filepath, os.path.join(SAVING_DIR, message.data.decode()))
            print("Файл", message.data.decode())
        del self.__msgs_of_client[message.user]

    def send_text(self, text: str):
        """
        Отправка текстового сообщения
        """
        i = 0
        while i <= len(text):
            data = from_dict_to_bytes({
                'user': self.__username,
                'data': text[i: i + self.__limit],
                'is_end': 1 if i + self.__limit > len(text) else 0,
                'type': 't'
            })
            i += self.__limit
            self.__socket.sendto(data, self.__server_address)
            time.sleep(TIMEOUT)

    def send_file(self, filepath: str):
        """
        Отправка файла
        """
        with open(filepath, 'rb') as f:
            file_part = f.read(self.__limit)
            # print('limit', self.limit)
            # print('filepart', len(file_part))
            while file_part:
                data = from_dict_to_bytes({
                    'user': self.__username,
                    'data': file_part,
                    'is_end': 0,
                    'type': 'f'
                })
                # print('dict', data)
                # print('data', len(data))
                self.__socket.sendto(data, self.__server_address)
                time.sleep(TIMEOUT)
                file_part = f.read(self.__limit)
        data = from_dict_to_bytes({
            'user': self.__username,
            'data': os.path.basename(filepath),
            'is_end': 1,
            'type': 'h'
        })
        # print('end', data)
        self.__socket.sendto(data, self.__server_address)
