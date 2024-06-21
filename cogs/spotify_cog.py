import discord
from discord import app_commands
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config


class SpotifyCog(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=config.SPOTIFY_REDIRECT_URI,
                scope=(
                    "user-library-read user-read-playback-state "
                    "user-modify-playback-state user-read-currently-playing"
                )
            )
        )

    @app_commands.command(
        name="current_track", description="Get the currently playing song"
    )
    async def current_track(self, interaction: discord.Interaction):
        current = self.sp.currently_playing()
        if current is None or current["item"] is None:
            await interaction.response.send_message(
                "No song is currently playing"
            )
        else:
            track = current["item"]
            artist = ", ".join([artist["name"] for artist in track["artists"]])
            await interaction.response.send_message(
                f"Currently playing: {track['name']} by {artist} "
                f"({track['album']['name']})"
            )

    @app_commands.command(
        name="play_track", description="Play a track by searching for it"
    )
    async def play_track(self, interaction: discord.Interaction, query: str):
        results = self.sp.search(q=query, limit=1, type="track")
        if not results["tracks"]["items"]:
            await interaction.response.send_message("No results found")
            return

        track = results["tracks"]["items"][0]
        uri = track["uri"]
        self.sp.start_playback(uris=[uri])
        await interaction.response.send_message(
            f"Now playing: {track['name']} by "
            f"{', '.join([artist['name'] for artist in track['artists']])} "
            f"({track['album']['name']})"
        )


async def setup(bot):
    await bot.add_cog(SpotifyCog(bot))
