import discord
from discord import app_commands
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config


class SpotifyModule:
    def __init__(self, bot):
        self.bot = bot
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=config.SPOTIPY_CLIENT_ID,
                client_secret=config.SPOTIPY_CLIENT_SECRET,
                redirect_uri=config.SPOTIPY_REDIRECT_URI,
                scope=(
                    "user-library-read user-read-playback-state "
                    "user-modify-playback-state user-read-currently-playing"
                )
            )
        )
        self.add_commands()

    def add_commands(self):
        @app_commands.command(
            name="current_track", description="Get the currently playing song"
        )
        async def current_track(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                current = self.sp.currently_playing()
                if current is None or current["item"] is None:
                    await interaction.followup.send(
                        "No song is currently playing"
                    )
                else:
                    track = current["item"]
                    artist = ", ".join([a["name"] for a in track["artists"]])
                    await interaction.followup.send(
                        f"Currently playing: {track['name']} by {artist} "
                        f"({track['album']['name']})"
                    )
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="play_track", description="Play a track by searching for it"
        )
        async def play_track(interaction: discord.Interaction, query: str):
            await interaction.response.defer()
            try:
                results = self.sp.search(q=query, limit=1, type="track")
                if not results["tracks"]["items"]:
                    await interaction.followup.send("No results found")
                    return

                track = results["tracks"]["items"][0]
                uri = track["uri"]

                devices = self.sp.devices()
                if not devices["devices"]:
                    await interaction.followup.send(
                        "No active devices found. Please open Spotify on a "
                        "device."
                    )
                    return

                self.sp.start_playback(uris=[uri])
                await interaction.followup.send(
                    f"Now playing: {track['name']} by "
                    f"{', '.join([a['name'] for a in track['artists']])} "
                    f"({track['album']['name']})"
                )
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="play_playlist",
            description="Play a playlist by searching for it"
        )
        async def play_playlist(interaction: discord.Interaction, query: str):
            await interaction.response.defer()
            try:
                results = self.sp.search(q=query, limit=1, type="playlist")
                if not results["playlists"]["items"]:
                    await interaction.followup.send("No results found")
                    return

                playlist = results["playlists"]["items"][0]
                uri = playlist["uri"]

                devices = self.sp.devices()
                if not devices["devices"]:
                    await interaction.followup.send(
                        "No active devices found. Please open Spotify on a "
                        "device."
                    )
                    return

                self.sp.start_playback(context_uri=uri)
                await interaction.followup.send(
                    f"Now playing playlist: {playlist['name']} by "
                    f"{playlist['owner']['display_name']}"
                )
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="pause", description="Pause the currently playing track"
        )
        async def pause(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                self.sp.pause_playback()
                await interaction.followup.send("Playback paused.")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="resume", description="Resume the currently playing track"
        )
        async def resume(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                self.sp.start_playback()
                await interaction.followup.send("Playback resumed.")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="next", description="Skip to the next track"
        )
        async def next_track(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                self.sp.next_track()
                await interaction.followup.send("Skipped to the next track.")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="previous", description="Go back to the previous track"
        )
        async def previous_track(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                self.sp.previous_track()
                await interaction.followup.send(
                    "Returned to the previous track."
                )
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        self.bot.tree.add_command(current_track)
        self.bot.tree.add_command(play_track)
        self.bot.tree.add_command(play_playlist)
        self.bot.tree.add_command(pause)
        self.bot.tree.add_command(resume)
        self.bot.tree.add_command(next_track)
        self.bot.tree.add_command(previous_track)


async def setup(bot):
    SpotifyModule(bot)
