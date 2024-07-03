import discord
from config import config
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = config['DISCORD_TOKEN']
GUILD_ID = config['GUILD_ID']

intents = discord.Intents.default()
intents.message_content = True


class Selena(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.xp_module = None  # Initialize as None
        self.load_modules()

    async def setup_hook(self):
        logging.info("Setting up modules...")
        self.tree.copy_global_to(guild=discord.Object(id=GUILD_ID))
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        logging.info("Modules setup and commands synchronized")
        # Call setup_hook for xp_module here
        if self.xp_module:
            await self.xp_module.setup_hook()

    def load_modules(self):
        if config['modules']['currency']['enabled']:
            from modules.user.currency import Currency
            currency = Currency(self)
            currency.setup(self.tree)
            logging.info("Currency module loaded")

        if config['modules']['xp']['enabled']:
            from modules.user.xp import XP
            xp = XP(self)
            xp.setup(self.tree)
            self.xp_module = xp  # Set the xp_module attribute
            logging.info("XP module loaded")

        if config['modules']['birthday']['enabled']:
            from modules.user.birthday import Birthday
            birthday = Birthday(self)
            birthday.setup(self.tree)
            logging.info("Birthday module loaded")

        if config['modules']['destiny2']['enabled']:
            from modules.games.destiny2 import Destiny2
            destiny2 = Destiny2(self)
            destiny2.setup(self.tree)
            logging.info("Destiny 2 module loaded")

        if config['modules']['music']['enabled']:
            from modules.music.music import Music
            music = Music(self)
            music.setup(self.tree)
            logging.info("Music module loaded")

        if config['modules']['youtube']['enabled']:
            from modules.social.youtube import YouTube
            youtube = YouTube(self)
            youtube.setup(self.tree)
            logging.info("YouTube module loaded")

        if config['modules']['twitch']['enabled']:
            from modules.social.twitch import Twitch
            twitch = Twitch(self)
            twitch.setup(self.tree)
            self.twitch_module = twitch
            logging.info("Twitch module loaded")

        if config['modules']['update']['enabled']:
            from modules.admin.update import Update
            update = Update(self)
            update.setup(self.tree)
            logging.info("Update module loaded")

        if config['modules']['data_privacy']['enabled']:
            from modules.admin.data_privacy import DataPrivacy
            data_privacy = DataPrivacy(self)
            data_privacy.setup(self.tree)
            logging.info("Data Privacy module loaded")

        if config['modules']['terms_privacy']['enabled']:
            from modules.admin.terms_privacy import TermsPrivacy
            terms_privacy = TermsPrivacy(self)
            terms_privacy.setup(self.tree)
            logging.info("Terms and Privacy module loaded")


bot = Selena()


@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_message(message):
    logging.debug(f"Message from {message.author}: {message.content}")
    if message.author == bot.user:
        return
    if bot.xp_module:
        await bot.xp_module.handle_message(message)

bot.run(TOKEN)
