import os.path
import socket
import threading
import time

from code.utils import from_dict_to_bytes, from_bytes_to_message, MsgInfo, calculate_limit
from code.storage import Storage
from code.configs import BUF_SIZE, KEY_PHRASE, SERVER_PORT, TIMEOUT


SAVING_DIR = os.path.join(os.getcwd(), './my_saves')


class Client:
    def __init__(self, username):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__socket.settimeout(0.1)
        self.server_address = None
        self.__msgs_of_client = Storage(SAVING_DIR)
        self.__username = username
        self.__limit = calculate_limit(self.__username)
        self.connected = True
        self.data = None

    def get_server_address(self):
        """
        Получение адреса сервера
        """
        self.__socket.sendto(KEY_PHRASE.encode(), ('<broadcast>', SERVER_PORT))
        while True:
            data, server = self.__socket.recvfrom(BUF_SIZE)
            if data:
                self.server_address = server
                break

    def set_data(self, data):
        self.data = data

    def loop(self):
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
        self.__socket.close()

    def __handle_new_message(self, message: MsgInfo):
        """
        Обработка нового сообщения
        """
        if message.type != 'h':
            if message.user not in self.__msgs_of_client:
                self.__msgs_of_client[message.user] = message.data
            else:
                self.__msgs_of_client.add(message.user, message.data)

        if message.is_end and self.data:
            self.print_message(message)

    def print_message(self, message: MsgInfo):
        """
        Печать целого сообщения в чат клиента
        """
        text = message.user + ": "
        if message.type == 't':
            with open(self.__msgs_of_client[message.user], 'rb') as f:
                bin_string = f.read(BUF_SIZE)
                while bin_string:
                    text_string = bin_string.decode()
                    text += text_string
                    bin_string = f.read(BUF_SIZE)
        elif message.type == 'h':
            filepath = self.__msgs_of_client[message.user]
            os.rename(filepath, os.path.join(SAVING_DIR, message.data.decode()))
            text += "файл " + message.data.decode()
        self.data['text'] += text + "\n"
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
            self.__socket.sendto(data, self.server_address)
            time.sleep(TIMEOUT)

    def send_file(self, filepath: str, progressbar):
        """
        Отправка файла
        """
        file_size = os.path.getsize(filepath)
        add_part_size = self.__limit / file_size * 100
        sent_size = 0
        with open(filepath, 'rb') as f:
            file_part = f.read(self.__limit)
            while file_part:
                data = from_dict_to_bytes({
                    'user': self.__username,
                    'data': file_part,
                    'is_end': 0,
                    'type': 'f'
                })
                self.__socket.sendto(data, self.server_address)
                time.sleep(TIMEOUT)
                file_part = f.read(self.__limit)
                sent_size += add_part_size
                progressbar.setValue(int(sent_size))
        data = from_dict_to_bytes({
            'user': self.__username,
            'data': os.path.basename(filepath),
            'is_end': 1,
            'type': 'h'
        })
        self.__socket.sendto(data, self.server_address)
