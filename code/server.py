import socket
import threading
import time

from configs import BUF_SIZE, KEY_PHRASE, SERVER_PORT as PORT, TIMEOUT, SERVER_TCP_PORT

IP = ""


class Server:
    def __init__(self, ip, port, port_tcp):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.bind((ip, port))
        self.socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_tcp.bind((ip, port_tcp))
        self.socket_tcp.listen(10)

        self.clients = dict()
        print("Сервер настроился!")

    def start(self):
        """
        Основной цикл обработки входящих сообщений
        """
        print("Сервер запущен!")
        threading.Thread(target=self.start_tcp).start()
        threading.Thread(target=self.start_udp).start()

    def start_tcp(self):
        while True:
            connection, address = self.socket_tcp.accept()
            print(connection, address)
            threading.Thread(target=self.clientThread, args=(connection, address)).start()

    def start_udp(self):
        while True:
            try:
                data, client = self.socket.recvfrom(BUF_SIZE)
            except socket.error:
                pass
            else:
                if data[: len(KEY_PHRASE)].decode() == KEY_PHRASE:
                    print('Сервер отправил свой адрес клиенту: ')
                    self.socket.sendto(KEY_PHRASE.encode(), client)
                    continue

    def clientThread(self, connection, client):
        data = connection.recv(BUF_SIZE)
        self.clients[client] = (data.decode(), connection)

        while True:
            try:
                data = connection.recv(BUF_SIZE)
                self.handle_new_data(data, client, connection)
            except Exception as e:
                print(e)
                break

    def handle_new_data(self, data: bytes, client: tuple, connection):
        """
        Обработка нового сообщения
        """
        username = self.clients[client][0]
        other_connections = [(self.clients[c][1], c) for c in self.clients.keys() if c != client]

        if data[:4].decode() == 'TEXT':
            _, text = data.decode().split('#')
            new_data = (username + ': ' + text).encode()
            self.send_data_to_connections(new_data, other_connections)
        elif data[:4].decode() == 'FILE':
            _, file_size, filename = data.decode().split('#')
            new_data = ('FILE#' + file_size + '#' + username + '#' + filename).encode()
            self.send_data_to_connections(new_data, other_connections)
            total = 0
            file_size = int(file_size)
            while total < file_size:
                new_data = connection.recv(BUF_SIZE)
                total = total + len(new_data)
                self.send_data_to_connections(new_data, other_connections)

    def send_data_to_connections(self, data, connections):
        """
        Отправка сообщения на все подключения
        """
        for some_connection, some_client in connections:
            try:
                some_connection.send(data)
            except:
                some_connection.close()
                self.remove_connection(some_client)

    def remove_connection(self, client):
        del self.clients[client]


if __name__ == "__main__":
    server = Server(IP, PORT, SERVER_TCP_PORT)
    server.start()
