import discord
from discord import app_commands
import yt_dlp
import asyncio
import json
import os

class Music:
    def __init__(self, client):
        self.client = client
        self.voice_clients = {}
        self.music_queues = {}
        self.current_tracks = {}
        self.save_file = 'music_state.json'
        self.volumes = {}  # Store volume levels per guild
        self.default_volume = 0.5  # Default volume level (50%)

        # Load saved state for auto-resume
        self.load_music_state()

        # Register app commands
        self.register_commands()

    def register_commands(self):
        @app_commands.command(name='play', description='Play a song by title and artist')
        async def play(interaction: discord.Interaction, *, query: str):
            await self.play(interaction, query)

        @app_commands.command(name='pause', description='Pause the current song')
        async def pause(interaction: discord.Interaction):
            await self.pause(interaction)

        @app_commands.command(name='resume', description='Resume the paused song')
        async def resume(interaction: discord.Interaction):
            await self.resume(interaction)

        @app_commands.command(name='skip', description='Skip the current song')
        async def skip(interaction: discord.Interaction):
            await self.skip(interaction)

        @app_commands.command(name='stop', description='Stop playback and clear the queue')
        async def stop(interaction: discord.Interaction):
            await self.stop(interaction)

        @app_commands.command(name='volume', description='Set the playback volume')
        @app_commands.describe(level='Volume level between 0 and 100')
        async def volume(interaction: discord.Interaction, level: int):
            await self.set_volume(interaction, level)

        # Add commands to the client's tree
        self.client.tree.add_command(play)
        self.client.tree.add_command(pause)
        self.client.tree.add_command(resume)
        self.client.tree.add_command(skip)
        self.client.tree.add_command(stop)
        self.client.tree.add_command(volume)

    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        guild_id = interaction.guild_id

        # Check if the user is in a voice channel
        if interaction.user.voice is None:
            await interaction.followup.send("You must be connected to a voice channel to use this command.")
            return

        # Connect to the voice channel if not already connected
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            channel = interaction.user.voice.channel
            self.voice_clients[guild_id] = await channel.connect()

        # Ensure volume is set
        if guild_id not in self.volumes:
            self.volumes[guild_id] = self.default_volume

        await interaction.followup.send(f"🔍 **Searching for:** {query}")

        # Search YouTube for the song
        search_url = await self.search_youtube(query)
        if not search_url:
            await interaction.followup.send("❌ **Could not find the song on YouTube.**")
            return

        # Add URL to the music queue
        if guild_id not in self.music_queues:
            self.music_queues[guild_id] = []
        self.music_queues[guild_id].append(search_url)

        await interaction.followup.send(f"✅ **Added to queue:** {query}")

        # If nothing is playing, start playing
        if not self.voice_clients[guild_id].is_playing():
            await self.play_next(guild_id)

    async def search_youtube(self, query):
        """Searches YouTube for the query and returns the URL of the first result."""
        ytdl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'default_search': 'ytsearch',
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
            try:
                info = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
                if 'entries' in info:
                    # Take the first item from the search results
                    video = info['entries'][0]
                else:
                    video = info
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                return video_url
            except Exception as e:
                print(f"Error searching YouTube: {e}")
                return None

    async def play_next(self, guild_id):
        if guild_id not in self.music_queues or not self.music_queues[guild_id]:
            await self.voice_clients[guild_id].disconnect()
            return

        url = self.music_queues[guild_id].pop(0)
        self.current_tracks[guild_id] = url

        try:
            # Use yt_dlp to get audio source
            ytdl_opts = {'format': 'bestaudio/best'}
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                info = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                audio_url = info['url']
                title = info.get('title', 'Unknown Title')
                webpage_url = info.get('webpage_url', url)
                thumbnail = info.get('thumbnail')

            # Prepare FFmpeg options
            ffmpeg_opts = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn',
            }

            # Create audio source using FFmpegPCMAudio
            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_opts)
            volume = self.volumes.get(guild_id, self.default_volume)
            source = discord.PCMVolumeTransformer(source, volume=volume)

            # Play audio
            self.voice_clients[guild_id].play(source, after=lambda e: self.after_song(e, guild_id))

            # Send an embedded message indicating the song is now playing
            embed = discord.Embed(
                title="Now Playing 🎵",
                description=f"[{title}]({webpage_url})",
                color=discord.Color.blue()
            )
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)

            channel = self.voice_clients[guild_id].channel
            text_channel = channel.guild.system_channel or channel.guild.text_channels[0]
            await text_channel.send(embed=embed)

            # Save state for auto-resume
            self.save_music_state()

        except Exception as e:
            print(f"Error during playback: {e}")
            await self.voice_clients[guild_id].disconnect()

    def after_song(self, error, guild_id):
        if error:
            print(f"Error: {error}")
        coro = self.play_next(guild_id)
        asyncio.run_coroutine_threadsafe(coro, self.client.loop)

    async def pause(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_playing():
            self.voice_clients[guild_id].pause()
            await interaction.response.send_message("⏸️ **Music paused.**")
        else:
            await interaction.response.send_message("❌ **No music is playing.**")

    async def resume(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_paused():
            self.voice_clients[guild_id].resume()
            await interaction.response.send_message("▶️ **Music resumed.**")
        else:
            await interaction.response.send_message("❌ **No music is paused.**")

    async def skip(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_playing():
            self.voice_clients[guild_id].stop()
            await interaction.response.send_message("⏭️ **Skipped current song.**")
        else:
            await interaction.response.send_message("❌ **No music is playing.**")

    async def stop(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id in self.voice_clients:
            self.voice_clients[guild_id].stop()
            self.music_queues[guild_id] = []
            await self.voice_clients[guild_id].disconnect()
            await interaction.response.send_message("🛑 **Playback stopped and queue cleared.**")
        else:
            await interaction.response.send_message("❌ **No music is playing.**")

    async def set_volume(self, interaction: discord.Interaction, level: int):
        guild_id = interaction.guild_id

        # Validate volume level
        if level < 0 or level > 100:
            await interaction.response.send_message("❌ **Volume must be between 0 and 100.**")
            return

        # Set the volume
        volume = level / 100  # Convert to a 0.0 - 1.0 scale
        self.volumes[guild_id] = volume

        # Adjust volume if something is playing
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_playing():
            current_source = self.voice_clients[guild_id].source
            if isinstance(current_source, discord.PCMVolumeTransformer):
                current_source.volume = volume
            else:
                # Wrap the existing source with PCMVolumeTransformer
                self.voice_clients[guild_id].source = discord.PCMVolumeTransformer(current_source, volume=volume)

        await interaction.response.send_message(f"🔊 **Volume set to {level}%.**")

    def save_music_state(self):
        state = {
            'current_tracks': self.current_tracks,
            'music_queues': self.music_queues,
            'volumes': self.volumes
        }
        with open(self.save_file, 'w') as f:
            json.dump(state, f)

    def load_music_state(self):
        if os.path.exists(self.save_file):
            with open(self.save_file, 'r') as f:
                state = json.load(f)
                self.current_tracks = state.get('current_tracks', {})
                self.music_queues = state.get('music_queues', {})
                self.volumes = state.get('volumes', {})
        else:
            self.current_tracks = {}
            self.music_queues = {}
            self.volumes = {}
