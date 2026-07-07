import sqlite3
from datetime import datetime

DB_PATH = "./chat_history.db"

def init_db():
    """Create tables if not exists."""
    conn = sqlite3.connect(DB_PATH)
    
    # Chats table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Messages table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            role TEXT,
            content TEXT,
            sources TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id)
        )
    """)
    
    conn.commit()
    conn.close()


def create_new_chat(title="New Chat"):
    """Create a new chat session."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO chats (title) VALUES (?)",
        (title,)
    )
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return chat_id


def save_message(chat_id, role, content, sources=""):
    """Save a message to a chat."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO messages (chat_id, role, content, sources) VALUES (?, ?, ?, ?)",
        (chat_id, role, content, sources)
    )
    conn.commit()
    conn.close()


def update_chat_title(chat_id, title):
    """Update chat title based on first question."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE chats SET title=? WHERE id=?",
        (title[:50], chat_id)
    )
    conn.commit()
    conn.close()


def load_all_chats():
    """Load all chat sessions."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT id, title, created_at FROM chats ORDER BY created_at DESC"
    )
    chats = cursor.fetchall()
    conn.close()
    return chats


def load_chat_messages(chat_id):
    """Load all messages for a chat."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT role, content, sources, timestamp FROM messages WHERE chat_id=? ORDER BY timestamp",
        (chat_id,)
    )
    messages = cursor.fetchall()
    conn.close()
    return messages


def delete_chat(chat_id):
    """Delete a chat and its messages."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()


def group_chats_by_date(chats):
    """Group chats by Today, Yesterday, Last Week."""
    from datetime import date, timedelta

    today = date.today()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)

    groups = {
        "Today": [],
        "Yesterday": [],
        "Last 7 Days": [],
        "Older": []
    }

    for chat in chats:
        chat_date = datetime.strptime(
            chat[2], "%Y-%m-%d %H:%M:%S"
        ).date()

        if chat_date == today:
            groups["Today"].append(chat)
        elif chat_date == yesterday:
            groups["Yesterday"].append(chat)
        elif chat_date >= last_week:
            groups["Last 7 Days"].append(chat)
        else:
            groups["Older"].append(chat)

    return groups