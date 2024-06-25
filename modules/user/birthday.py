import discord
from discord import app_commands
from datetime import datetime
import sqlite3
import asyncio


class Birthday:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS birthdays (
                    user_id TEXT PRIMARY KEY,
                    birthday TEXT
                )
            ''')
            conn.commit()

    def _set_birthday(self, user_id, birthday):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO birthdays (user_id, birthday) VALUES (?, ?)', (user_id, birthday))
            conn.commit()

    def _get_birthday(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT birthday FROM birthdays WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def _remove_birthday(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM birthdays WHERE user_id = ?', (user_id,))
            conn.commit()

    async def set_birthday(self, interaction: discord.Interaction, date: str):
        user_id = str(interaction.user.id)
        try:
            datetime.strptime(date, "%Y-%m-%d")
            self._set_birthday(user_id, date)
            await interaction.response.send_message(f'{interaction.user.mention}, your birthday has been set to {date}.', ephemeral=True)
        except ValueError:
            await interaction.response.send_message(f'{interaction.user.mention}, the date format is incorrect. Please use YYYY-MM-DD.', ephemeral=True)

    async def get_birthday(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        birthday = self._get_birthday(user_id)
        if birthday:
            await interaction.response.send_message(f'{interaction.user.mention}, your birthday is set to {birthday}.', ephemeral=True)
        else:
            await interaction.response.send_message(f'{interaction.user.mention}, you have not set your birthday.', ephemeral=True)

    async def remove_birthday(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        self._remove_birthday(user_id)
        await interaction.response.send_message(f'{interaction.user.mention}, your birthday has been removed.', ephemeral=True)

    async def check_birthday(self):
        today = datetime.today().strftime("%Y-%m-%d")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM birthdays WHERE birthday = ?', (today,))
            users = cursor.fetchall()

        for user in users:
            user_id = user[0]
            user_obj = await self.bot.fetch_user(user_id)
            if user_obj:
                await user_obj.send(f'🎉🎂 Happy Birthday, {user_obj.mention}! 🎂🎉')

    def setup(self, tree):
        @app_commands.command(name='set_birthday', description='Set your birthday')
        @app_commands.describe(date='Your birthday in YYYY-MM-DD format')
        async def set_birthday_command(interaction: discord.Interaction, date: str):
            await self.set_birthday(interaction, date)

        @app_commands.command(name='get_birthday', description='Check your birthday')
        async def get_birthday_command(interaction: discord.Interaction):
            await self.get_birthday(interaction)

        @app_commands.command(name='remove_birthday', description='Remove your birthday')
        async def remove_birthday_command(interaction: discord.Interaction):
            await self.remove_birthday(interaction)

        tree.add_command(set_birthday_command)
        tree.add_command(get_birthday_command)
        tree.add_command(remove_birthday_command)

    async def setup_hook(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.check_birthday()
            await asyncio.sleep(86400)  # Check once every 24 hours


def setup(bot):
    birthday = Birthday(bot)
    bot.add_cog(birthday)
    bot.setup_hook = birthday.setup_hook
