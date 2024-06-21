import sqlite3


def initialize_db():
    conn = sqlite3.connect('currency.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS currency (
            user_id TEXT PRIMARY KEY,
            balance INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect('currency.db')
