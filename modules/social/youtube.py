import discord
from discord import app_commands
import requests
import logging
import asyncio
import sqlite3
from datetime import datetime
from config import config


class YouTube:
    def __init__(self, bot):
        self.bot = bot
        self.api_key = config['YOUTUBE_API_KEY']
        self.logger = logging.getLogger('YouTube')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)
        self.db_path = 'data/selena.db'

    async def fetch_latest_video(self, channel_id):
        url = f'https://www.googleapis.com/youtube/v3/search?key={self.api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=1'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['items']:
                return data['items'][0]
        return None

    async def check_channels(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id, last_video_id, alert_channel_id FROM youtube_channels")
        channels = cursor.fetchall()
        for channel_id, last_video_id, alert_channel_id in channels:
            latest_video = await self.fetch_latest_video(channel_id)
            if latest_video and latest_video['id']['videoId'] != last_video_id:
                await self.send_alert(alert_channel_id, latest_video)
                cursor.execute("UPDATE youtube_channels SET last_video_id = ? WHERE channel_id = ?", (latest_video['id']['videoId'], channel_id))
                conn.commit()
        conn.close()

    async def send_alert(self, alert_channel_id, video):
        channel = self.bot.get_channel(alert_channel_id)
        if channel:
            title = video['snippet']['title']
            description = video['snippet']['description']
            url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            thumbnail = video['snippet']['thumbnails']['high']['url']
            embed = discord.Embed(title=title, description=description, url=url, color=discord.Color.red())
            embed.set_thumbnail(url=thumbnail)
            await channel.send(embed=embed)

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="add_youtube_channel", description="Add a YouTube channel to monitor")
        async def add_youtube_channel_command(interaction: discord.Interaction, channel_id: str, alert_channel: discord.TextChannel):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO youtube_channels (channel_id, last_video_id, alert_channel_id) VALUES (?, ?, ?)", (channel_id, '', alert_channel.id))
            conn.commit()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Added YouTube channel {channel_id} to monitor.", color=discord.Color.green()))

        @tree.command(name="remove_youtube_channel", description="Remove a YouTube channel from monitoring")
        async def remove_youtube_channel_command(interaction: discord.Interaction, channel_id: str):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM youtube_channels WHERE channel_id = ?", (channel_id,))
            conn.commit()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Removed YouTube channel {channel_id} from monitoring.", color=discord.Color.green()))

        if not tree.get_command("add_youtube_channel"):
            tree.add_command(add_youtube_channel_command)

        if not tree.get_command("remove_youtube_channel"):
            tree.add_command(remove_youtube_channel_command)

    async def setup_hook(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.check_channels()
            await asyncio.sleep(3600)  # Check every hour


def setup(bot):
    youtube = YouTube(bot)
    youtube.setup(bot.tree)
    bot.loop.create_task(youtube.setup_hook())
