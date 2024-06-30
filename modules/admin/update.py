import discord
from discord import app_commands
import os
import logging
import subprocess
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
        try:
            await interaction.response.send_message(embed=discord.Embed(description="Updating Selena...", color=discord.Color.green()))
        except discord.errors.InteractionResponded:
            await interaction.followup.send(embed=discord.Embed(description="Updating Selena...", color=discord.Color.green()))

        # Fetch updates from the specified branch
        branch = 'main'  # change this to your branch if necessary
        result = subprocess.run(['git', 'pull', 'origin', branch], capture_output=True, text=True)

        if result.returncode == 0:
            self.logger.info("Successfully pulled updates from the repository")
            self.logger.info(result.stdout)
            try:
                await interaction.followup.send(embed=discord.Embed(description="Successfully updated Selena. Restarting...", color=discord.Color.green()))
            except discord.errors.InteractionResponded:
                await interaction.followup.send(embed=discord.Embed(description="Successfully updated Selena. Restarting...", color=discord.Color.green()))

            # Restart the bot (this is just a placeholder, modify according to your setup)
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            self.logger.error(f"Failed to pull updates: {result.stderr}")
            try:
                await interaction.followup.send(embed=discord.Embed(description="Failed to update Selena. Check logs for details.", color=discord.Color.red()))
            except discord.errors.InteractionResponded:
                await interaction.followup.send(embed=discord.Embed(description="Failed to update Selena. Check logs for details.", color=discord.Color.red()))

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="update", description="Update the bot to the latest version")
        async def update_command(interaction: discord.Interaction):
            await self.update_bot(interaction)

        if not tree.get_command("update"):
            tree.add_command(update_command)


def setup(bot):
    update = Update(bot)
    update.setup(bot.tree)
