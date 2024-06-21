import discord
import config


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
        extensions = [
            "modules.admin.logger_module",
            "modules.media.spotify_module",
            "modules.user.birthday_module",
            "modules.money.currency_module",
            # Add other modules here
        ]
        for extension in extensions:
            await self.load_extension(extension)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


if __name__ == "__main__":
    intents = discord.Intents.default()
    client = Selena(intents=intents)
    client.run(config.DISCORD_TOKEN)
