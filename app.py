import os
import socket
import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit

import interface.design as design
from code.client import Client


class ChatApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self, client):
        super().__init__()
        self.setupUi(self)
        self.client = client
        self.file_path = None
        self.send_msg_btn.clicked.connect(self.send_message)
        self.add_file_btn.clicked.connect(self.add_file)

    def send_message(self):
        if self.file_path:
            self.client.send_file(self.file_path)
        else:
            text = self.message_tb.text()
            self.client.send_text(text)
        self.file_path = None
        self.message_tb.setText('')
        self.label_3.setText('')

    def add_file(self):
        self.file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите файл для передачи")[0]
        self.message_tb.clear()
        self.label_3.setText('прикреплен файл ' + os.path.basename(self.file_path))


def main():
    app = QtWidgets.QApplication([])
    window1 = QtWidgets.QWidget()
    username, ok_pressed = QInputDialog.getText(window1, "Подключение к чату", "Пожалуйста введите ваш логин:")
    if ok_pressed and username:
        client = Client(username)
        try:
            client.start()
            window = ChatApp(client=client)
            window.show()
            sys.exit(app.exec())
        except socket.error:
            QMessageBox.about(window1, "Ошибка", "Не удалось подключиться!")
        finally:
            client.connected = False
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
