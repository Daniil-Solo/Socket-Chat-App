import os.path
import socket
import time

from utils import calculate_limit
from storage import Storage
from configs import BUF_SIZE, KEY_PHRASE, SERVER_PORT, TIMEOUT


SAVING_DIR = os.path.join(os.getcwd(), './my_saves')


class Client:
    def __init__(self, username, lock):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__socket.settimeout(TIMEOUT)
        self.server_address = None
        self.__msgs_of_client = Storage(SAVING_DIR)
        self.__username = username
        self.__limit = calculate_limit(self.__username)
        self.connected = True
        self.data = None
        self.lock = lock
        self.file_waiting_from_username = ''

    def get_server_address(self):
        """
        Получение адреса сервера
        """
        self.__socket.sendto((KEY_PHRASE + self.__username).encode(), ('<broadcast>', SERVER_PORT))
        while True:
            data, server = self.__socket.recvfrom(BUF_SIZE)
            if data:
                self.server_address = server
                break

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
            try:
                data, server = self.__socket.recvfrom(BUF_SIZE)
            except socket.timeout as ex:
                pass
            except ConnectionResetError as ex:
                print(ex)
                pass
            else:
                print('клиент получил новое сообщение', data[:15])
                self.__handle_new_data(data)
        self.__socket.close()

    def __handle_new_data(self, data: bytes):
        """
        Обработка нового сообщения
        """
        if self.file_waiting_from_username != '':
            print('клиент ожидает файлов')
            try:
                part_msg = data[:4].decode()
                if part_msg == 'FEND':
                    print('клиент получил конец файла')
                    self.wait_file = ''
                    filename = data.decode().split('FEND')[1]
                    filepath = self.__msgs_of_client[self.file_waiting_from_username]
                    try:
                        os.rename(filepath, os.path.join(SAVING_DIR, filename))
                        del self.__msgs_of_client[self.file_waiting_from_username]
                    except FileExistsError as ex:
                        print(ex)
                    print('клиент вывел сообщение о полученном файле', filename)
                    self.print_message(self.file_waiting_from_username + ' отправил файл ' + filename)
                else:
                    print('клиент получил часть файла')
                    if self.file_waiting_from_username not in self.__msgs_of_client:
                        print('Это часть была первой')
                        self.__msgs_of_client[self.file_waiting_from_username] = data
                    else:
                        print('Это часть была в середине')
                        self.__msgs_of_client.add(self.file_waiting_from_username, data)
            except UnicodeDecodeError:
                print('клиент получил часть файла')
                if self.file_waiting_from_username not in self.__msgs_of_client:
                    print('Это часть была первой')
                    self.__msgs_of_client[self.file_waiting_from_username] = data
                else:
                    print('Это часть была в середине')
                    self.__msgs_of_client.add(self.file_waiting_from_username, data)
        else:
            print('клиент не ждет файлов')
            try:
                part_msg = data[:100].decode()
                if part_msg.find('FILE') != -1:
                    print('клиент начинает ждать файл от', part_msg.split('FILE')[0])
                    self.file_waiting_from_username = part_msg.split('FILE')[0]
                else:
                    print('клиент вывел текстовое сообщение')
                    self.print_message(data.decode())
            except UnicodeDecodeError:
                print('клиент получил часть файла')
                if self.file_waiting_from_username not in self.__msgs_of_client:
                    print('Это часть была первой')
                    self.__msgs_of_client[self.file_waiting_from_username] = data
                else:
                    print('Это часть была в середине')
                    self.__msgs_of_client.add(self.file_waiting_from_username, data)

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
        data = ('t' + text).encode()
        self.__socket.sendto(data, self.server_address)

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
                self.__socket.sendto(file_part, self.server_address)
                time.sleep(TIMEOUT)
                file_part = f.read(self.__limit)
                sent_size += add_part_size
                progressbar[0] = int(sent_size)
        data = ('FEND' + os.path.basename(filepath)).encode()
        self.__socket.sendto(data, self.server_address)