import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

from PyQt6.QtWidgets import QLabel, QProgressBar, QTextBrowser, QSizePolicy
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication

from ui.floating_panel import FloatingPanel


class GPTResponseWindow(FloatingPanel):
    def __init__(self):
        super().__init__(title="", width=1000, height=140, closable=False)

        self.status_label = QLabel("🧠 GPT is thinking")
        self.status_label.setStyleSheet("color: white; font-size: 14px; padding: 4px;")
        self.layout.addWidget(self.status_label)

        self.spinner = QProgressBar(self)
        self.spinner.setRange(0, 0)
        self.spinner.setFixedHeight(4)
        self.spinner.setTextVisible(False)
        self.spinner.hide()
        self.layout.addWidget(self.spinner)

        self.browser = QTextBrowser(self)
        self.browser.setStyleSheet("""
            background-color: transparent;
            color: white;
            font-size: 18px;
            font-family: 'Segoe UI', sans-serif;
            line-height: 1.5;
            border: none;
        """)
        self.browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.browser.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        self.browser.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.browser.hide()
        self.layout.addWidget(self.browser)

        self.dots = 0
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_thinking)
        self.timer.start()

        self.typewriter_timer = QTimer(self)
        self.typewriter_timer.setInterval(10)
        self.typewriter_timer.timeout.connect(self.typewriter_effect)
        self.full_html = ""
        self.typewriter_index = 0

    def update_thinking(self):
        self.dots = (self.dots + 1) % 4
        self.status_label.setText("🧠 GPT is thinking" + "." * self.dots)

    def show_response(self, text: str):
        self.timer.stop()
        self.spinner.hide()
        self.status_label.hide()
        self.browser.setHtml("")
        self.browser.show()
        self.full_html = self.render_markdown(text)
        self.typewriter_index = 0
        self.typewriter_timer.start()

    def typewriter_effect(self):
        if self.typewriter_index >= len(self.full_html):
            self.typewriter_timer.stop()
            return
        self.typewriter_index += 12
        self.browser.setHtml(self.full_html[: self.typewriter_index])
        doc = self.browser.document()
        doc.adjustSize()
        doc.setTextWidth(self.browser.viewport().width())
        h = int(doc.size().height()) + 60
        max_h = QGuiApplication.primaryScreen().availableGeometry().height() - 100
        h = min(h, max_h)
        geom = self.geometry()
        self.setGeometry(geom.x(), geom.y(), geom.width(), h)
        self.bg.setGeometry(0, 0, geom.width(), h)

    def render_markdown(self, text: str) -> str:
        formatter = HtmlFormatter(noclasses=True, style="monokai")
        code_block_re = r"```(\\w+)?\\n(.*?)```"
        for lang, code in re.findall(code_block_re, text, re.DOTALL):
            try:
                lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
                highlighted = highlight(code, lexer, formatter)
                wrapped = (
                    '<div style="background:#1e1e1e; padding:6px; '
                    'border-radius:6px; margin:8px 0;">'
                    + highlighted +
                    '</div>'
                )
                text = text.replace(f"```{lang}\\n{code}```", wrapped)
            except Exception:
                continue
        html_body = markdown.markdown(text, extensions=["extra", "sane_lists"])
        return (
            '<div style="white-space: pre-wrap; color: white; '
            'font-family: Segoe UI, sans-serif; font-size: 18px; '
            'line-height: 1.6;">' + html_body + '</div>'
        )
