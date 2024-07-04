import discord
from discord.ext import tasks
import sqlite3
import logging
import datetime

class Birthday:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'
        self.logger = logging.getLogger('Birthday')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)

        self.ensure_table_exists()

    def ensure_table_exists(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS birthdays (
            user_id TEXT,
            guild_id TEXT,
            birthday TEXT,
            PRIMARY KEY (user_id, guild_id)
        );
        """)
        conn.commit()
        conn.close()
        self.logger.info('Birthday table ensured in database')

    async def set_birthday(self, user_id, guild_id, birthday):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO birthdays (user_id, guild_id, birthday)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, guild_id)
            DO UPDATE SET birthday = ?
        """, (user_id, guild_id, birthday, birthday))
        conn.commit()
        conn.close()
        self.logger.info(f'Set birthday for user {user_id} in guild {guild_id}')

    async def get_birthday(self, user_id, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT birthday FROM birthdays WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    @tasks.loop(hours=24)
    async def check_birthdays(self):
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, guild_id FROM birthdays WHERE birthday = ?", (today,))
        rows = cursor.fetchall()
        conn.close()
        for user_id, guild_id in rows:
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                user = guild.get_member(int(user_id))
                if user:
                    channel = guild.system_channel or next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
                    if channel:
                        await channel.send(f"Happy Birthday, {user.mention}! 🎉🎂")

    async def setup_hook(self):
        self.check_birthdays.start()
        self.logger.info('Started birthday check loop')

    def setup(self, tree: discord.app_commands.CommandTree):
        @tree.command(name="set_birthday", description="Set your birthday")
        async def set_birthday_command(interaction: discord.Interaction):
            await interaction.response.send_modal(BirthdayModal(self))

        @tree.command(name="check_birthday", description="Check your birthday")
        async def check_birthday_command(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            birthday = await self.get_birthday(user_id, guild_id)
            if birthday:
                await interaction.response.send_message(f"Your birthday is set to {birthday}.", ephemeral=True)
            else:
                await interaction.response.send_message("You have not set your birthday yet. Use /set_birthday to set it.", ephemeral=True)

        if not tree.get_command("set_birthday"):
            tree.add_command(set_birthday_command)

        if not tree.get_command("check_birthday"):
            tree.add_command(check_birthday_command)


class BirthdayModal(discord.ui.Modal, title="Set Birthday"):
    birthday = discord.ui.TextInput(label="Your Birthday", placeholder="Enter your birthday (YYYY-MM-DD)...", required=True)

    def __init__(self, birthday_module):
        super().__init__()
        self.birthday_module = birthday_module

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        try:
            birthday = self.birthday.value
            await self.birthday_module.set_birthday(user_id, guild_id, birthday)
            await interaction.response.send_message("Your birthday has been set.", ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)


def setup(bot):
    birthday_module = Birthday(bot)
    bot.add_cog(birthday_module)
    bot.birthday_module = birthday_module
