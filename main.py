import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from db.database import init_db, create_session, get_last_session
from ui.main_window import MainWindow

APP_STYLE = """
QApplication, QWidget {
    background-color: #0f0f13;
    color: #e8e8f0;
}
QMessageBox {
    background-color: #16161f;
    color: #e8e8f0;
}
QMessageBox QLabel {
    color: #e8e8f0;
}
QMessageBox QPushButton {
    background: #7c5cbf;
    color: white;
    border-radius: 6px;
    padding: 6px 16px;
    min-width: 80px;
}
QMessageBox QPushButton:hover {
    background: #9070d0;
}
QDialog {
    background-color: #16161f;
    color: #e8e8f0;
}
QInputDialog QLabel {
    color: #e8e8f0;
}
QInputDialog QLineEdit {
    background: #1e1e2e;
    color: #e8e8f0;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    padding: 6px;
}
QInputDialog QPushButton {
    background: #7c5cbf;
    color: white;
    border-radius: 6px;
    padding: 6px 16px;
}
"""


def ask_resume(last_session) -> bool:
    """Ask user whether to resume the last session."""
    if last_session is None:
        return False

    mb = QMessageBox()
    mb.setWindowTitle("English Tutor — Alex")
    mb.setText("Continuă conversația anterioară?")
    mb.setInformativeText(
        f"Sesiunea precedentă a avut {last_session['total_messages']} mesaje "
        f"(nivel: {last_session['level']})."
    )
    mb.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    mb.setDefaultButton(QMessageBox.StandardButton.Yes)
    mb.setStyleSheet("""
        QMessageBox { background-color: #16161f; color: #e8e8f0; }
        QLabel { color: #e8e8f0; }
        QPushButton {
            background: #7c5cbf; color: white;
            border-radius: 6px; padding: 6px 16px; min-width: 80px;
        }
        QPushButton:hover { background: #9070d0; }
    """)
    result = mb.exec()
    return result == QMessageBox.StandardButton.Yes


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("English Tutor")
    app.setOrganizationName("EnglishTutor")
    app.setStyleSheet(APP_STYLE)

    # Prefer Noto Serif if available
    font = QFont("Noto Serif", 11)
    font.setStyleHint(QFont.StyleHint.Serif)
    app.setFont(font)

    # Initialize database
    init_db()

    last_session = get_last_session()
    resume = ask_resume(last_session)

    if resume and last_session:
        session_id = last_session["id"]
    else:
        session_id = create_session()

    window = MainWindow(session_id=session_id, resume=resume)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
