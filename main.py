import discord
import config


class Selena(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        for extension in ["cogs.spotify_cog"]:
            await self.load_extension(extension)
        await self.tree.sync()

    async def on_ready(self):
        print("Logged in as {0.user}".format(self))


if __name__ == "__main__":
    intents = discord.Intents.default()
    client = Selena(intents=intents)
    client.run(config.DISCORD_TOKEN)
