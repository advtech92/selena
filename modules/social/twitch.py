import discord
from discord import app_commands
import requests
import logging
import asyncio
import sqlite3
from config import config


class Twitch:
    def __init__(self, bot):
        self.bot = bot
        self.client_id = config['TWITCH_CLIENT_ID']
        self.client_secret = config['TWITCH_CLIENT_SECRET']
        self.logger = logging.getLogger('Twitch')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)
        self.db_path = 'data/selena.db'
        self.token = None
        self.token_expiry = None
        self.channel_alerts = {}
        self.ensure_table_exists()

    def ensure_table_exists(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS twitch_channels (
            channel_name TEXT PRIMARY KEY,
            alert_channel_id TEXT
        );
        """)
        conn.commit()
        conn.close()
        self.logger.info('Twitch channels table ensured in database')

    async def get_token(self):
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, params=params)
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.token_expiry = asyncio.get_event_loop().time() + data['expires_in']
            self.logger.info('Successfully obtained Twitch token')
        else:
            self.logger.error(f'Failed to obtain Twitch token: {response.status_code} - {response.text}')

    async def ensure_token(self):
        if not self.token or asyncio.get_event_loop().time() >= self.token_expiry:
            await self.get_token()

    async def fetch_channel_info(self, channel_name):
        await self.ensure_token()
        url = "https://api.twitch.tv/helix/streams"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Client-Id': self.client_id
        }
        params = {
            'user_login': channel_name
        }
        response = requests.get(url, headers=headers, params=params)
        self.logger.debug(f'Response status code: {response.status_code}')
        self.logger.debug(f'Response content: {response.content}')
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                return data['data'][0]  # Return the first stream (should only be one)
        return None

    async def fetch_user_info(self, user_id):
        await self.ensure_token()
        url = f"https://api.twitch.tv/helix/users?id={user_id}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Client-Id': self.client_id
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                return data['data'][0]
        return None

    async def check_channels(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT channel_name, alert_channel_id FROM twitch_channels")
        channels = cursor.fetchall()
        for channel_name, alert_channel_id in channels:
            channel_info = await self.fetch_channel_info(channel_name)
            if channel_info and not self.channel_alerts.get(channel_name):
                await self.send_alert(alert_channel_id, channel_info)
                self.channel_alerts[channel_name] = True
            elif not channel_info and self.channel_alerts.get(channel_name):
                self.channel_alerts[channel_name] = False
        conn.close()

    async def send_alert(self, alert_channel_id, channel_info):
        user_info = await self.fetch_user_info(channel_info['user_id'])
        channel = self.bot.get_channel(alert_channel_id)
        if channel:
            title = channel_info['title']
            url = f"https://www.twitch.tv/{channel_info['user_login']}"
            thumbnail = channel_info['thumbnail_url'].replace('{width}', '320').replace('{height}', '180')
            logo = user_info['profile_image_url'] if user_info else None
            embed = discord.Embed(title=title, url=url, color=discord.Color.purple())
            embed.set_thumbnail(url=logo if logo else thumbnail)
            embed.add_field(name="Channel", value=channel_info['user_name'], inline=True)
            embed.add_field(name="Game", value=channel_info['game_name'], inline=True)
            await channel.send(embed=embed)

    async def is_channel_followed(self, channel_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM twitch_channels WHERE channel_name = ?", (channel_name,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="add_twitch_channel", description="Add a Twitch channel to monitor")
        async def add_twitch_channel_command(interaction: discord.Interaction, channel_name: str, alert_channel: discord.TextChannel):
            if await self.is_channel_followed(channel_name):
                await interaction.response.send_message(embed=discord.Embed(description=f"Twitch channel {channel_name} is already being monitored.", color=discord.Color.orange()))
                return
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO twitch_channels (channel_name, alert_channel_id) VALUES (?, ?)", (channel_name, alert_channel.id))
            conn.commit()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Added Twitch channel {channel_name} to monitor.", color=discord.Color.green()))

        @tree.command(name="remove_twitch_channel", description="Remove a Twitch channel from monitoring")
        async def remove_twitch_channel_command(interaction: discord.Interaction, channel_name: str):
            if not await self.is_channel_followed(channel_name):
                await interaction.response.send_message(embed=discord.Embed(description=f"Twitch channel {channel_name} is not being monitored.", color=discord.Color.red()))
                return
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM twitch_channels WHERE channel_name = ?", (channel_name,))
            conn.commit()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Removed Twitch channel {channel_name} from monitoring.", color=discord.Color.green()))

        @tree.command(name="check_twitch_channel", description="Check if a Twitch channel is live")
        async def check_twitch_channel_command(interaction: discord.Interaction, channel_name: str):
            channel_info = await self.fetch_channel_info(channel_name)
            user_info = await self.fetch_user_info(channel_info['user_id']) if channel_info else None
            if channel_info:
                thumbnail = channel_info['thumbnail_url'].replace('{width}', '320').replace('{height}', '180')
                logo = user_info['profile_image_url'] if user_info else None
                embed = discord.Embed(title=f"{channel_info['user_name']} is live!", url=f"https://www.twitch.tv/{channel_info['user_login']}", color=discord.Color.purple())
                embed.set_thumbnail(url=logo if logo else thumbnail)
                embed.add_field(name="Title", value=channel_info['title'], inline=False)
                embed.add_field(name="Game", value=channel_info['game_name'], inline=False)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(embed=discord.Embed(description=f"{channel_name} is not live.", color=discord.Color.red()))

        if not tree.get_command("add_twitch_channel"):
            tree.add_command(add_twitch_channel_command)

        if not tree.get_command("remove_twitch_channel"):
            tree.add_command(remove_twitch_channel_command)

        if not tree.get_command("check_twitch_channel"):
            tree.add_command(check_twitch_channel_command)

    async def setup_hook(self):
        await self.bot.wait_until_ready()
        await self.get_token()
        while not self.bot.is_closed():
            await self.check_channels()
            await asyncio.sleep(300)  # Check every 5 minutes


def setup(bot):
    twitch = Twitch(bot)
    twitch.setup(bot.tree)
    bot.loop.create_task(twitch.setup_hook())
