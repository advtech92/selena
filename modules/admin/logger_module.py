# modules/admin/logger_module.py
import logging
import logging.config

import discord
from discord import app_commands

from .logging_config import logging_config


class LoggerModule:
    def __init__(self, bot):
        self.bot = bot
        logging.config.dictConfig(logging_config)
        self.logger = logging.getLogger(__name__)
        self.add_logging_commands()

    def add_logging_commands(self):
        @self.bot.tree.command(name="log_test", description="Test the logging system")  # noqa: E501
        async def log_test(interaction: discord.Interaction):
            self.logger.debug("This is a debug message")
            self.logger.info("This is an info message")
            self.logger.warning("This is a warning message")
            self.logger.error("This is an error message")
            self.logger.critical("This is a critical message")
            await interaction.response.send_message(
                "Logging test completed. Check the logs!"
            )

        @self.bot.tree.command(
            name="set_log_level", description="Set the logging level (Owner/Admin only)"  # noqa: E501
        )
        @app_commands.choices(
            level=[
                app_commands.Choice(name="DEBUG", value="DEBUG"),
                app_commands.Choice(name="INFO", value="INFO"),
                app_commands.Choice(name="WARNING", value="WARNING"),
                app_commands.Choice(name="ERROR", value="ERROR"),
                app_commands.Choice(name="CRITICAL", value="CRITICAL"),
            ]
        )
        async def set_log_level(
            interaction: discord.Interaction, level: app_commands.Choice[str]
        ):
            guild = interaction.guild
            if guild is not None and (
                interaction.user.id == guild.owner_id
                or any(
                    role.permissions.administrator for role in interaction.user.roles  # noqa: E501
                )
            ):
                logging.getLogger().setLevel(level.value)
                await interaction.response.send_message(
                    f"Logging level set to {level.value}"
                )
            else:
                await interaction.response.send_message(
                    "You do not have permission to set the logging level.",
                    ephemeral=True,
                )


async def setup(bot):
    LoggerModule(bot)
