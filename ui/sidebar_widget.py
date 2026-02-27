from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QScrollArea, QFrame, QProgressBar, QListWidget, QListWidgetItem,
    QPushButton, QInputDialog, QLineEdit,
)

BG = "#0f0f13"
SIDEBAR_BG = "#13131c"
ACCENT = "#7c5cbf"
TEXT = "#e8e8f0"
GREEN = "#3dba6f"
ORANGE = "#e08040"
BLUE = "#4a9edd"
MUTED = "#888"

TAB_STYLE = f"""
QTabWidget::pane {{
    border: none;
    background: {SIDEBAR_BG};
}}
QTabBar::tab {{
    background: #1a1a2a;
    color: {MUTED};
    padding: 8px 14px;
    border: none;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background: {SIDEBAR_BG};
    color: {TEXT};
    border-bottom: 2px solid {ACCENT};
}}
"""


def _section(title: str, color: str, body: str) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(f"background: #1a1a2a; border-radius: 8px; border-left: 3px solid {color};")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(4)

    title_lbl = QLabel(title)
    title_lbl.setFont(QFont("Noto Serif", 9, QFont.Weight.Bold))
    title_lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")

    body_lbl = QLabel(body or "—")
    body_lbl.setWordWrap(True)
    body_lbl.setFont(QFont("Noto Serif", 10))
    body_lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
    body_lbl.setObjectName("body")

    layout.addWidget(title_lbl)
    layout.addWidget(body_lbl)
    return frame


class FeedbackTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {SIDEBAR_BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self._positive_frame = _section("✅ Bine făcut", GREEN, "")
        self._correction_frame = _section("✏️ Corecție", ORANGE, "")
        self._tip_frame = _section("💡 Sfat", BLUE, "")

        layout.addWidget(self._positive_frame)
        layout.addWidget(self._correction_frame)
        layout.addWidget(self._tip_frame)
        layout.addStretch()

    def _get_body(self, frame: QFrame) -> QLabel:
        for i in range(frame.layout().count()):
            w = frame.layout().itemAt(i).widget()
            if isinstance(w, QLabel) and w.objectName() == "body":
                return w

    def update_feedback(self, positive: str, correction: str | None, tip: str):
        self._get_body(self._positive_frame).setText(positive or "—")
        self._get_body(self._correction_frame).setText(correction or "—")
        self._get_body(self._tip_frame).setText(tip or "—")

    def reset(self):
        self._get_body(self._positive_frame).setText("—")
        self._get_body(self._correction_frame).setText("—")
        self._get_body(self._tip_frame).setText("—")


class GoalsTab(QWidget):
    goals_changed = pyqtSignal()

    def __init__(self, session_id: int, parent=None):
        super().__init__(parent)
        self._session_id = session_id
        self.setStyleSheet(f"background: {SIDEBAR_BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        lbl = QLabel("Obiective de învățare")
        lbl.setFont(QFont("Noto Serif", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {TEXT};")
        layout.addWidget(lbl)

        self._list = QListWidget()
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: #1a1a2a;
                color: {TEXT};
                border-radius: 8px;
                border: none;
                font-size: 12px;
            }}
            QListWidget::item {{ padding: 6px 8px; }}
            QListWidget::item:selected {{ background: {ACCENT}; }}
        """)
        self._list.setFont(QFont("Noto Serif", 10))
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Adaugă")
        del_btn = QPushButton("🗑 Șterge")
        for btn in (add_btn, del_btn):
            btn.setFont(QFont("Noto Serif", 10))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #2a2a3a;
                    color: {TEXT};
                    border-radius: 6px;
                    padding: 6px 12px;
                    border: none;
                }}
                QPushButton:hover {{ background: {ACCENT}; }}
            """)
        add_btn.clicked.connect(self._add_goal)
        del_btn.clicked.connect(self._delete_goal)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

    def set_goals(self, goals: list[str]):
        self._list.clear()
        for g in goals:
            item = QListWidgetItem(f"• {g}")
            item.setData(Qt.ItemDataRole.UserRole, g)
            self._list.addItem(item)

    def get_goals(self) -> list[str]:
        return [
            self._list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self._list.count())
        ]

    def _add_goal(self):
        from db.database import add_goal
        text, ok = QInputDialog.getText(self, "Obiectiv nou", "Obiectiv:", QLineEdit.EchoMode.Normal)
        if ok and text.strip():
            add_goal(text.strip(), self._session_id)
            item = QListWidgetItem(f"• {text.strip()}")
            item.setData(Qt.ItemDataRole.UserRole, text.strip())
            self._list.addItem(item)
            self.goals_changed.emit()

    def _delete_goal(self):
        from db.database import delete_goal
        current = self._list.currentItem()
        if current:
            goal_text = current.data(Qt.ItemDataRole.UserRole)
            delete_goal(goal_text, self._session_id)
            self._list.takeItem(self._list.row(current))
            self.goals_changed.emit()


class ProgressTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {SIDEBAR_BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Grammar accuracy
        layout.addWidget(self._make_label("Acuratețe gramatică"))
        self._grammar_bar = self._make_bar(GREEN)
        layout.addWidget(self._grammar_bar)

        # Vocabulary
        layout.addWidget(self._make_label("Vocabular acumulat"))
        self._vocab_bar = self._make_bar(BLUE)
        layout.addWidget(self._vocab_bar)

        layout.addWidget(self._make_separator())

        # Session stats
        sess_lbl = QLabel("Sesiunea curentă")
        sess_lbl.setFont(QFont("Noto Serif", 10, QFont.Weight.Bold))
        sess_lbl.setStyleSheet(f"color: {ACCENT};")
        layout.addWidget(sess_lbl)

        self._sess_messages = self._make_stat("Mesaje: 0")
        self._sess_corrections = self._make_stat("Corecții: 0")
        self._sess_words = self._make_stat("Cuvinte noi: 0")
        layout.addWidget(self._sess_messages)
        layout.addWidget(self._sess_corrections)
        layout.addWidget(self._sess_words)

        layout.addWidget(self._make_separator())

        # Cumulative stats
        cum_lbl = QLabel("Total cumulat")
        cum_lbl.setFont(QFont("Noto Serif", 10, QFont.Weight.Bold))
        cum_lbl.setStyleSheet(f"color: {ACCENT};")
        layout.addWidget(cum_lbl)

        self._cum_sessions = self._make_stat("Sesiuni: 0")
        self._cum_words = self._make_stat("Cuvinte totale: 0")
        self._cum_corrections = self._make_stat("Corecții totale: 0")
        self._cum_accuracy = self._make_stat("Acuratețe medie: 0.0%")
        layout.addWidget(self._cum_sessions)
        layout.addWidget(self._cum_words)
        layout.addWidget(self._cum_corrections)
        layout.addWidget(self._cum_accuracy)

        layout.addStretch()

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Noto Serif", 10))
        lbl.setStyleSheet(f"color: {TEXT};")
        return lbl

    def _make_stat(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Noto Serif", 10))
        lbl.setStyleSheet(f"color: {MUTED};")
        return lbl

    def _make_bar(self, color: str) -> QProgressBar:
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setFixedHeight(12)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: #1a1a2a;
                border-radius: 6px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 6px;
            }}
        """)
        return bar

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: #2a2a3a; border: none; max-height: 1px;")
        return line

    def update_session_stats(self, messages: int, corrections: int, words: int, accuracy: float):
        self._sess_messages.setText(f"Mesaje: {messages}")
        self._sess_corrections.setText(f"Corecții: {corrections}")
        self._sess_words.setText(f"Cuvinte noi: {words}")
        self._grammar_bar.setValue(int(accuracy))
        self._vocab_bar.setValue(min(100, int(words / 50 * 100)))

    def update_cumulative_stats(self, sessions: int, total_words: int, total_corrections: int, avg_accuracy: float):
        self._cum_sessions.setText(f"Sesiuni: {sessions}")
        self._cum_words.setText(f"Cuvinte totale: {total_words}")
        self._cum_corrections.setText(f"Corecții totale: {total_corrections}")
        self._cum_accuracy.setText(f"Acuratețe medie: {avg_accuracy:.1f}%")


class SidebarWidget(QWidget):
    def __init__(self, session_id: int, parent=None):
        super().__init__(parent)
        self._session_id = session_id
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"background: {SIDEBAR_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(TAB_STYLE)

        self._feedback_tab = FeedbackTab()
        self._goals_tab = GoalsTab(self._session_id)
        self._progress_tab = ProgressTab()

        self._tabs.addTab(self._feedback_tab, "Feedback")
        self._tabs.addTab(self._goals_tab, "Obiective")
        self._tabs.addTab(self._progress_tab, "Progres")

        layout.addWidget(self._tabs)

    def update_feedback(self, positive: str, correction: str | None, tip: str):
        self._feedback_tab.update_feedback(positive, correction, tip)
        self._tabs.setCurrentIndex(0)

    def set_goals(self, goals: list[str]):
        self._goals_tab.set_goals(goals)

    def update_session_stats(self, messages: int, corrections: int, words: int, accuracy: float):
        self._progress_tab.update_session_stats(messages, corrections, words, accuracy)

    def update_cumulative_stats(self, sessions: int, total_words: int, total_corrections: int, avg_accuracy: float):
        self._progress_tab.update_cumulative_stats(sessions, total_words, total_corrections, avg_accuracy)
