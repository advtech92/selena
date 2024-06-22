import logging
import random
from datetime import datetime, timedelta

import discord
from discord import app_commands

from modules.data.db import get_connection

logger = logging.getLogger(__name__)


class XPModule:
    def __init__(self, bot):
        self.bot = bot
        self.cooldown = {}  # Dictionary to store cooldowns
        self.add_commands()
        self.setup_event_listeners()

    async def on_message(self, message):
        logger.debug(f"Received message from {message.author.id}")
        if message.author.bot:
            logger.debug("Message is from a bot, ignoring")
            return

        user_id = message.author.id
        now = datetime.now()

        if user_id in self.cooldown and now < self.cooldown[user_id]:
            logger.debug(f"User {user_id} is on cooldown, ignoring")
            return  # User is on cooldown

        xp = random.randint(1, 5)  # Award between 1 and 5 XP for a message
        logger.debug(f"Awarding {xp} XP to user {user_id}")
        self.give_xp(user_id, xp)
        self.cooldown[user_id] = now + timedelta(seconds=10)  # 1 minute cooldown # noqa: E501

    def give_xp(self, user_id, xp):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT xp, level FROM user_xp WHERE user_id = ?", (user_id,))  # noqa: E501
        row = c.fetchone()

        if row:
            current_xp, current_level = row
            new_xp = current_xp + xp
            new_level = current_level

            # Level up logic
            while new_xp >= self.xp_for_next_level(new_level):
                new_xp -= self.xp_for_next_level(new_level)
                new_level += 1
                logger.info(f"User {user_id} leveled up to {new_level}")

            c.execute(
                "UPDATE user_xp SET xp = ?, level = ? WHERE user_id = ?",
                (new_xp, new_level, user_id),
            )
        else:
            c.execute(
                "INSERT INTO user_xp (user_id, xp, level) VALUES (?, ?, ?)",
                (user_id, xp, 1),
            )

        conn.commit()
        conn.close()
        logger.debug(f"Updated XP for user {user_id}")

    def xp_for_next_level(self, level):
        return int(
            100 * (1.5 ** (level - 1))
        )  # Exponential scaling for XP required to level up

    def add_commands(self):
        @app_commands.command(name="xp", description="Check your XP and level")
        async def check_xp(interaction: discord.Interaction):
            user_id = interaction.user.id
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT xp, level FROM user_xp WHERE user_id = ?", (user_id,))  # noqa: E501
            row = c.fetchone()
            conn.close()

            if row:
                xp, level = row
                await interaction.response.send_message(
                    f"You have {xp} XP and are level {level}."
                )
            else:
                await interaction.response.send_message("You have no XP yet.")

        self.bot.tree.add_command(check_xp)

    def setup_event_listeners(self):
        @self.bot.event
        async def on_message(message):
            await self.on_message(message)


async def setup(bot):
    XPModule(bot)
