import discord
from config import config

TOKEN = config['DISCORD_TOKEN']
GUILD_ID = config['GUILD_ID']

intents = discord.Intents.default()
intents.messages = True


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

    async def setup_hook(self):
        self.tree.copy_global_to(guild=discord.Object(id=GUILD_ID))
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))


bot = Selena()


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)
