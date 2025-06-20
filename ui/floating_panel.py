import sys
import time
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QTextEdit, QComboBox, QCheckBox,
)
from PyQt6.QtCore import Qt, QTimer, QObject, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QGuiApplication, QMouseEvent, QShortcut

from audio.recorder import AudioRecorder
from whisper.transcriber import Transcriber
from utils.text_helpers import (
    load_prompt, load_terms, ensure_russian_request, correct_tech_terms
)
from groq.client import ask_groq
from ui.response_window import GPTResponseWindow
from ui.edit_dialog import EditDialog


class FloatingPanel(QWidget):
    def __init__(self, title, width=200, height=180, closable=True):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(width, height)

        self.bg = QWidget(self)
        self.bg.setStyleSheet("background-color: rgba(40, 40, 40, 200); border-radius: 28px;")
        self.bg.setGeometry(0, 0, width, height)

        self.layout = QVBoxLayout(self.bg)
        self.layout.setContentsMargins(16, 50, 16, 16)
        self.layout.setSpacing(8)

        self.title_icon = QLabel(self.bg)
        pixmap = QPixmap("icon.png").scaledToHeight(20, Qt.TransformationMode.SmoothTransformation)
        self.title_icon.setPixmap(pixmap)
        self.title_icon.move(16, 14)

        self.title_label = QLabel(title, self.bg)
        self.title_label.setStyleSheet("color: white; font-size: 14px;")
        self.title_label.move(46, 14)

        if closable:
            self.close_btn = QPushButton("✖", self.bg)
            self.close_btn.setStyleSheet("background-color: rgba(255,255,255,40); border:none; border-radius:12px;")
            self.close_btn.setFixedSize(24, 24)
            self.close_btn.move(width - 40, 10)
            self.close_btn.clicked.connect(QApplication.quit)

        self._drag_pos = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if (event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

    def center_on_screen(self, y_offset=0):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - self.width() // 2, screen.top() + y_offset)


class MainController(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon("icon.icns"))

        self.prompt_system = load_prompt("prompt/system.md")
        self.prompt_legend = load_prompt("prompt/legend.md")
        self.technical_terms = load_terms("prompt/technical_terms.txt")

        self.chat_history = []
        self.history_records = []
        self.response_window = None
        self.transcriber = Transcriber()

        self.top_bar = FloatingPanel("Aisly", width=350)
        self.layout = self.top_bar.layout
        self.top_bar.center_on_screen(y_offset=40)

        self.edit_box = QTextEdit()
        self.edit_box.setStyleSheet("font-size: 16px; background: #2a2a2a; color: white; padding: 4px;")
        self.edit_box.hide()
        self.layout.addWidget(self.edit_box)

        self.resend_btn = QPushButton("↻ Отправить с изменениями")
        self.resend_btn.clicked.connect(self.resend_modified_query)
        self.resend_btn.hide()
        self.layout.addWidget(self.resend_btn)

        self.history_menu = QComboBox()
        self.history_menu.addItem("История запросов")
        self.history_menu.currentIndexChanged.connect(self.on_history_selected)
        self.layout.addWidget(self.history_menu)

        self.edit_btn = QPushButton("✏ Редактировать запрос")
        self.edit_btn.clicked.connect(self.show_edit_dialog)
        self.layout.addWidget(self.edit_btn)

        self.use_legend_checkbox = QCheckBox("Включить легенду")
        self.use_legend_checkbox.setChecked(True)
        self.layout.addWidget(self.use_legend_checkbox)

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.start_streaming)
        self.layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_streaming)
        self.stop_btn.hide()
        self.layout.addWidget(self.stop_btn)

        self.toggle_resp_btn = QPushButton("🪄 Показать/скрыть ответ")
        self.toggle_resp_btn.clicked.connect(self.toggle_response_window)
        self.layout.addWidget(self.toggle_resp_btn)

        self.recorder = AudioRecorder(self.process_audio)
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.check_silence)

        # Shortcuts
        self.start_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.top_bar, self.start_streaming)
        self.clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self.top_bar, self.clear_history)
        self.hide_shortcut = QShortcut(QKeySequence("Meta+H"), self.top_bar,
                                       lambda: [w.hide() for w in QApplication.topLevelWidgets()])
        self.toggle_resp_shortcut = QShortcut(QKeySequence("Ctrl+H"), self.top_bar, self.toggle_response_window)

        self.top_bar.show()

    def build_chat_history(self) -> list:
        history = [{"role": "system", "content": self.prompt_system}]
        if self.use_legend_checkbox.isChecked():
            history.append({"role": "system", "content": self.prompt_legend})
        return history

    def start_streaming(self):
        self.recorder.start()
        self.start_btn.hide()
        self.stop_btn.show()
        self.timer.start()

    def stop_streaming(self):
        self.recorder.stop()
        self.start_btn.show()
        self.stop_btn.hide()
        self.timer.stop()

    def check_silence(self):
        # можно расширить по времени молчания
        if self.recorder.audio_data:
            audio = np.concatenate(self.recorder.audio_data)
            self.recorder.audio_data.clear()
            self.process_audio(audio)

    def process_audio(self, audio):
        if not self.response_window:
            self.response_window = GPTResponseWindow()
            self.response_window.center_on_screen(y_offset=180)
            self.response_window.show()

        user_text = self.transcriber.transcribe(audio)
        user_text = correct_tech_terms(user_text)
        user_text = ensure_russian_request(user_text)

        self.chat_history = self.build_chat_history()
        self.chat_history.append({"role": "user", "content": user_text})
        self.history_records.append([user_text, None])
        self.history_menu.addItem(f"Запрос {len(self.history_records)}")
        self.ask_groq()

    def ask_groq(self):
        self.response_window.spinner.show()
        self.response_window.status_label.show()
        messages = list(self.chat_history)

        class GroqWorker(QObject):
            finished = pyqtSignal(str)
            def run(self_inner):
                reply = ask_groq(messages)
                self_inner.finished.emit(reply)

        self._groq_thread = QThread()
        self._groq_worker = GroqWorker()
        self._groq_worker.moveToThread(self._groq_thread)
        self._groq_thread.started.connect(self._groq_worker.run)
        self._groq_worker.finished.connect(self.on_groq_finished)
        self._groq_worker.finished.connect(self._groq_thread.quit)
        self._groq_worker.finished.connect(self._groq_worker.deleteLater)
        self._groq_thread.finished.connect(self._groq_thread.deleteLater)
        self._groq_thread.start()

    def on_groq_finished(self, reply: str):
        idx = len(self.history_records) - 1
        self.history_records[idx][1] = reply
        self.chat_history.append({"role": "assistant", "content": reply})
        self.response_window.spinner.hide()
        self.response_window.show_response(reply)

    def resend_modified_query(self):
        edited = self.edit_box.toPlainText().strip()
        if not edited:
            return
        edited = ensure_russian_request(correct_tech_terms(edited))
        self.chat_history = self.build_chat_history()
        self.chat_history.append({"role": "user", "content": edited})
        self.history_records.append([edited, None])
        self.history_menu.addItem(f"Запрос {len(self.history_records)}")
        self.ask_groq()

    def on_history_selected(self, idx: int):
        if idx <= 0 or idx > len(self.history_records):
            return
        q, a = self.history_records[idx - 1]
        html = f"<b>Вопрос:</b> {q}\n\n<b>Ответ:</b>\n{a or '(ответ ещё не получен)'}"
        self.response_window.show_response(html)

    def show_edit_dialog(self):
        idx = self.history_menu.currentIndex()
        if idx <= 0 or idx > len(self.history_records):
            return
        q, _ = self.history_records[idx - 1]
        dialog = EditDialog(q)
        if dialog.exec() == dialog.DialogCode.Accepted:
            edited = dialog.get_text().strip()
            if edited:
                edited = ensure_russian_request(correct_tech_terms(edited))
                self.chat_history = self.build_chat_history()
                self.chat_history.append({"role": "user", "content": edited})
                self.history_records.append([edited, None])
                self.history_menu.addItem(f"Запрос {len(self.history_records)}")
                self.ask_groq()

    def clear_history(self):
        self.history_records.clear()
        self.history_menu.clear()
        self.history_menu.addItem("История запросов")

    def toggle_response_window(self):
        if not self.response_window:
            return
        if self.response_window.isVisible():
            self.response_window.hide()
        else:
            self.response_window.show()

    def run(self):
        sys.exit(self.app.exec())
