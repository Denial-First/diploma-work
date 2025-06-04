import sys
import asyncio
from copy import copy
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QComboBox,
                               QGroupBox, QFormLayout, QLineEdit, QSystemTrayIcon)
from PySide6.QtCore import Qt, QTimer
import os
from dotenv import load_dotenv
import qasync
from telegram_processing import TelegramBotHandler
from message_processing import TelegramAttackDetector

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class ScannerApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__active_scan = False
        self.__current_scanner = None
        self.message_list = []
        self.__initUI()
        self.__spam_detector = None

    def __initUI(self):
        self.setWindowTitle("Information attack detector")
        self.setMinimumSize(450, 320)
        mainWidget = QWidget()
        self.mainLayout = QVBoxLayout(mainWidget)

        configGroup = QGroupBox("Configuration")
        configLayout = QFormLayout()

        self.languageSelector = QComboBox()
        self.languageSelector.addItems([
            "----",
            "English"
        ])
        self.socialNetworkSelector = QComboBox()
        self.socialNetworkSelector.addItems([
            "----",
            "Telegram"
        ])

        self.languageSelector.currentIndexChanged.connect(self.__check_parameters)
        self.socialNetworkSelector.currentIndexChanged.connect(self.__additional_config_show)

        configLayout.addRow("Language:", self.languageSelector)
        configLayout.addRow("Social Network:", self.socialNetworkSelector)
        configGroup.setLayout(configLayout)

        self.statusLabel = QLabel("Ready")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        buttonLayout = QHBoxLayout()
        self.startButton = QPushButton("Start Scanning")
        self.startButton.setMinimumHeight(40)
        self.startButton.setEnabled(False)
        self.startButton.clicked.connect(self.__start_scan)

        self.stopButton = QPushButton("Stop Scanning")
        self.stopButton.setMinimumHeight(40)
        self.stopButton.clicked.connect(self.__stop_scan)
        self.stopButton.setEnabled(False)

        buttonLayout.addWidget(self.startButton)
        buttonLayout.addWidget(self.stopButton)

        self.mainLayout.addWidget(configGroup)
        self.mainLayout.addSpacing(15)
        self.mainLayout.addWidget(self.statusLabel)
        self.mainLayout.addSpacing(20)
        self.mainLayout.addLayout(buttonLayout)

        self.setCentralWidget(mainWidget)

    def __start_scan(self):
        self.statusLabel.setText(f"Scanning")
        self.__active_scan = True
        chat_id = int(self.chatIdField.text())
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.languageSelector.setEnabled(False)
        self.socialNetworkSelector.setEnabled(False)
        self.chatIdField.setEnabled(False)
        if self.socialNetworkSelector.currentIndex() == 1:
            asyncio.create_task(self.__run_bot_and_detector(chat_id))

    async def __run_bot_and_detector(self, chat_id):
        self.__current_scanner = TelegramBotHandler(
            BOT_TOKEN,
            chat_id,
            self.message_list
        )
        await self.__current_scanner.start()
        participants = await self.__current_scanner.get_participants()

        self.__spam_detector = TelegramAttackDetector(
            self.languageSelector.currentText(),
            participants
        )

        self.poll_timer = QTimer()
        self.poll_timer.setInterval(60000) # check message list with 1m interval
        self.poll_timer.timeout.connect(self.process_incoming_messages)
        self.poll_timer.start()

    def __stop_scan(self):
        if not self.__active_scan:
            return
        self.__active_scan = False
        asyncio.create_task(self.__current_scanner.stop())
        self.__current_scanner = None
        self.__spam_detector = None
        self.message_list = []
        self.poll_timer.stop()
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.languageSelector.setEnabled(True)
        self.socialNetworkSelector.setEnabled(True)
        self.chatIdField.setEnabled(True)
        self.statusLabel.setText(f"Scanning stopped")


    def __check_parameters(self):
        if self.languageSelector.currentIndex() > 0 and self.__check_social_network_data():
            self.startButton.setEnabled(True)
        else:
            self.startButton.setEnabled(False)

    def __additional_config_show(self, index):
        if index == 1:
            self.socialNetworkConfigGroup = QGroupBox("Social Network Configuration")
            socialNetworkConfigLayout = QFormLayout()
            self.chatIdField = QLineEdit()
            self.chatIdField.setMaxLength(20)
            self.chatIdField.textEdited.connect(self.__check_parameters)
            socialNetworkConfigLayout.addRow("Chat ID:", self.chatIdField)
            self.socialNetworkConfigGroup.setLayout(socialNetworkConfigLayout)
            self.mainLayout.insertWidget(1, self.socialNetworkConfigGroup)

        else:
            self.mainLayout.removeWidget(self.socialNetworkConfigGroup)
            self.socialNetworkConfigGroup.setParent(None)
            self.socialNetworkConfigGroup.deleteLater()
        self.__check_parameters()

    def __check_social_network_data(self):
        selected_item = self.socialNetworkSelector.currentIndex()
        if selected_item <= 0:
            return False
        if selected_item == 1:
            if self.chatIdField.text().strip() != '':
                return True
            return False
        return None

    def process_incoming_messages(self):
        if len(self.message_list) >= 5:
            messages_to_check = copy(self.message_list)
            self.message_list.clear()
            asyncio.create_task(self.__get_participants(messages_to_check))

    async def __get_participants(self, messages_to_check):
        participants = await self.__current_scanner.get_participants()

        res = self.__spam_detector.analyze_messages(participants, messages_to_check)
        if res:
            icon=QIcon('icon.jpg')
            tray_icon = QSystemTrayIcon(icon)
            tray_icon.setVisible(True)
            tray_icon.showMessage(
                "Notification Title",
                res,
                QSystemTrayIcon.Information,
                5000
            )


def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    app.setStyle('Fusion')
    app.setApplicationName('Information attack detector')
    window = ScannerApplication()
    window.show()
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()