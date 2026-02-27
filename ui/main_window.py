from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPainter
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QSplitter, QSystemTrayIcon, QMenu,
)

from ui.chat_widget import ChatWidget
from ui.sidebar_widget import SidebarWidget

BG = "#0f0f13"
ACCENT = "#7c5cbf"
TEXT = "#e8e8f0"

LEVEL_COLORS = {
    "beginner": "#f59e0b",
    "elementary": "#3b82f6",
    "intermediate": "#22c55e",
    "upper-intermediate": "#a855f7",
    "advanced": "#ef4444",
}


def _make_tray_icon() -> QPixmap:
    px = QPixmap(32, 32)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setBrush(QColor(ACCENT))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 28, 28)
    p.setPen(QColor("white"))
    p.setFont(QFont("Noto Serif", 14, QFont.Weight.Bold))
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "E")
    p.end()
    return px


class MainWindow(QMainWindow):
    def __init__(self, session_id: int, resume: bool = False):
        super().__init__()
        self._session_id = session_id
        self._messages: list[dict] = []
        self._corrections_count = 0
        self._words_learned: set[str] = set()
        self._current_level = "beginner"

        self._setup_window()
        self._setup_tray()
        self._setup_ui()

        if resume:
            self._load_history()
        else:
            self._chat.add_message(
                "Hello! I'm Alex, your English tutor. How are you today? "
                "Feel free to write in English — I'm here to help you practice!",
                "assistant",
            )

        self._refresh_stats()

    def _setup_window(self):
        self.setWindowTitle("English Tutor — Alex")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

    def _setup_tray(self):
        px = _make_tray_icon()
        tray = QSystemTrayIcon(QIcon(px), self)
        tray.setToolTip("English Tutor")
        menu = QMenu()
        menu.addAction("Show", self.show)
        menu.addAction("Quit", self.close)
        tray.setContextMenu(menu)
        tray.show()
        self._tray = tray

    def _setup_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background: {BG};")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top bar
        top_bar = self._build_top_bar()
        root_layout.addWidget(top_bar)

        # Main split
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setStyleSheet("QSplitter::handle { background: #2a2a3a; width: 1px; }")
        self._splitter.setHandleWidth(1)

        self._chat = ChatWidget()
        self._sidebar = SidebarWidget(self._session_id)

        self._splitter.addWidget(self._chat)
        self._splitter.addWidget(self._sidebar)
        self._splitter.setStretchFactor(0, 7)
        self._splitter.setStretchFactor(1, 3)

        root_layout.addWidget(self._splitter)

        self._chat.message_submitted.connect(self._on_user_message)

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet(f"background: #16161f; border-bottom: 1px solid #2a2a3a;")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("English Tutor — Alex")
        title.setFont(QFont("Noto Serif", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT};")

        layout.addWidget(title)
        layout.addStretch()

        self._level_badge = QLabel("beginner")
        self._level_badge.setFont(QFont("Noto Serif", 10, QFont.Weight.Bold))
        self._level_badge.setStyleSheet(
            f"background: {LEVEL_COLORS['beginner']}; color: white; "
            "border-radius: 10px; padding: 3px 10px;"
        )
        layout.addWidget(self._level_badge)

        return bar

    def _update_level_badge(self, level: str):
        self._current_level = level
        color = LEVEL_COLORS.get(level, ACCENT)
        self._level_badge.setText(level)
        self._level_badge.setStyleSheet(
            f"background: {color}; color: white; "
            "border-radius: 10px; padding: 3px 10px;"
        )

    def _on_user_message(self, text: str):
        from db.database import save_message
        from core.tutor import TutorWorker

        # Display in chat
        self._chat.add_message(text, "user")
        self._chat.set_input_enabled(False)
        self._chat.set_typing(True)

        # Persist
        save_message(self._session_id, "user", text)

        # Build history for API
        self._messages.append({"role": "user", "content": text})

        # Start worker
        self._worker = TutorWorker(list(self._messages), self)
        self._worker.response_ready.connect(self._on_response)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_response(self, data: dict):
        from db.database import (
            save_message, save_feedback, save_vocabulary,
            save_goals, update_stats, update_session_level,
        )

        self._chat.set_typing(False)
        self._chat.set_input_enabled(True)

        reply = data.get("reply", "")
        feedback = data.get("feedback", {})
        level = data.get("level", self._current_level)
        new_words = data.get("newWords", [])
        goals = data.get("goals", [])

        # Display reply
        self._chat.add_message(reply, "assistant")

        # Persist assistant message
        msg_id = save_message(self._session_id, "assistant", reply)

        # Persist feedback
        save_feedback(
            msg_id,
            feedback.get("positive", ""),
            feedback.get("correction"),
            feedback.get("tip", ""),
        )

        # Persist vocabulary
        save_vocabulary(new_words, self._session_id)
        for w in new_words:
            self._words_learned.add(w)

        # Persist goals
        if goals:
            save_goals(goals, self._session_id)
            self._sidebar.set_goals(goals)

        # Track corrections
        if feedback.get("correction"):
            self._corrections_count += 1

        # Update level
        self._update_level_badge(level)
        update_session_level(self._session_id, level)

        # Compute accuracy
        total_user = sum(1 for m in self._messages if m["role"] == "user")
        accuracy = max(0.0, 100.0 - (self._corrections_count / max(total_user, 1)) * 100)
        update_stats(self._session_id, accuracy, len(self._words_learned), self._corrections_count)

        # Update sidebar
        self._sidebar.update_feedback(
            feedback.get("positive", ""),
            feedback.get("correction"),
            feedback.get("tip", ""),
        )
        self._refresh_stats()

        # Append to history
        self._messages.append({"role": "assistant", "content": reply})

    def _on_error(self, error_msg: str):
        self._chat.set_typing(False)
        self._chat.set_input_enabled(True)
        self._chat.add_message(error_msg, "assistant")

    def _load_history(self):
        from db.database import get_messages, get_goals, get_stats, get_vocabulary

        rows = get_messages(self._session_id)
        for row in rows:
            self._chat.add_message(row["content"], row["role"])
            self._messages.append({"role": row["role"], "content": row["content"]})

        goals = get_goals(self._session_id)
        if goals:
            self._sidebar.set_goals(goals)

        stats = get_stats(self._session_id)
        if stats:
            self._corrections_count = stats["corrections_count"]

        words = get_vocabulary(self._session_id)
        self._words_learned = set(words)

    def _refresh_stats(self):
        from db.database import get_stats, get_cumulative_stats

        stats = get_stats(self._session_id)
        if stats:
            total_user = sum(1 for m in self._messages if m["role"] == "user")
            self._sidebar.update_session_stats(
                total_user,
                stats["corrections_count"],
                stats["words_learned"],
                stats["accuracy_pct"],
            )

        cum = get_cumulative_stats()
        self._sidebar.update_cumulative_stats(
            cum["total_sessions"],
            cum["total_words"],
            cum["total_corrections"],
            cum["avg_accuracy"],
        )

    def closeEvent(self, event):
        from db.database import update_stats
        total_user = sum(1 for m in self._messages if m["role"] == "user")
        accuracy = max(0.0, 100.0 - (self._corrections_count / max(total_user, 1)) * 100)
        update_stats(self._session_id, accuracy, len(self._words_learned), self._corrections_count)
        self._tray.hide()
        super().closeEvent(event)
