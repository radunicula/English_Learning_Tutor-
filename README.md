# English Learning Tutor — Alex

A desktop English learning tutor application for Fedora Linux 43, built with Python and PyQt6. It helps Romanian speakers learn and practice English through AI-powered conversations with a friendly tutor named **Alex**, powered by Anthropic Claude.

---

## Features

- 💬 **AI-powered chat** — Converse with Alex in English; he always replies in English and gently redirects you if you write in Romanian.
- ✏️ **Real-time grammar feedback** — Every message is analysed for grammar, vocabulary and syntax errors.
- 📈 **Level detection** — Your proficiency level (beginner → advanced) is tracked and updated automatically.
- 📚 **Vocabulary tracking** — New words introduced during each session are saved and counted.
- 🎯 **Learning goals** — View, add and delete personalised learning objectives in the sidebar.
- 📊 **Progress statistics** — Per-session and cumulative stats: messages sent, corrections, words learned and grammar accuracy.
- 🔄 **Session persistence** — Resume your last conversation or start a fresh one at launch.
- 🌙 **Dark theme UI** — Elegant dark interface built with PyQt6.

---

## Requirements

- **OS**: Fedora Linux 43 (or any modern Linux desktop)
- **Python**: 3.11 or newer
- **Anthropic API key**: [Get one at console.anthropic.com](https://console.anthropic.com/)

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/radunicula/English_Learning_Tutor-.git
   cd English_Learning_Tutor-
   ```

2. **Create and activate a virtual environment** (recommended)

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key**

   Copy the example environment file and add your Anthropic API key:

   ```bash
   cp .env.example .env
   ```

   Open `.env` in a text editor and replace the placeholder with your real key:

   ```
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   ```

---

## Usage

```bash
python main.py
```

When the app launches, you will be asked whether to **resume** the last session or start a new one.

### Chat interface

- Type your message in English in the input box.
- Press **Enter** to send, or **Shift+Enter** for a new line.
- Alex's response appears on the left; your messages appear on the right.

### Sidebar tabs

| Tab | Description |
|-----|-------------|
| **Feedback** | Shows what you did well (✅), any correction (✏️) and a grammar/vocabulary tip (💡) after each message. |
| **Obiective** (Goals) | Lists your current learning objectives. Use **+ Adaugă** to add a goal and **🗑 Șterge** to remove the selected one. |
| **Progres** (Progress) | Displays grammar accuracy, vocabulary progress bars and session/cumulative statistics. |

---

## Project Structure

```
English_Learning_Tutor-/
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── core/
│   └── tutor.py          # Anthropic API integration & background worker
├── db/
│   └── database.py       # SQLite database (sessions, messages, feedback, vocabulary, goals, stats)
└── ui/
    ├── main_window.py    # Main application window
    ├── chat_widget.py    # Chat message bubbles and input area
    └── sidebar_widget.py # Feedback, Goals and Progress sidebar tabs
```

---

## Technology Stack

| Component | Library / Tool |
|-----------|----------------|
| GUI framework | [PyQt6](https://pypi.org/project/PyQt6/) ≥ 6.6 |
| AI backend | [Anthropic Claude](https://pypi.org/project/anthropic/) (claude-3-5-sonnet) ≥ 0.25 |
| Environment config | [python-dotenv](https://pypi.org/project/python-dotenv/) ≥ 1.0 |
| Database | SQLite (via Python standard library) |

---

## Database

The application stores all data in a local SQLite database at:

```
~/.local/share/english-tutor/tutor.db
```

Tables: `sessions`, `messages`, `feedback`, `vocabulary`, `goals`, `stats`.

---

## License

This project is provided as-is for educational purposes.
