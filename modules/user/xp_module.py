import discord
from discord import app_commands
import logging
from modules.data.db import get_connection
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class XPModule:
    def __init__(self, bot):
        self.bot = bot
        self.cooldown = {}  # Dictionary to store cooldowns
        self.add_commands()

    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = message.author.id
        now = datetime.now()

        if user_id in self.cooldown:
            if now < self.cooldown[user_id]:
                return  # User is on cooldown

        self.give_xp(user_id, 10)  # Give 10 XP for a message
        self.cooldown[user_id] = now + timedelta(seconds=60)  # 1 minute cooldown

    def give_xp(self, user_id, xp):
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT xp, level FROM user_xp WHERE user_id = ?', (user_id,))
        row = c.fetchone()

        if row:
            current_xp, current_level = row
            new_xp = current_xp + xp
            new_level = current_level

            # Level up logic
            if new_xp >= self.xp_for_next_level(current_level):
                new_level += 1
                new_xp = new_xp - self.xp_for_next_level(current_level)
                logger.info(f"User {user_id} leveled up to {new_level}")

            c.execute('UPDATE user_xp SET xp = ?, level = ? WHERE user_id = ?', (new_xp, new_level, user_id))
        else:
            c.execute('INSERT INTO user_xp (user_id, xp, level) VALUES (?, ?, ?)', (user_id, xp, 1))

        conn.commit()
        conn.close()

    def xp_for_next_level(self, level):
        return 100 * level  # Example leveling curve

    def add_commands(self):
        @app_commands.command(name='xp', description='Check your XP and level')
        async def check_xp(interaction: discord.Interaction):
            user_id = interaction.user.id
            conn = get_connection()
            c = conn.cursor()
            c.execute('SELECT xp, level FROM user_xp WHERE user_id = ?', (user_id,))
            row = c.fetchone()
            conn.close()

            if row:
                xp, level = row
                await interaction.response.send_message(f"You have {xp} XP and are level {level}.")
            else:
                await interaction.response.send_message("You have no XP yet.")

        self.bot.tree.add_command(check_xp)


async def setup(bot):
    xp_module = XPModule(bot)

    @bot.event
    async def on_message(message):
        if not message.author.bot:  # Ensure the bot doesn't earn XP
            await xp_module.on_message(message)
        await bot.process_commands(message)  # Process commands after the XP check