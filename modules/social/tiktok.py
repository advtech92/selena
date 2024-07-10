import discord
from discord import app_commands
import logging
import re


class TikTok:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('TikTok')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)

    async def on_message(self, message):
        if message.author.bot:
            return

        tiktok_url = self.extract_tiktok_url(message.content)
        if tiktok_url:
            embed = self.create_tiktok_embed(tiktok_url)
            await message.channel.send(embed=embed)
            await message.delete()
            await message.author.send("Your TikTok video has been properly embedded.")

    def extract_tiktok_url(self, content):
        tiktok_regex = re.compile(
            r'(https?://(?:www\.)?tiktok\.com/[^ ]+|https?://vm\.tiktok\.com/[^ ]+)')
        match = tiktok_regex.search(content)
        return match.group(0) if match else None

    def create_tiktok_embed(self, url):
        embed = discord.Embed(title="TikTok Video", description="Here is the TikTok video:", url=url)
        embed.set_author(name="TikTok", icon_url="https://upload.wikimedia.org/wikipedia/en/a/a9/TikTok_logo.svg")
        embed.add_field(name="Link", value=f"[Watch on TikTok]({url})")
        embed.set_footer(text="TikTok Embed Module")
        return embed

    def setup(self, tree: app_commands.CommandTree):
        pass


def setup(bot):
    tiktok = TikTok(bot)
    bot.add_listener(tiktok.on_message, "on_message")
    bot.tiktok_module = tiktok
