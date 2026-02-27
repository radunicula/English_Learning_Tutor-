from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QTextEdit, QPushButton, QSizePolicy, QFrame,
)

ACCENT = "#7c5cbf"
BG = "#0f0f13"
USER_BUBBLE = "#3b2d5e"
ASSISTANT_BUBBLE = "#1e1e2e"
TEXT_COLOR = "#e8e8f0"
TYPING_COLOR = "#888"


class MessageBubble(QFrame):
    def __init__(self, text: str, role: str, parent=None):
        super().__init__(parent)
        self.setObjectName("bubble")
        is_user = role == "user"

        color = USER_BUBBLE if is_user else ASSISTANT_BUBBLE
        radius = "18px 18px 4px 18px" if is_user else "18px 18px 18px 4px"

        self.setStyleSheet(f"""
            #bubble {{
                background-color: {color};
                border-radius: 14px;
                padding: 4px;
            }}
        """)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet(f"color: {TEXT_COLOR}; padding: 8px 14px; background: transparent;")
        label.setFont(QFont("Noto Serif", 11))
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)


class ChatWidget(QWidget):
    message_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area for messages
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(f"background: {BG}; border: none;")

        self._messages_container = QWidget()
        self._messages_container.setStyleSheet(f"background: {BG};")
        self._messages_layout = QVBoxLayout(self._messages_container)
        self._messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._messages_layout.setSpacing(8)
        self._messages_layout.setContentsMargins(16, 16, 16, 16)
        self._messages_layout.addStretch()

        self._scroll.setWidget(self._messages_container)
        layout.addWidget(self._scroll)

        # Typing indicator
        self._typing_label = QLabel("Alex is typing...")
        self._typing_label.setStyleSheet(f"color: {TYPING_COLOR}; font-style: italic; padding: 4px 20px;")
        self._typing_label.setFont(QFont("Noto Serif", 10))
        self._typing_label.hide()
        layout.addWidget(self._typing_label)

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet(f"background: #16161f; border-top: 1px solid #2a2a3a;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(8)

        self._input = QTextEdit()
        self._input.setPlaceholderText("Type your message... (Enter to send, Shift+Enter for new line)")
        self._input.setFixedHeight(60)
        self._input.setFont(QFont("Noto Serif", 11))
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background: #1e1e2e;
                color: {TEXT_COLOR};
                border: 1px solid #3a3a5a;
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        self._input.installEventFilter(self)

        send_btn = QPushButton("Send")
        send_btn.setFixedSize(80, 44)
        send_btn.setFont(QFont("Noto Serif", 11))
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #9070d0; }}
            QPushButton:pressed {{ background: #5a3d9a; }}
        """)
        send_btn.clicked.connect(self._on_send)

        input_layout.addWidget(self._input)
        input_layout.addWidget(send_btn)
        layout.addWidget(input_frame)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        if obj is self._input and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if (key_event.key() == Qt.Key.Key_Return and
                    not (key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def _on_send(self):
        text = self._input.toPlainText().strip()
        if text:
            self._input.clear()
            self.message_submitted.emit(text)

    def add_message(self, text: str, role: str):
        is_user = role == "user"

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)

        bubble = MessageBubble(text, role)
        bubble.setMaximumWidth(680)

        if is_user:
            row_layout.addStretch()
            row_layout.addWidget(bubble)
        else:
            row_layout.addWidget(bubble)
            row_layout.addStretch()

        # Insert before the final stretch
        count = self._messages_layout.count()
        self._messages_layout.insertWidget(count - 1, row)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))

    def set_typing(self, visible: bool):
        if visible:
            self._typing_label.show()
        else:
            self._typing_label.hide()

    def set_input_enabled(self, enabled: bool):
        self._input.setEnabled(enabled)

    def clear_messages(self):
        # Remove all widgets except the final stretch
        while self._messages_layout.count() > 1:
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
