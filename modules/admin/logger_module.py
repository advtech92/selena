# modules/admin/logger_module.py
import discord
import logging
import logging.config
from .logging_config import logging_config


class LoggerModule:
    def __init__(self, bot):
        self.bot = bot
        logging.config.dictConfig(logging_config)
        self.logger = logging.getLogger(__name__)

    def add_logging_commands(self):
        @self.bot.tree.command(name="log_test",
                               description="Test the logging system")
        async def log_test(interaction: discord.Interaction):
            self.logger.debug("This is a debug message")
            self.logger.info("This is an info message")
            self.logger.warning("This is a warning message")
            self.logger.error("This is an error message")
            self.logger.critical("This is a critical message")
            await interaction.response.send_message("Logging test completed."
                                                    "Check the logs!")


async def setup(bot):
    logger_module = LoggerModule(bot)
    logger_module.add_logging_commands()
