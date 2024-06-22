import logging

import discord

import config

# Set up logging
logging.basicConfig(level=logging.DEBUG)


class Selena(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=config.DISCORD_GUILD_ID)
        await self.load_extensions()
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def load_extension(self, name):
        module = __import__(name, fromlist=["setup"])
        await module.setup(self)

    async def load_extensions(self):
        # Mandatory modules that cannot be disabled
        mandatory_modules = [
            "modules.admin.logger_module",
            "modules.admin.policy_module",
        ]

        # Load mandatory modules
        for extension in mandatory_modules:
            await self.load_extension(extension)

        # Load enabled modules from configuration
        for extension in config.ENABLED_MODULES:
            await self.load_extension(extension)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")


if __name__ == "__main__":
    # Enable message content intent
    intents = discord.Intents.default()
    intents.message_content = True

    client = Selena(intents=intents)
    client.run(config.DISCORD_TOKEN)
