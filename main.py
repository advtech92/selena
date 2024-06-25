import discord
from config import config

TOKEN = config['DISCORD_TOKEN']
GUILD_ID = config['GUILD_ID']
DISCORD_CHANNEL_ID = config['DISCORD_CHANNEL_ID']

intents = discord.Intents.default()
intents.messages = True
guild = discord.Object(id=GUILD_ID)


class Selena(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.load_modules()

    def load_modules(self):
        if config['modules']['currency']['enabled']:
            from modules.user.currency import Currency
            currency = Currency(self)
            currency.setup(self.tree)

        if config['modules']['xp']['enabled']:
            from modules.user.xp import XP
            xp = XP(self)
            xp.setup(self.tree)

        if config['modules']['twitch']['enabled']:
            from modules.social.twitch import Twitch
            twitch = Twitch(self)
            twitch.setup(self.tree)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


bot = Selena()


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)
