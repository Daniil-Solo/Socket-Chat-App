import os
import socket
import sys
import threading

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QMessageBox

import interface.main_window as main_window
import interface.login_window as login_window
import interface.progress_window as progress_window
from code.client import Client
from code.configs import BUF_SIZE
from code.utils import from_bytes_to_message


class ClientThread(QThread):
    data = {
        'status': 'ok',
        'text': ""
    }

    def __init__(self, parent):
        super(ClientThread, self).__init__()
        self.client = parent.client

    def run(self):
        try:
            self.client.get_server_address()
        except socket.error:
            self.data['status'] = 'error'
            return
        self.client.set_data(self.data)
        self.client.loop()


class ChatApp(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    ADD_FILE_1 = '<html><head/><body><p align="center">Прикреплен файл '
    ADD_FILE_2 = '</p></body></html>'
    NO_FILE = "<html><head/><body><p align=\"center\">Нет прикрепленного файла</p></body></html>"

    def __init__(self, client):
        super().__init__()
        self.setupUi(self)
        self.client = client
        self.file_path = None
        self.filename = ''
        self.send_msg_btn.clicked.connect(self.send_message)
        self.add_file_btn.clicked.connect(self.add_file)
        self.remove_file_btn.clicked.connect(self.remove_file)
        self.progress_widget = None
        self.client_thread = ClientThread(self)
        self.client_thread.start()
        self.timer = QTimer()
        self.timer.timeout.connect(self.set_data)
        self.timer.start(500)

    def send_message(self):
        if self.file_path:
            self.chat_tb.appendPlainText('Вы отправили файл: ' + self.filename)
            self.hide()
            self.progress_widget = ProgressWidget(self, self.file_path, self.client)
            self.progress_widget.show()
        else:
            text = self.message_tb.text()
            self.client.send_text(text)
            self.message_tb.clear()
            self.chat_tb.appendPlainText('Вы: ' + text)

    def finish_file_sending(self):
        self.file_path = None
        self.message_tb.clear()
        self.file_lbl.setText(self.NO_FILE)

    def add_file(self):
        self.file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите файл для передачи")[0] or None
        self.message_tb.clear()
        if self.file_path:
            self.filename = os.path.basename(self.file_path)
            if len(self.filename) > 50:
                self.filename = self.filename[:40] + ".." + self.filename[-3:]
            self.file_lbl.setText(self.ADD_FILE_1 + self.filename + self.ADD_FILE_2)
        else:
            self.file_lbl.setText(self.NO_FILE)

    def remove_file(self):
        self.file_path = None
        self.message_tb.clear()
        self.file_lbl.setText(self.NO_FILE)

    def set_data(self):
        if self.client_thread.data.get('status') == 'error':
            QMessageBox.about(self, "Ошибка", "Не удалось подключиться!")
            self.close()
        else:
            text = self.client_thread.data.get('text')
            self.client_thread.data['text'] = ''
            self.chat_tb.appendPlainText(text)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.client.connected = False
        event.accept()


class ProgressWidget(QtWidgets.QWidget, progress_window.Ui_Form):
    def __init__(self, parent: ChatApp, file_path: str, client: Client):
        super().__init__()
        self.setupUi(self)
        self.chat = parent
        self.file_path = file_path
        self.client = client
        self.cancel_loading_btn.clicked.connect(self.cancel_loading)
        threading.Thread(target=self.progress_sending).start()

    def progress_sending(self):
        self.progress.setValue(0)
        self.client.send_file(self.file_path, self.progress)
        self.chat.show()
        self.chat.finish_file_sending()
        self.close()

    def cancel_loading(self):
        pass


class LoginDialog(QtWidgets.QDialog, login_window.Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.chat = None
        self.setupUi(self)
        self.login_btn.clicked.connect(self.connect)

    def connect(self):
        login = self.login_tb.text()
        if login != '':
            client = Client(login)
            self.hide()
            self.chat = ChatApp(client)
            self.chat.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    dialog = LoginDialog()
    dialog.show()
    sys.exit(app.exec())
