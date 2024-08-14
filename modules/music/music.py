import discord
from discord.ext import commands
from discord import app_commands
from yt_dlp import YoutubeDL
import os
from dotenv import load_dotenv

load_dotenv()

YTDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': 'True',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = YoutubeDL(YTDL_OPTIONS)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.is_playing = False
        self.volume = 0.3
        self.loop = False  # Initialize loop state
        self.current_song = None  # Track the current song

    async def join(self, interaction: discord.Interaction):
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await channel.connect(self_deaf=True)  # Join the channel deafened
            await interaction.followup.send("Joined the voice channel.")
        else:
            await interaction.followup.send("Already in a voice channel.")

    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.followup.send("Left the voice channel.")
        else:
            await interaction.followup.send("Not connected to a voice channel.")

    async def play(self, interaction: discord.Interaction, search: str):
        if not interaction.guild.voice_client:
            await self.join(interaction)

        info = ytdl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
        url = info['url']

        if interaction.guild.voice_client.is_playing():
            self.queue.append((url, info['title']))
            await interaction.followup.send(f'Queued: {info["title"]}')
        else:
            self.current_song = (url, info['title'])
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), volume=self.volume)
            interaction.guild.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction)))
            self.is_playing = True
            await interaction.followup.send(f'Playing: {info["title"]}')

    async def play_next(self, interaction: discord.Interaction):
        if self.loop and self.current_song:  # If loop is active, repeat the current song
            url, title = self.current_song
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), volume=self.volume)
            interaction.guild.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction)))
            await interaction.followup.send(f'Repeating: {title}')
        elif self.queue:
            url, title = self.queue.pop(0)
            self.current_song = (url, title)
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), volume=self.volume)
            interaction.guild.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction)))
            await interaction.followup.send(f'Playing next: {title}')
        else:
            self.is_playing = False

    async def pause(self, interaction: discord.Interaction):
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.followup.send("Paused the song.")
        else:
            await interaction.followup.send("No song is currently playing.")

    async def resume(self, interaction: discord.Interaction):
        if interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.followup.send("Resumed the song.")
        else:
            await interaction.followup.send("The song is not paused.")

    async def stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            self.queue = []
            self.current_song = None
            await interaction.followup.send("Stopped the song.")
        else:
            await interaction.followup.send("No song is currently playing.")

    async def set_volume(self, interaction: discord.Interaction, volume: float):
        self.volume = volume
        if interaction.guild.voice_client and interaction.guild.voice_client.source:
            interaction.guild.voice_client.source.volume = self.volume
            await interaction.followup.send(f"Volume set to {volume * 100}%.")
        else:
            await interaction.followup.send("No audio source found.")

    async def toggle_loop(self, interaction: discord.Interaction):
        self.loop = not self.loop  # Toggle the loop state
        state = "enabled" if self.loop else "disabled"
        await interaction.followup.send(f"Loop has been {state}.")

    def setup(self, tree: discord.app_commands.CommandTree):
        @tree.command(name="join", description="Join the voice channel")
        async def join_command(interaction: discord.Interaction):
            await interaction.response.defer()
            await self.join(interaction)

        @tree.command(name="leave", description="Leave the voice channel")
        async def leave_command(interaction: discord.Interaction):
            await interaction.response.defer()
            await self.leave(interaction)

        @tree.command(name="play", description="Play a song from YouTube")
        async def play_command(interaction: discord.Interaction, search: str):
            await interaction.response.defer()
            await self.play(interaction, search)

        @tree.command(name="pause", description="Pause the current song")
        async def pause_command(interaction: discord.Interaction):
            await interaction.response.defer()
            await self.pause(interaction)

        @tree.command(name="resume", description="Resume the paused song")
        async def resume_command(interaction: discord.Interaction):
            await interaction.response.defer()
            await self.resume(interaction)

        @tree.command(name="stop", description="Stop the current song")
        async def stop_command(interaction: discord.Interaction):
            await interaction.response.defer()
            await self.stop(interaction)

        @tree.command(name="volume", description="Set the volume (0 to 1)")
        async def volume_command(interaction: discord.Interaction, volume: float):
            await interaction.response.defer()
            await self.set_volume(interaction, volume)

        @tree.command(name="loop", description="Toggle loop for the current song")
        async def loop_command(interaction: discord.Interaction):
            await interaction.response.defer()
            await self.toggle_loop(interaction)


def setup(bot):
    music = Music(bot)
    music.setup(bot.tree)
