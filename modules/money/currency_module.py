# Flake8:noqa: E501
import logging
import random
from datetime import datetime, timedelta

import discord
from discord import app_commands

from modules.data.db import get_connection, initialize_db

logger = logging.getLogger(__name__)
initialize_db()


class CurrencyModule:
    COOLDOWN_PERIOD = timedelta(minutes=5)  # Set the cooldown period here

    def __init__(self, bot):
        self.bot = bot
        self.add_commands()

    def add_commands(self):
        @app_commands.command(name="earn_kibble", description="Earn Kibble")
        async def earn_kibble(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                conn = get_connection()
                cursor = conn.cursor()
                user_id = str(interaction.user.id)

                # Check cooldown
                cursor.execute(
                    "SELECT last_earned FROM currency WHERE user_id = ?", (user_id,)
                )
                result = cursor.fetchone()
                if result and result[0]:
                    last_earned = datetime.fromisoformat(result[0])
                    if datetime.now() - last_earned < CurrencyModule.COOLDOWN_PERIOD:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="Earn Kibble",
                                description="You are on cooldown. Please try again later.",
                                color=discord.Color.red(),
                            )
                        )
                        conn.close()
                        logger.info(
                            f"User {user_id} attempted to earn Kibble but is on cooldown."
                        )
                        return

                amount = random.choices([random.randint(1, 10), 100], [0.99, 0.01])[0]
                cursor.execute(
                    "INSERT OR IGNORE INTO currency (user_id, balance, last_earned) VALUES (?, ?, ?)",
                    (user_id, 0, datetime.now().isoformat()),
                )
                cursor.execute(
                    "UPDATE currency SET balance = balance + ?, last_earned = ? WHERE user_id = ?",
                    (amount, datetime.now().isoformat(), user_id),
                )
                conn.commit()
                cursor.execute(
                    "SELECT balance FROM currency WHERE user_id = ?", (user_id,)
                )
                new_balance = cursor.fetchone()[0]
                conn.close()
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Earn Kibble",
                        description=f"You have earned {amount} Kibble. Your new balance is {new_balance}.",
                        color=discord.Color.green(),
                    )
                )
                logger.info(
                    f"User {user_id} earned {amount} Kibble. New balance: {new_balance}"
                )
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in earn_kibble command: {e}")

        @app_commands.command(
            name="check_balance", description="Check your Kibble balance"
        )
        async def check_balance(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT balance FROM currency WHERE user_id = ?",
                    (str(interaction.user.id),),
                )
                result = cursor.fetchone()
                conn.close()
                if result:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="Check Balance",
                            description=f"Your current balance is {result[0]} Kibble.",
                            color=discord.Color.green(),
                        )
                    )
                    logger.info(
                        f"User {interaction.user.id} checked balance: {result[0]}"
                    )
                else:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="Check Balance",
                            description="You have no Kibble.",
                            color=discord.Color.red(),
                        )
                    )
                    logger.info(f"User {interaction.user.id} has no Kibble.")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in check_balance command: {e}")

        self.bot.tree.add_command(earn_kibble)
        self.bot.tree.add_command(check_balance)


async def setup(bot):
    CurrencyModule(bot)
