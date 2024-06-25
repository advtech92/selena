import discord
from discord import app_commands
from datetime import datetime, timedelta
import sqlite3


class XP:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'
        self._init_db()
        self.cooldowns = {}

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    kibble INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1
                )
            ''')
            conn.commit()

    def _get_user_xp(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT xp, level FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row if row else (0, 1)

    def _update_user_xp(self, user_id, xp):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO users (user_id, xp, level) VALUES (?, ?, ?)', (user_id, 0, 1))
            cursor.execute('UPDATE users SET xp = xp + ? WHERE user_id = ?', (xp, user_id))
            conn.commit()

    def _update_user_level(self, user_id, level):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET level = ? WHERE user_id = ?', (level, user_id))
            conn.commit()

    def xp_needed_for_next_level(self, level):
        return 5 * (level ** 2) + 50 * level + 100

    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        now = datetime.now()

        if user_id in self.cooldowns:
            if now < self.cooldowns[user_id]:
                return

        self.cooldowns[user_id] = now + timedelta(seconds=10)

        xp, level = self._get_user_xp(user_id)
        self._update_user_xp(user_id, 10)
        xp += 10

        if xp >= self.xp_needed_for_next_level(level):
            level += 1
            self._update_user_level(user_id, level)
            await message.channel.send(f'{message.author.mention} has leveled up to level {level}!')

    @app_commands.command(name='earn_xp', description='Manually earn XP (for testing)')
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def earn_xp(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        xp, level = self._get_user_xp(user_id)
        self._update_user_xp(user_id, 10)
        xp += 10

        if xp >= self.xp_needed_for_next_level(level):
            level += 1
            self._update_user_level(user_id, level)
            await interaction.response.send_message(f'{interaction.user.mention} has leveled up to level {level}!')
        else:
            await interaction.response.send_message(f'{interaction.user.mention} earned 10 XP!')

    @earn_xp.error
    async def earn_xp_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f'{interaction.user.mention}, you are on cooldown. Try again in {error.retry_after:.2f} seconds.', ephemeral=True)

    @app_commands.command(name='check_progress', description='Check your XP progress towards the next level')
    async def check_progress(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        xp, level = self._get_user_xp(user_id)
        xp_needed = self.xp_needed_for_next_level(level)
        xp_to_next_level = xp_needed - xp

        await interaction.response.send_message(f'{interaction.user.mention}, you need {xp_to_next_level} more XP to reach the next level.')

    def setup(self, tree):
        tree.add_command(self.earn_xp)
        tree.add_command(self.check_progress)


def setup(bot):
    bot.tree.add_cog(XP(bot))
