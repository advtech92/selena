import discord
from config import config
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = config['DISCORD_TOKEN']
GUILD_ID = config['GUILD_ID']

intents = discord.Intents.default()
intents.messages = True


class Selena(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.twitch = None
        self.load_modules()

    async def setup_hook(self):
        logging.info("Setting up modules...")
        if self.twitch:
            logging.info("Setting up Twitch module asynchronously...")
            await self.twitch.setup_hook()
        self.tree.copy_global_to(guild=discord.Object(id=GUILD_ID))
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))

    def load_modules(self):
        if config['modules']['currency']['enabled']:
            from modules.user.currency import Currency
            currency = Currency(self)
            currency.setup(self.tree)

        if config['modules']['xp']['enabled']:
            from modules.user.xp import XP
            xp = XP(self)
            xp.setup(self.tree)

        if config['modules']['birthday']['enabled']:
            from modules.user.birthday import Birthday
            birthday = Birthday(self)
            birthday.setup(self.tree)


bot = Selena()


@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)
