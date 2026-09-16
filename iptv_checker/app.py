from __future__ import annotations

import asyncio
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from threading import Event
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QSettings, Qt, QThreadPool, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDoubleSpinBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from . import __version__
from .i18n import Translator
from .models import Channel
from .network import check_streams, load_sources
from .parser import build_m3u, deduplicate_channels, redact_url
from .theme import MATRIX_BLUE_STYLESHEET


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    done = Signal()


class CoroutineWorker(QRunnable):
    def __init__(self, factory: Callable[[], object]):
        super().__init__()
        self.factory = factory
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            self.signals.result.emit(asyncio.run(self.factory()))
        except Exception as exc:
            self.signals.error.emit(str(exc))
        finally:
            self.signals.done.emit()


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative


def detect_vlc() -> str:
    candidates: list[str] = []
    if shutil.which("vlc"):
        candidates.append(shutil.which("vlc") or "")
    if sys.platform.startswith("win"):
        candidates += [r"C:\Program Files\VideoLAN\VLC\vlc.exe", r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"]
    elif sys.platform == "darwin":
        candidates.append("/Applications/VLC.app/Contents/MacOS/VLC")
    else:
        candidates += ["/usr/bin/vlc", "/usr/local/bin/vlc", "/snap/bin/vlc"]
    return next((path for path in candidates if path and Path(path).exists()), "")


class StatCard(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        label = QLabel(title)
        label.setObjectName("statTitle")
        self.value = QLabel("0")
        self.value.setObjectName("statValue")
        layout.addWidget(label)
        layout.addWidget(self.value)


class IPTVCheckerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("SWIR", "IPTV Checker")
        self.t = Translator(self.settings.value("language", None))
        self.thread_pool = QThreadPool.globalInstance()
        self.channels: list[Channel] = []
        self.row_channel_map: list[Channel] = []
        self.cancel_event = Event()
        self.is_busy = False

        self.setWindowTitle(self.t("app_title"))
        self.resize(1420, 860)
        self.setMinimumSize(1080, 680)
        self.setAcceptDrops(True)
        self.setStyleSheet(MATRIX_BLUE_STYLESHEET)
        icon = resource_path("assets/icon.svg")
        if icon.exists():
            self.setWindowIcon(QIcon(str(icon)))

        self._build_ui()
        self._restore_settings()
        self.statusBar().showMessage(self.t("ready"))

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(14)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(330)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 18, 18, 18)
        side.setSpacing(9)

        brand = QLabel("IPTV CHECKER")
        brand.setObjectName("brand")
        subtitle = QLabel(f"v{__version__} • Matrix Blue • by Swir")
        subtitle.setObjectName("subtitle")
        side.addWidget(brand)
        side.addWidget(subtitle)
        side.addSpacing(8)

        side.addWidget(QLabel(self.t("sources")))
        self.sources_edit = QPlainTextEdit()
        self.sources_edit.setPlaceholderText(self.t("sources_hint"))
        self.sources_edit.setMinimumHeight(165)
        side.addWidget(self.sources_edit)

        self.add_file_button = QPushButton(self.t("add_file"))
        self.load_button = QPushButton(self.t("load"))
        self.load_button.setObjectName("primary")
        self.check_button = QPushButton(self.t("check"))
        self.check_button.setObjectName("primary")
        self.stop_button = QPushButton(self.t("stop"))
        self.stop_button.setObjectName("danger")
        self.stop_button.setEnabled(False)
        self.add_file_button.clicked.connect(self.add_local_files)
        self.load_button.clicked.connect(self.load_playlists)
        self.check_button.clicked.connect(self.check_all_streams)
        self.stop_button.clicked.connect(self.stop_check)
        for button in (self.add_file_button, self.load_button, self.check_button, self.stop_button):
            side.addWidget(button)

        options = QGridLayout()
        options.addWidget(QLabel(self.t("workers")), 0, 0)
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 8)
        self.workers_spin.setValue(6)
        options.addWidget(self.workers_spin, 0, 1)
        options.addWidget(QLabel(self.t("timeout")), 1, 0)
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(2.0, 30.0)
        self.timeout_spin.setValue(8.0)
        self.timeout_spin.setSingleStep(1.0)
        options.addWidget(self.timeout_spin, 1, 1)
        side.addLayout(options)

        self.dedupe_button = QPushButton(self.t("remove_duplicates"))
        self.save_button = QPushButton(self.t("save_playlist"))
        self.export_button = QPushButton(self.t("export"))
        self.play_button = QPushButton(self.t("play"))
        self.dedupe_button.clicked.connect(self.remove_duplicates)
        self.save_button.clicked.connect(self.save_filtered_playlist)
        self.export_button.clicked.connect(self.export_report)
        self.play_button.clicked.connect(self.play_selected)
        for button in (self.dedupe_button, self.save_button, self.export_button, self.play_button):
            side.addWidget(button)

        side.addSpacing(5)
        side.addWidget(QLabel(self.t("vlc")))
        self.vlc_label = QLabel("—")
        self.vlc_label.setObjectName("subtitle")
        self.vlc_label.setWordWrap(True)
        self.vlc_button = QPushButton(self.t("select_vlc"))
        self.vlc_button.clicked.connect(self.select_vlc)
        side.addWidget(self.vlc_label)
        side.addWidget(self.vlc_button)
        side.addStretch(1)
        hint = QLabel(self.t("drag_hint"))
        hint.setWordWrap(True)
        hint.setObjectName("subtitle")
        legal = QLabel(self.t("legal"))
        legal.setWordWrap(True)
        legal.setObjectName("subtitle")
        side.addWidget(hint)
        side.addWidget(legal)
        root_layout.addWidget(sidebar)

        content = QVBoxLayout()
        content.setSpacing(10)
        root_layout.addLayout(content, 1)

        stats = QHBoxLayout()
        self.card_total = StatCard(self.t("total"))
        self.card_online = StatCard(self.t("status_online"))
        self.card_offline = StatCard(self.t("status_offline"))
        self.card_untested = StatCard(self.t("status_untested"))
        for card in (self.card_total, self.card_online, self.card_offline, self.card_untested):
            stats.addWidget(card)
        content.addLayout(stats)

        filters = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self.t("search"))
        self.group_combo = QComboBox()
        self.status_combo = QComboBox()
        self.status_combo.addItem(self.t("all_status"), "all")
        self.status_combo.addItem(self.t("untested"), "untested")
        self.status_combo.addItem(self.t("online"), "online")
        self.status_combo.addItem(self.t("offline"), "offline")
        self.status_combo.addItem(self.t("cancelled"), "cancelled")
        self.search_edit.textChanged.connect(self.refresh_table)
        self.group_combo.currentIndexChanged.connect(self.refresh_table)
        self.status_combo.currentIndexChanged.connect(self.refresh_table)
        filters.addWidget(self.search_edit, 1)
        filters.addWidget(self.group_combo)
        filters.addWidget(self.status_combo)
        content.addLayout(filters)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            self.t("col_status"), self.t("col_name"), self.t("col_group"), self.t("col_latency"),
            self.t("col_http"), self.t("col_type"), self.t("col_url")
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        for col in (0, 2, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self.play_selected)
        content.addWidget(self.table, 1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        content.addWidget(self.progress)
        footer = QLabel("by Swir • github.com/Swir • IPTV Checker 2.0")
        footer.setAlignment(Qt.AlignRight)
        footer.setObjectName("subtitle")
        content.addWidget(footer)
        self._rebuild_groups()

    def _restore_settings(self) -> None:
        self.workers_spin.setValue(max(1, min(8, int(self.settings.value("workers", 6)))))
        self.timeout_spin.setValue(max(2.0, min(30.0, float(self.settings.value("timeout", 8.0)))))
        saved = str(self.settings.value("vlc_path", "") or "")
        self.vlc_path = saved if saved and Path(saved).exists() else detect_vlc()
        self.vlc_label.setText(self.vlc_path or "VLC not detected")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.settings.setValue("workers", self.workers_spin.value())
        self.settings.setValue("timeout", self.timeout_spin.value())
        self.settings.setValue("vlc_path", self.vlc_path)
        event.accept()

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self.is_busy = busy
        self.load_button.setEnabled(not busy)
        self.check_button.setEnabled(not busy and bool(self.channels))
        self.stop_button.setEnabled(busy)
        self.progress.setRange(0, 0 if busy else 100)
        if not busy:
            self.progress.setValue(100 if self.channels else 0)
        if text:
            self.statusBar().showMessage(text)

    def _sources(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for line in self.sources_edit.toPlainText().splitlines():
            source = line.strip().strip('"')
            if source and source not in seen:
                seen.add(source)
                result.append(source)
        return result

    def add_local_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, self.t("add_file"), "", "M3U playlist (*.m3u *.m3u8);;All files (*)")
        if files:
            items = self._sources()
            items.extend(file for file in files if file not in items)
            self.sources_edit.setPlainText("\n".join(items))

    def load_playlists(self) -> None:
        if self.is_busy:
            return
        sources = self._sources()
        if not sources:
            QMessageBox.warning(self, self.t("error"), self.t("no_sources"))
            return
        self._set_busy(True, self.t("loading"))
        worker = CoroutineWorker(lambda: load_sources(sources, timeout=max(8.0, self.timeout_spin.value() * 2)))
        worker.signals.result.connect(lambda payload: self._on_loaded(payload, len(sources)))
        worker.signals.error.connect(self._show_error)
        worker.signals.done.connect(lambda: self._set_busy(False))
        self.thread_pool.start(worker)

    def _on_loaded(self, payload: object, source_count: int) -> None:
        channels, errors = payload  # type: ignore[misc]
        self.channels = channels
        self._rebuild_groups()
        self.refresh_table()
        self.statusBar().showMessage(self.t("loaded", count=len(self.channels), sources=source_count))
        if errors:
            text = "\n".join(errors[:8])
            if len(errors) > 8:
                text += f"\n… +{len(errors) - 8} more"
            QMessageBox.warning(self, self.t("error"), text)

    def check_all_streams(self) -> None:
        if self.is_busy:
            return
        if not self.channels:
            QMessageBox.warning(self, self.t("error"), self.t("no_channels"))
            return
        self.cancel_event = Event()
        self._set_busy(True, self.t("checking"))
        worker = CoroutineWorker(lambda: check_streams(self.channels, self.workers_spin.value(), self.timeout_spin.value(), self.cancel_event))
        worker.signals.result.connect(self._on_checked)
        worker.signals.error.connect(self._show_error)
        worker.signals.done.connect(lambda: self._set_busy(False))
        self.thread_pool.start(worker)

    def stop_check(self) -> None:
        self.cancel_event.set()
        self.statusBar().showMessage(self.t("stopped"))

    def _on_checked(self, channels: object) -> None:
        self.channels = channels  # type: ignore[assignment]
        self.refresh_table()
        online = sum(c.status == "online" for c in self.channels)
        offline = sum(c.status == "offline" for c in self.channels)
        self.statusBar().showMessage(self.t("checked", online=online, offline=offline))

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, self.t("error"), message)
        self.statusBar().showMessage(message)

    def _rebuild_groups(self) -> None:
        current = self.group_combo.currentData() if hasattr(self, "group_combo") else "all"
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        self.group_combo.addItem(self.t("all_groups"), "all")
        for group in sorted({channel.display_group for channel in self.channels}, key=str.casefold):
            self.group_combo.addItem(group, group)
        found = self.group_combo.findData(current)
        self.group_combo.setCurrentIndex(found if found >= 0 else 0)
        self.group_combo.blockSignals(False)

    def filtered_channels(self) -> list[Channel]:
        needle = self.search_edit.text().strip().casefold()
        group = self.group_combo.currentData() or "all"
        status = self.status_combo.currentData() or "all"
        result = []
        for channel in self.channels:
            if group != "all" and channel.display_group != group:
                continue
            if status != "all" and channel.status != status:
                continue
            if needle and needle not in channel.name.casefold() and needle not in channel.display_group.casefold():
                continue
            result.append(channel)
        return result

    def refresh_table(self) -> None:
        rows = self.filtered_channels()
        self.row_channel_map = rows
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(rows))
        colors = {"online": QColor("#66e3a4"), "offline": QColor("#ff6f91"), "untested": QColor("#8aa9c2"), "cancelled": QColor("#f4c56b")}
        symbols = {"online": "●", "offline": "●", "untested": "○", "cancelled": "◌"}
        for row, channel in enumerate(rows):
            status_item = QTableWidgetItem(symbols.get(channel.status, "○"))
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(colors.get(channel.status, QColor("#8aa9c2")))
            status_item.setToolTip(channel.error or channel.status)
            values = [
                status_item,
                QTableWidgetItem(channel.name),
                QTableWidgetItem(channel.display_group),
                QTableWidgetItem(f"{channel.latency_ms} ms" if channel.latency_ms is not None else "—"),
                QTableWidgetItem(str(channel.http_status) if channel.http_status is not None else "—"),
                QTableWidgetItem(channel.content_type or "—"),
                QTableWidgetItem(redact_url(channel.url)),
            ]
            for column, item in enumerate(values):
                self.table.setItem(row, column, item)
        self.table.setUpdatesEnabled(True)
        self.update_stats()

    def update_stats(self) -> None:
        self.card_total.value.setText(str(len(self.channels)))
        self.card_online.value.setText(str(sum(c.status == "online" for c in self.channels)))
        self.card_offline.value.setText(str(sum(c.status == "offline" for c in self.channels)))
        self.card_untested.value.setText(str(sum(c.status == "untested" for c in self.channels)))
        self.check_button.setEnabled(bool(self.channels) and not self.is_busy)

    def remove_duplicates(self) -> None:
        before = len(self.channels)
        self.channels = deduplicate_channels(self.channels)
        self._rebuild_groups()
        self.refresh_table()
        self.statusBar().showMessage(f"Removed {before - len(self.channels)} duplicate(s).")

    def _selected_channel(self) -> Channel | None:
        row = self.table.currentRow()
        return self.row_channel_map[row] if 0 <= row < len(self.row_channel_map) else None

    def select_vlc(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, self.t("select_vlc"), "", "Executable (*)")
        if path:
            self.vlc_path = path
            self.vlc_label.setText(path)
            self.settings.setValue("vlc_path", path)

    def play_selected(self, *_args) -> None:
        channel = self._selected_channel()
        if not channel:
            QMessageBox.warning(self, self.t("error"), self.t("no_selection"))
            return
        if not self.vlc_path or not Path(self.vlc_path).exists():
            self.vlc_path = detect_vlc()
        if not self.vlc_path:
            self.select_vlc()
            if not self.vlc_path:
                return
        try:
            subprocess.Popen([self.vlc_path, channel.url], close_fds=os.name != "nt")
        except Exception as exc:
            self._show_error(str(exc))

    def save_filtered_playlist(self) -> None:
        rows = self.filtered_channels()
        if not rows:
            QMessageBox.warning(self, self.t("error"), self.t("no_channels"))
            return
        path, _ = QFileDialog.getSaveFileName(self, self.t("save_playlist"), "filtered_playlist.m3u", "M3U playlist (*.m3u)")
        if path:
            if not path.lower().endswith(".m3u"):
                path += ".m3u"
            Path(path).write_text(build_m3u(rows), encoding="utf-8")
            self.statusBar().showMessage(self.t("saved"))

    def export_report(self) -> None:
        rows = self.filtered_channels()
        if not rows:
            QMessageBox.warning(self, self.t("error"), self.t("no_channels"))
            return
        path, selected = QFileDialog.getSaveFileName(self, self.t("export"), "iptv_report.csv", "CSV (*.csv);;JSON (*.json)")
        if not path:
            return
        data = [{"name": c.name, "group": c.display_group, "status": c.status, "http_status": c.http_status, "latency_ms": c.latency_ms, "content_type": c.content_type, "stream_url": c.url, "source": c.source, "error": c.error} for c in rows]
        if selected.startswith("JSON") or path.lower().endswith(".json"):
            if not path.lower().endswith(".json"):
                path += ".json"
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            if not path.lower().endswith(".csv"):
                path += ".csv"
            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(data[0].keys()))
                writer.writeheader()
                writer.writerows(data)
        self.statusBar().showMessage(self.t("saved"))

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls() and any(Path(url.toLocalFile()).suffix.lower() in {".m3u", ".m3u8"} for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        files = [url.toLocalFile() for url in event.mimeData().urls() if Path(url.toLocalFile()).suffix.lower() in {".m3u", ".m3u8"}]
        items = self._sources()
        items.extend(file for file in files if file and file not in items)
        self.sources_edit.setPlainText("\n".join(items))
        event.acceptProposedAction()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("IPTV Checker")
    app.setOrganizationName("SWIR")
    window = IPTVCheckerWindow()
    window.show()
    return app.exec()
