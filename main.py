import discord
from config import config
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = config['DISCORD_TOKEN']
GUILD_ID_1 = config['GUILD_ID_1']
GUILD_ID_2 = config['GUILD_ID_2']

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
        await self.tree.sync(guild=discord.Object(id=GUILD_ID_1))
        logging.info(f"Modules setup and commands synchronized to {GUILD_ID_1}")
        await self.tree.sync(guild=discord.Object(id=GUILD_ID_2))
        logging.info(f"Modules setup and commands synchronized to {GUILD_ID_2}")
        # Call setup_hook for xp_module here
        if self.xp_module:
            await self.xp_module.setup_hook()

    def load_modules(self):
        if config['modules']['music']['enabled']:
            from modules.music.music import Music
            music = Music(self)
            music.setup(self.tree)
            logging.info("Music module loaded")

        if config['modules']['terms_privacy']['enabled']:
            from modules.admin.terms_privacy import TermsPrivacy
            terms_privacy = TermsPrivacy(self)
            terms_privacy.setup(self.tree)
            logging.info("Terms and Privacy module loaded")

        if config['modules']['data_privacy']['enabled']:
            from modules.admin.data_privacy import DataPrivacy
            data_privacy = DataPrivacy(self)
            data_privacy.setup(self.tree)
            logging.info("Data Privacy module loaded")


bot = Selena()


@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)
