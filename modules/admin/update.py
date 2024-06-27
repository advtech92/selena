# modules/admin/update.py
import discord
from discord import app_commands
import os
import subprocess
import logging


class Update:
    def __init__(self, bot, branch='dev-rework'):
        self.bot = bot
        self.branch = branch
        self.logger = logging.getLogger('Update')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)

    async def update_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(description="Updating Selena...", color=discord.Color.green()))

        self.logger.info(f"Pulling latest code from Git repository on branch {self.branch}...")
        subprocess.run(["git", "fetch"], check=True)
        subprocess.run(["git", "checkout", self.branch], check=True)
        subprocess.run(["git", "pull", "origin", self.branch], check=True)

        self.logger.info("Installing dependencies...")
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)

        await interaction.followup.send(embed=discord.Embed(description="Update completed. Restarting Selena...", color=discord.Color.green()))
        self.logger.info("Update completed. Restarting Selena...")

        os._exit(0)

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="update", description="Update Selena to the latest version")
        async def update_command(interaction: discord.Interaction):
            await interaction.response.defer()  # Defer the interaction response
            await self.update_bot(interaction)

        if not tree.get_command("update"):
            tree.add_command(update_command)


def setup(bot, branch='dev-rework'):
    updater = Update(bot, branch=branch)
    updater.setup(bot.tree)
