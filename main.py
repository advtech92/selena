import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Import the Music module
from modules.music import Music

intents = discord.Intents.default()
intents.message_content = True  # Required for accessing message content


class Selena(discord.Client):
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

        # Initialize modules
        self.music = Music(self)

    async def setup_hook(self):
        # Sync the app commands with Discord
        await self.tree.sync()


client = Selena(intents=intents)

# Run the bot
client.run(TOKEN)
