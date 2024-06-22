import sqlite3


def initialize_db():
    conn = sqlite3.connect('selena.db')
    cursor = conn.cursor()

    # Birthdays table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS birthdays (
            user_id TEXT PRIMARY KEY,
            birthday TEXT
        )
    ''')

    # Currency table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS currency (
            user_id TEXT PRIMARY KEY,
            balance INTEGER,
            last_earned TIMESTAMP
        )
    ''')

    # Followed channels table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS followed_channels (
            twitch_name TEXT PRIMARY KEY,
            discord_channel_id INTEGER
        )
    ''')

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect('selena.db')
