import logging

import discord
import spotipy
from discord import app_commands
from spotipy.oauth2 import SpotifyOAuth

import config

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
                ),
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
                        embed=discord.Embed(
                            title="Current Track",
                            description="No song is currently playing",
                            color=discord.Color.red(),
                        )
                    )
                    logger.info("No song is currently playing")
                else:
                    track = current["item"]
                    artist = ", ".join([a["name"] for a in track["artists"]])
                    embed = discord.Embed(
                        title="Current Track",
                        description=f"{track['name']} by {artist}",
                        color=discord.Color.green(),
                    )
                    embed.add_field(
                        name="Album", value=track["album"]["name"], inline=False
                    )
                    embed.set_thumbnail(url=track["album"]["images"][0]["url"])
                    await interaction.followup.send(embed=embed)
                    logger.info(
                        f"Currently playing: {track['name']} by {artist}"
                    )  # noqa: E501
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in current_track command: {e}")

        @app_commands.command(
            name="play_track", description="Play a track by searching for it"
        )
        async def play_track(interaction: discord.Interaction, query: str):
            await interaction.response.defer()
            try:
                results = self.sp.search(q=query, limit=1, type="track")
                if not results["tracks"]["items"]:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="Play Track",
                            description="No results found",
                            color=discord.Color.red(),
                        )
                    )
                    logger.info(f"No results found for query: {query}")
                    return

                track = results["tracks"]["items"][0]
                uri = track["uri"]

                devices = self.sp.devices()
                if not devices["devices"]:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="Play Track",
                            description="No active devices found."
                            "Please open Spotify on a device.",
                            color=discord.Color.red(),
                        )
                    )
                    logger.info("No active devices found for playback")
                    return

                self.sp.start_playback(uris=[uri])
                embed = discord.Embed(
                    title="Now Playing",
                    description=f"{track['name']} by {', '.join([a['name'] for a in track['artists']])}",  # noqa: E501
                    color=discord.Color.green(),
                )
                embed.add_field(
                    name="Album", value=track["album"]["name"], inline=False
                )
                embed.set_thumbnail(url=track["album"]["images"][0]["url"])
                await interaction.followup.send(embed=embed)
                logger.info(
                    f"Now playing: {track['name']} by {', '.join([a['name'] for a in track['artists']])}"
                )  # noqa: E501
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in play_track command: {e}")

        @app_commands.command(
            name="play_playlist",
            description="Play a playlist by searching for it" "or providing a link",
        )
        async def play_playlist(interaction: discord.Interaction, query: str):
            await interaction.response.defer()
            try:
                # Check if the query is a link
                if query.startswith("https://open.spotify.com/playlist/"):
                    uri = query.split("/")[-1].split("?")[0]
                    uri = f"spotify:playlist:{uri}"
                else:
                    # Search for the playlist
                    results = self.sp.search(q=query, limit=1, type="playlist")
                    if not results["playlists"]["items"]:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="Play Playlist",
                                description="No results found",
                                color=discord.Color.red(),
                            )
                        )
                        logger.info(f"No results found for query: {query}")
                        return
                    playlist = results["playlists"]["items"][0]
                    uri = playlist["uri"]

                devices = self.sp.devices()
                if not devices["devices"]:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="Play Playlist",
                            description="No active devices found."
                            "Please open Spotify on a device.",
                            color=discord.Color.red(),
                        )
                    )
                    logger.info("No active devices found for playback")
                    return

                self.sp.start_playback(context_uri=uri)
                embed = discord.Embed(
                    title="Now Playing Playlist",
                    description=(
                        f"{playlist['name']} by {playlist['owner']['display_name']}"
                        if not query.startswith("https://open.spotify.com/playlist/")
                        else "Playing playlist"
                    ),  # noqa: E501
                    color=discord.Color.green(),
                )
                if not query.startswith("https://open.spotify.com/playlist/"):
                    embed.set_thumbnail(url=playlist["images"][0]["url"])
                await interaction.followup.send(embed=embed)
                logger.info(
                    f"Now playing playlist: {playlist['name']} by {playlist['owner']['display_name']}"
                )  # noqa: E501
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in play_playlist command: {e}")

        @app_commands.command(
            name="pause", description="Pause the currently playing track"
        )
        async def pause(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                self.sp.pause_playback()
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Pause",
                        description="Playback paused.",
                        color=discord.Color.green(),
                    )
                )
                logger.info("Playback paused")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in pause command: {e}")

        @app_commands.command(
            name="resume", description="Resume the currently playing track"
        )
        async def resume(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                self.sp.start_playback()
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Resume",
                        description="Playback resumed.",
                        color=discord.Color.green(),
                    )
                )
                logger.info("Playback resumed")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in resume command: {e}")

        @app_commands.command(name="next", description="Skip to the next track")
        async def next_track(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                self.sp.next_track()
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Next Track",
                        description="Skipped to the next track.",
                        color=discord.Color.green(),
                    )
                )
                logger.info("Skipped to the next track")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in next_track command: {e}")

        @app_commands.command(
            name="previous", description="Go back to the previous track"
        )
        async def previous_track(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                self.sp.previous_track()
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Previous Track",
                        description="Returned to the previous track.",
                        color=discord.Color.green(),
                    )
                )
                logger.info("Returned to the previous track")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in previous_track command: {e}")

        self.bot.tree.add_command(current_track)
        self.bot.tree.add_command(play_track)
        self.bot.tree.add_command(play_playlist)
        self.bot.tree.add_command(pause)
        self.bot.tree.add_command(resume)
        self.bot.tree.add_command(next_track)
        self.bot.tree.add_command(previous_track)


async def setup(bot):
    SpotifyModule(bot)
