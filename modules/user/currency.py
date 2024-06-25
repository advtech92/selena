import discord
from discord import app_commands
import random
import sqlite3
import os


class Currency:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    kibble INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def _get_user_kibble(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT kibble FROM users WHERE user_id = ?',
                           (user_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def _update_user_kibble(self, user_id, amount):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO users (user_id, kibble) VALUES (?, ?)',
                           (user_id, 0))
            cursor.execute('UPDATE users SET kibble = kibble + ? WHERE user_id = ?',
                           (amount, user_id))
            conn.commit()

    def setup(self, tree):
        @tree.command(name='earn_kibble', description='Earn Kibble')
        @app_commands.checks.cooldown(1, 30)
        async def earn_kibble(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            amount = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100],
                                    [0.01, 10, 10, 10, 10, 10, 10, 10, 10,
                                     10, 10, 0.01])[0]
            self._update_user_kibble(user_id, amount)
            await interaction.response.send_message
            (f'{interaction.user.mention} earned {amount} Kibble!')

        @tree.command(name='balance', description='Check your Kibble balance')
        async def balance(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            balance = self._get_user_kibble(user_id)
            await interaction.response.send_message
            (f'{interaction.user.mention} has {balance} Kibble.')


def setup(bot):
    bot.tree.add_cog(Currency(bot))
