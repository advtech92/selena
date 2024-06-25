import discord
from discord import app_commands
import sqlite3
import aiohttp
import asyncio
from config import config
from datetime import datetime, timedelta


class Twitch:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'
        self.client_id = config['TWITCH_CLIENT_ID']
        self.client_secret = config['TWITCH_CLIENT_SECRET']
        self._init_db()
        self.live_channels = set()
        self.token = None
        self.token_expiry = datetime.utcnow()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS twitch_channels (
                    channel_name TEXT PRIMARY KEY
                )
            ''')
            conn.commit()

    async def fetch_twitch_token(self):
        if self.token and datetime.utcnow() < self.token_expiry:
            return self.token
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://id.twitch.tv/oauth2/token', params={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }) as response:
                data = await response.json()
                self.token = data['access_token']
                self.token_expiry = datetime.utcnow() + timedelta(seconds=data['expires_in'])
                return self.token

    async def fetch_twitch_channel(self, channel_name):
        token = await self.fetch_titch_token()
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.twitch.tv/helix/users', headers={
                'Client-ID': self.client_id,
                'Authorization': f'Bearer {token}'
            }, params={'login': channel_name}) as response:
                data = await response.json()
                if data['data']:
                    return data['data'][0]
                return None

    async def fetch_stream_status(self, user_id):
        token = await self.fetch_twitch_token()
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.twitch.tv/helix/streams', headers={
                'Client-ID': self.client_id,
                'Authorization': f'Bearer {token}'
            }, params={'user_id': user_id}) as response:
                data = await response.json()
                if data['data']:
                    return data['data'][0]
                return None

    async def check_live_status(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT channel_name FROM twitch_channels')
            channels = cursor.fetchall()
        
        for (channel_name,) in channels:
            channel = await self.fetch_twitch_channel(channel_name)
            if channel:
                stream = await self.fetch_stream_status(channel['id'])
                if stream and channel_name not in self.live_channels:
                    self.live_channels.add(channel_name)
                    discord_channel = self.bot.get_channel(config['DISCORD_CHANNEL_ID'])
                    await discord_channel.send(f'{channel_name} is now live on Twitch!')
                elif not stream and channel_name in self.live_channels:
                    self.live_channels.remove(channel_name)

    @app_commands.command(name='add_twitch_channel', description='Follow a new Twitch channel')
    async def add_twitch_channel(self, interaction: discord.Interaction, channel_name: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO twitch_channels (channel_name) VALUES (?)', (channel_name,))
            conn.commit()
        await interaction.response.send_message(f'Added {channel_name} to the followed Twitch channels.')

    @app_commands.command(name='remove_twitch_channel', description='Unfollow a Twitch channel')
    async def remove_twitch_channel(self, interaction: discord.Interaction, channel_name: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM twitch_channels WHERE channel_name = ?', (channel_name,))
            conn.commit()
        await interaction.response.send_message(f'Removed {channel_name} from the followed Twitch channels.')

    @app_commands.command(name='check_twitch_channel', description='Check if a Twitch channel is live')
    async def check_twitch_channel(self, interaction: discord.Interaction, channel_name: str):
        channel = await self.fetch_twitch_channel(channel_name)
        if channel:
            stream = await self.fetch_stream_status(channel['id'])
            if stream:
                await interaction.response.send_message(f'{channel_name} is currently live on Twitch!')
            else:
                await interaction.response.send_message(f'{channel_name} is not live on Twitch.')
        else:
            await interaction.response.send_message(f'Could not find Twitch channel: {channel_name}')

    async def start_checking_live_status(self):
        while True:
            await self.check_live_status()
            await asyncio.sleep(60)

    def setup(self, tree):
        tree.add_command(self.add_twitch_channel)
        tree.add_command(self.remove_twitch_channel)
        tree.add_command(self.check_twitch_channel)


def setup(bot):
    bot.tree.add_cog(Twitch(bot))
