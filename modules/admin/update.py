import discord
from discord import app_commands
import os
import subprocess
import logging
import sys


class Update:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('Update')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)

    async def update_bot(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(description="Updating Selena...", color=discord.Color.green()))
        self.logger.info('Starting update process...')
        try:
            subprocess.run(["git", "pull"], check=True)
            self.logger.info('Successfully pulled updates from git.')
            await interaction.followup.send(embed=discord.Embed(description="Update complete. Restarting...", color=discord.Color.green()))
            os.execv(sys.executable, ['python'] + sys.argv)
        except subprocess.CalledProcessError as e:
            self.logger.error(f'Error during update: {e}')
            await interaction.followup.send(embed=discord.Embed(description=f"Update failed: {e}", color=discord.Color.red()))

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="update", description="Update the bot from the repository")
        async def update_command(interaction: discord.Interaction):
            await self.update_bot(interaction)

        if not tree.get_command("update"):
            tree.add_command(update_command)


def setup(bot):
    update = Update(bot)
    update.setup(bot.tree)
