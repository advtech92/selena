import sqlite3


def initialize_db():
    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS birthdays (
            user_id TEXT PRIMARY KEY,
            birthday TEXT
        )
    ''')
    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect('birthdays.db')
