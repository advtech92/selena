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

        if config['modules']['destiny2']['enabled']:
            from modules.games.destiny2 import Destiny2
            destiny2 = Destiny2(self)
            destiny2.setup(self.tree)

        if config['modules']['music']['enabled']:
            from modules.music.music import Music
            music = Music(self)
            music.setup(self.tree)

        if config['modules']['youtube']['enabled']:
            from modules.social.youtube import YouTube
            youtube = YouTube(self)
            youtube.setup(self.tree)

        if config['modules']['twitch']['enabled']:
            from modules.social.twitch import Twitch
            twitch = Twitch(self)
            twitch.setup(self.tree)

        if config['modules']['update']['enabled']:
            from modules.admin.update import Update
            update = Update(self)
            update.setup(self.tree)

        if config['modules']['data_privacy']['enabled']:
            from modules.admin.data_privacy import DataPrivacy
            data_privacy = DataPrivacy(self)
            data_privacy.setup(self.tree)

        if config['modules']['terms_privacy']['enabled']:
            from modules.admin.terms_privacy import TermsPrivacy
            terms_privacy = TermsPrivacy(self)
            terms_privacy.setup(self.tree)


bot = Selena()


@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)
