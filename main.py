import discord
import config


class Selena(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        modules = ["modules.media.spotify_module",
                   "modules.media.plex_module"]
        for module in modules:
            await self.load_extension(module)
        await self.tree.sync()

    async def load_extension(self, name):
        module = __import__(name, fromlist=["setup"])
        await module.setup(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


if __name__ == "__main__":
    intents = discord.Intents.default()
    client = Selena(intents=intents)
    client.run(config.DISCORD_TOKEN)
