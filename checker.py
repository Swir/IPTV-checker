import asyncio
import aiohttp
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPlainTextEdit,
    QPushButton, QWidget, QLabel, QMessageBox, QProgressDialog, QFileDialog,
    QListWidget, QListWidgetItem, QHBoxLayout, QComboBox
)

class IPTVProgram(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPTV Rozpierdalacz checker by Swir 1.0")
        self.setGeometry(100, 100, 800, 600)
        self.set_stylesheet()  # Ustawienie arkusza stylów

        main_layout = QVBoxLayout()

        self.url_input = QPlainTextEdit()
        self.url_input.setPlaceholderText("Wprowadź linki do listy IPTV (oddzielone nową linią)")
        main_layout.addWidget(self.url_input)

        filter_layout = QHBoxLayout()
        self.filter_label = QLabel("Filtruj kanały:")
        self.filter_input = QPlainTextEdit()
        self.filter_input.setFixedHeight(30)  # Ustawienie stałej wysokości pola filtrującego
        self.filter_input.setPlaceholderText("Wprowadź fragment nazwy kanału")
        filter_layout.addWidget(self.filter_label)
        filter_layout.addWidget(self.filter_input)
        main_layout.addLayout(filter_layout)

        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Wczytaj")
        self.load_button.clicked.connect(self.load_channels)
        button_layout.addWidget(self.load_button)

        self.download_button = QPushButton("Pobierz playlistę")
        self.download_button.clicked.connect(self.download_playlist)
        button_layout.addWidget(self.download_button)

        self.play_button = QPushButton("Odtwórz w VLC")
        self.play_button.clicked.connect(self.play_in_vlc)
        button_layout.addWidget(self.play_button)

        main_layout.addLayout(button_layout)

        self.combo_box = QComboBox()
        self.combo_box.currentIndexChanged.connect(self.populate_channels)
        main_layout.addWidget(self.combo_box)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget(self.scroll_area)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        self.vlc_path = ""
        self.vlc_label = QLabel("VLC Path: None")
        self.vlc_label.setStyleSheet("color: white;")
        main_layout.addWidget(self.vlc_label)
        self.select_vlc_button = QPushButton("Wybierz VLC")
        self.select_vlc_button.clicked.connect(self.select_vlc_path)
        main_layout.addWidget(self.select_vlc_button)

        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(main_layout)

        self.all_channels = {}

    def set_stylesheet(self):
        style_sheet = """
        QMainWindow {
            background-color: #222;
        }
        QLabel {
            color: white;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPlainTextEdit, QComboBox {
            background-color: #333;
            color: white;
            border: 1px solid #555;
        }
        QScrollArea {
            background-color: #333;
            border: 1px solid #555;
        }
        QListWidget {
            background-color: #444;
            border: none;
        }
        QListWidget::item {
            padding: 5px;
        }
        """
        self.setStyleSheet(style_sheet)

    async def get_iptv_channels(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.text()
                        lines = data.splitlines()
                        channels = []
                        current_group = "SWIRTVTEAM"

                        for line in lines:
                            if line.startswith("#EXTINF:"):
                                channel = line.split(",")[-1]
                                channels.append((current_group, channel, True))
                            elif line.startswith("#EXTGRP:"):
                                current_group = line.replace("#EXTGRP:", "").strip()

                        return channels
                    else:
                        return None
        except Exception as e:
            return None

    def populate_channels(self):
        selected_url = self.combo_box.currentText()
        if selected_url:
            channels = self.all_channels.get(selected_url, [])
            self.scroll_layout.removeWidget(self.scroll_content)
            self.scroll_content.deleteLater()
            self.scroll_content = QWidget(self.scroll_area)
            self.scroll_layout = QVBoxLayout(self.scroll_content)

            filter_text = self.filter_input.toPlainText().lower()

            for group, channel, is_working in channels:
                if filter_text in channel.lower():
                    item_text = f"{group} - {channel}"
                    label = QLabel(item_text)
                    if not is_working:
                        label.setStyleSheet("color: red; background-color: black;")
                    else:
                        label.setStyleSheet("color: black; background-color: white;")
                    self.scroll_layout.addWidget(label)

            self.scroll_area.setWidget(self.scroll_content)
            self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
# ...

    async def load_channels_async(self, urls):
        self.progress_dialog = QProgressDialog("Pobieranie kanałów...", None, 0, len(urls), self)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_dialog.show()

        self.all_channels.clear()

        for i, url in enumerate(urls):
            channels = await self.get_iptv_channels(url)
            if channels is not None:
                self.all_channels[url] = channels
                self.combo_box.addItem(url)
            else:
                self.all_channels[url] = [("Błąd: nie można pobrać danych", "", False)]
            self.progress_dialog.setValue(i + 1)

        self.progress_dialog.close()

    def load_channels(self):
        urls = self.url_input.toPlainText().splitlines()
        if not urls:
            QMessageBox.warning(self, "Błąd", "Wprowadź linki IPTV.")
            return

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.load_channels_async(urls))
        self.populate_channels()

    def select_vlc_path(self):
        options = QFileDialog.Options()
        vlc_path, _ = QFileDialog.getOpenFileName(self, "Wybierz VLC", "", "Executable Files (*.exe);;All Files (*)", options=options)
        if vlc_path:
            self.vlc_path = vlc_path
            self.vlc_label.setText(f"VLC Path: {self.vlc_path}")

    def download_playlist(self):
        selected_url = self.combo_box.currentText()
        if selected_url:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Zapisz playlistę", "", "M3U Files (*.m3u);;All Files (*)", options=options)
            if file_name:
                playlist_url = selected_url
                playlist_content = asyncio.run(self.get_playlist_content(playlist_url))
                if playlist_content:
                    with open(file_name, 'w', encoding='utf-8') as file:
                        file.write(playlist_content)
                    QMessageBox.information(self, "Sukces", "Playlistę zapisano pomyślnie!")

    async def get_playlist_content(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        return None
        except Exception as e:
            return None

    def play_in_vlc(self):
        selected_url = self.combo_box.currentText()
        if selected_url and hasattr(self, 'vlc_path'):
            playlist_url = selected_url
            subprocess.Popen([self.vlc_path, playlist_url])
        else:
            QMessageBox.warning(self, "Błąd", "Wybierz ścieżkę do programu VLC.")

if __name__ == "__main__":
    app = QApplication([])
    program = IPTVProgram()
    program.show()
    app.exec_()
