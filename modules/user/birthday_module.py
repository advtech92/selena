# Flake8:noqa: E501
import discord
from discord import app_commands
import sqlite3
import logging
from modules.data.db import initialize_db, get_connection

logger = logging.getLogger(__name__)
initialize_db()


class BirthdayModule:
    def __init__(self, bot):
        self.bot = bot
        self.add_commands()

    def add_commands(self):
        @app_commands.command(
            name="add_birthday", description="Add your birthday"
        )
        async def add_birthday(interaction: discord.Interaction, date: str):
            await interaction.response.defer()
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO birthdays (user_id, birthday) VALUES (?, ?)',
                               (str(interaction.user.id), date))
                conn.commit()
                conn.close()
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Add Birthday",
                        description=f"Your birthday {date} has been added.",
                        color=discord.Color.green()
                    )
                )
                logger.info(f"Birthday added for user {interaction.user.id}: {date}")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in add_birthday command: {e}")

        @app_commands.command(
            name="view_birthday", description="View your birthday"
        )
        async def view_birthday(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT birthday FROM birthdays WHERE user_id = ?', (str(interaction.user.id),))
                result = cursor.fetchone()
                conn.close()
                if result:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="View Birthday",
                            description=f"Your birthday is {result[0]}.",
                            color=discord.Color.green()
                        )
                    )
                    logger.info(f"Birthday viewed for user {interaction.user.id}: {result[0]}")
                else:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="View Birthday",
                            description="You have not set a birthday yet.",
                            color=discord.Color.red()
                        )
                    )
                    logger.info(f"Birthday not found for user {interaction.user.id}")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in view_birthday command: {e}")

        @app_commands.command(
            name="remove_birthday", description="Remove your birthday"
        )
        async def remove_birthday(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM birthdays WHERE user_id = ?', (str(interaction.user.id),))
                conn.commit()
                conn.close()
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Remove Birthday",
                        description="Your birthday has been removed.",
                        color=discord.Color.green()
                    )
                )
                logger.info(f"Birthday removed for user {interaction.user.id}")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in remove_birthday command: {e}")

        self.bot.tree.add_command(add_birthday)
        self.bot.tree.add_command(view_birthday)
        self.bot.tree.add_command(remove_birthday)


async def setup(bot):
    BirthdayModule(bot)
