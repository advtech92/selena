import discord
from discord import app_commands
import yt_dlp as youtube_dl
import logging
import asyncio


class Music:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('Music')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='music.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }

    async def search_youtube(self, query):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            try:
                requests = ydl.extract_info(f"ytsearch:{query}", download=False)
                return requests['entries'][0]
            except Exception as e:
                self.logger.error(f'Error searching YouTube: {e}')
                return None

    async def join(self, interaction: discord.Interaction):
        self.logger.debug(f'User {interaction.user} is attempting to join a voice channel')

        if interaction.guild.voice_client:
            await interaction.followup.send(embed=discord.Embed(description="Already connected to a voice channel.", color=discord.Color.red()))
            return

        if interaction.user.voice:
            channel = interaction.user.voice.channel
            try:
                voice_client = await channel.connect()
                await voice_client.guild.change_voice_state(channel=channel, self_deaf=True)
                await interaction.followup.send(embed=discord.Embed(description=f"Joined {channel.name}", color=discord.Color.green()))
                self.logger.info(f"Successfully connected to {channel.name}")
            except discord.ClientException as e:
                self.logger.error(f'Error joining voice channel: {e}')
                await interaction.followup.send(embed=discord.Embed(description=f"Error joining voice channel: {e}", color=discord.Color.red()))
            except asyncio.TimeoutError:
                self.logger.error('Timeout error while trying to connect to voice channel')
                await interaction.followup.send(embed=discord.Embed(description='Timeout error while trying to connect to voice channel', color=discord.Color.red()))
            except Exception as e:
                self.logger.error(f'Unexpected error: {e}')
                await interaction.followup.send(embed=discord.Embed(description=f'Unexpected error: {e}', color=discord.Color.red()))
        else:
            await interaction.followup.send(embed=discord.Embed(description="You're not in a voice channel.", color=discord.Color.red()))

    async def leave(self, interaction: discord.Interaction):
        self.logger.debug(f'User {interaction.user} is attempting to leave the voice channel')

        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.followup.send(embed=discord.Embed(description="Left the voice channel.", color=discord.Color.green()))
            self.logger.info(f"Disconnected from the voice channel in {interaction.guild.name}")
        else:
            await interaction.followup.send(embed=discord.Embed(description="I'm not in a voice channel.", color=discord.Color.red()))

    async def play(self, interaction: discord.Interaction, search: str):
        self.logger.debug(f'User {interaction.user} is attempting to play: {search}')

        if not interaction.guild.voice_client:
            await self.join(interaction)
            if not interaction.guild.voice_client:
                return

        info = await self.search_youtube(search)
        if info:
            url = info['url']
            title = info.get('title')
            self.logger.debug(f'Playing URL: {url}')
            try:
                source = await discord.FFmpegOpusAudio.from_probe(url)
                interaction.guild.voice_client.play(source)
                embed = discord.Embed(description=f'Now playing: **{title}**', color=discord.Color.green())
                await interaction.followup.send(embed=embed)
                self.logger.info(f'Now playing: {title}')
            except Exception as e:
                self.logger.error(f'Error playing audio: {e}')
                await interaction.followup.send(embed=discord.Embed(description='Error playing the audio.', color=discord.Color.red()))
        else:
            await interaction.followup.send(embed=discord.Embed(description='Could not find any results.', color=discord.Color.red()))
            self.logger.error('Could not find any results for the search query')

    async def pause(self, interaction: discord.Interaction):
        self.logger.debug(f'User {interaction.user} is attempting to pause the music')

        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.followup.send(embed=discord.Embed(description="Paused the current song.", color=discord.Color.green()))
            self.logger.info('Paused the current song')
        else:
            await interaction.followup.send(embed=discord.Embed(description="I'm not playing anything right now.", color=discord.Color.red()))

    async def resume(self, interaction: discord.Interaction):
        self.logger.debug(f'User {interaction.user} is attempting to resume the music')

        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.followup.send(embed=discord.Embed(description="Resumed the paused song.", color=discord.Color.green()))
            self.logger.info('Resumed the paused song')
        else:
            await interaction.followup.send(embed=discord.Embed(description="I'm not playing anything right now.", color=discord.Color.red()))

    async def stop(self, interaction: discord.Interaction):
        self.logger.debug(f'User {interaction.user} is attempting to stop the music')

        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.followup.send(embed=discord.Embed(description="Stopped the current song.", color=discord.Color.green()))
            self.logger.info('Stopped the current song')
        else:
            await interaction.followup.send(embed=discord.Embed(description="I'm not playing anything right now.", color=discord.Color.red()))

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="join", description="Join the voice channel")
        async def join_command(interaction: discord.Interaction):
            await interaction.response.defer()  # Defer the interaction response
            await self.join(interaction)

        @tree.command(name="leave", description="Leave the voice channel")
        async def leave_command(interaction: discord.Interaction):
            await interaction.response.defer()  # Defer the interaction response
            await self.leave(interaction)

        @tree.command(name="play", description="Play a song from YouTube")
        async def play_command(interaction: discord.Interaction, search: str):
            await interaction.response.defer()  # Defer the interaction response
            await self.play(interaction, search)

        @tree.command(name="pause", description="Pause the current song")
        async def pause_command(interaction: discord.Interaction):
            await interaction.response.defer()  # Defer the interaction response
            await self.pause(interaction)

        @tree.command(name="resume", description="Resume the paused song")
        async def resume_command(interaction: discord.Interaction):
            await interaction.response.defer()  # Defer the interaction response
            await self.resume(interaction)

        @tree.command(name="stop", description="Stop the current song")
        async def stop_command(interaction: discord.Interaction):
            await interaction.response.defer()  # Defer the interaction response
            await self.stop(interaction)


def setup(bot):
    music = Music(bot)
    music.setup(bot.tree)
