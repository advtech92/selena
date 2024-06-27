import discord
from discord import app_commands
import requests
import logging
import asyncio
import sqlite3
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
        self.channel_alerts = {}

    async def fetch_channel_id(self, identifier):
        if identifier.startswith('@'):
            url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={identifier[1:]}&type=channel&key={self.api_key}'
        else:
            url = f'https://www.googleapis.com/youtube/v3/channels?part=id&id={identifier}&key={self.api_key}'
        self.logger.debug(f'Fetching channel ID with URL: {url}')
        response = requests.get(url)
        self.logger.debug(f'Channel ID response status code: {response.status_code}')
        self.logger.debug(f'Channel ID response content: {response.content}')
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                if identifier.startswith('@'):
                    for item in data['items']:
                        if item['snippet']['title'].lower() == identifier[1:].lower():
                            self.logger.debug(f'Found channel ID: {item["id"]["channelId"]} for {identifier}')
                            return item['id']['channelId']
                else:
                    return data['items'][0]['id']
        else:
            self.logger.error(f'Failed to fetch channel ID: {response.status_code} - {response.text}')
        return None

    async def fetch_latest_video(self, channel_id):
        url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&order=date&maxResults=1&type=video&key={self.api_key}'
        self.logger.debug(f'Fetching latest video with URL: {url}')
        response = requests.get(url)
        self.logger.debug(f'Latest video response status code: {response.status_code}')
        self.logger.debug(f'Latest video response content: {response.content}')
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                return data['items'][0]
        else:
            self.logger.error(f'Failed to fetch latest video: {response.status_code} - {response.text}')
        return None

    async def fetch_channel_info(self, channel_id):
        url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet&id={channel_id}&key={self.api_key}'
        self.logger.debug(f'Fetching channel info with URL: {url}')
        response = requests.get(url)
        self.logger.debug(f'Channel info response status code: {response.status_code}')
        self.logger.debug(f'Channel info response content: {response.content}')
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                return data['items'][0]
        else:
            self.logger.error(f'Failed to fetch channel info: {response.status_code} - {response.text}')
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
            await self.check_if_live(channel_id, alert_channel_id)
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

    async def check_if_live(self, channel_id, alert_channel_id):
        url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&type=video&eventType=live&key={self.api_key}'
        self.logger.debug(f'Checking live status with URL: {url}')
        response = requests.get(url)
        self.logger.debug(f'Live status response status code: {response.status_code}')
        self.logger.debug(f'Live status response content: {response.content}')
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                for live_video in data['items']:
                    if live_video['id']['kind'] == 'youtube#video':
                        await self.send_live_alert(alert_channel_id, live_video)
                        return True  # Indicate that the channel is live
        elif response.status_code == 400:
            # Handle the specific error case with additional logging
            self.logger.error(f'Error checking live status: {response.status_code} - {response.text}')
        return False  # Indicate that the channel is not live

    async def send_live_alert(self, alert_channel_id, live_video):
        channel = self.bot.get_channel(alert_channel_id)
        if channel:
            title = live_video['snippet']['title']
            description = live_video['snippet']['description']
            url = f"https://www.youtube.com/watch?v={live_video['id']['videoId']}"
            thumbnail = live_video['snippet']['thumbnails']['high']['url']
            embed = discord.Embed(title=title, description=description, url=url, color=discord.Color.red())
            embed.set_thumbnail(url=thumbnail)
            embed.add_field(name="Status", value="Live", inline=True)
            await channel.send(embed=embed)

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="add_youtube_channel", description="Add a YouTube channel to monitor")
        async def add_youtube_channel_command(interaction: discord.Interaction, identifier: str, alert_channel: discord.TextChannel):
            channel_id = await self.fetch_channel_id(identifier)
            if channel_id:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO youtube_channels (channel_id, last_video_id, alert_channel_id) VALUES (?, ?, ?)", (channel_id, '', alert_channel.id))
                conn.commit()
                conn.close()
                await interaction.response.send_message(embed=discord.Embed(description=f"Added YouTube channel {identifier} to monitor.", color=discord.Color.green()))
            else:
                await interaction.response.send_message(embed=discord.Embed(description=f"Failed to find YouTube channel {identifier}.", color=discord.Color.red()))

        @tree.command(name="remove_youtube_channel", description="Remove a YouTube channel from monitoring")
        async def remove_youtube_channel_command(interaction: discord.Interaction, channel_id: str):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM youtube_channels WHERE channel_id = ?", (channel_id,))
            conn.commit()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Removed YouTube channel {channel_id} from monitoring.", color=discord.Color.green()))

        @tree.command(name="check_youtube_channel", description="Check if a YouTube channel is live")
        async def check_youtube_channel_command(interaction: discord.Interaction, identifier: str):
            channel_id = await self.fetch_channel_id(identifier)
            if not channel_id:
                await interaction.response.send_message(embed=discord.Embed(description=f"Failed to find YouTube channel {identifier}.", color=discord.Color.red()))
                return
            is_live = await self.check_if_live(channel_id, interaction.channel_id)
            if is_live:
                await interaction.response.send_message(embed=discord.Embed(description=f"{identifier} is live!", color=discord.Color.green()))
            else:
                channel_info = await self.fetch_channel_info(channel_id)
                if channel_info:
                    embed = discord.Embed(description=f"{channel_info['snippet']['title']} is not live.", color=discord.Color.red())
                    embed.set_thumbnail(url=channel_info['snippet']['thumbnails']['high']['url'])
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message(embed=discord.Embed(description=f"{identifier} is not live.", color=discord.Color.red()))

        if not tree.get_command("add_youtube_channel"):
            tree.add_command(add_youtube_channel_command)

        if not tree.get_command("remove_youtube_channel"):
            tree.add_command(remove_youtube_channel_command)

        if not tree.get_command("check_youtube_channel"):
            tree.add_command(check_youtube_channel_command)

    async def setup_hook(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.check_channels()
            await asyncio.sleep(3600)  # Check every hour


def setup(bot):
    youtube = YouTube(bot)
    youtube.setup(bot.tree)
    bot.loop.create_task(youtube.setup_hook())
