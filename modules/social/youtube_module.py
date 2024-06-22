# modules/social/youtube_module.py
import asyncio
import logging

import discord
from discord import app_commands
from googleapiclient.discovery import build

import config
from modules.data.db import get_connection

logger = logging.getLogger(__name__)


class YouTubeModule:
    def __init__(self, bot):
        self.bot = bot
        self.youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
        self.bot.loop.create_task(self.check_youtube_channels())
        self.add_commands()

    async def check_youtube_channels(self):
        while True:
            conn = get_connection()
            c = conn.cursor()
            c.execute(
                "SELECT youtube_channel_id, discord_channel_id FROM followed_youtube_channels"
            )
            followed_channels = c.fetchall()
            conn.close()

            for youtube_channel_id, discord_channel_id in followed_channels:
                try:
                    request = self.youtube.channels().list(
                        part="contentDetails", id=youtube_channel_id
                    )
                    response = request.execute()
                    if "items" in response and len(response["items"]) > 0:
                        uploads_playlist_id = response["items"][0]["contentDetails"][
                            "relatedPlaylists"
                        ]["uploads"]

                        request = self.youtube.playlistItems().list(
                            part="snippet", playlistId=uploads_playlist_id, maxResults=1
                        )
                        response = request.execute()
                        if "items" in response and len(response["items"]) > 0:
                            latest_video = response["items"][0]["snippet"]
                            video_id = latest_video["resourceId"]["videoId"]
                            title = latest_video["title"]
                            latest_video["publishedAt"]
                            thumbnail_url = latest_video["thumbnails"]["high"]["url"]

                            c.execute(
                                "SELECT last_video_id FROM youtube_status WHERE youtube_channel_id = ?",
                                (youtube_channel_id,),
                            )
                            row = c.fetchone()
                            last_video_id = row[0] if row else None

                            if video_id != last_video_id:
                                channel = self.bot.get_channel(discord_channel_id)
                                if channel:
                                    embed = discord.Embed(
                                        title=f"New Video from {youtube_channel_id}",
                                        description=f"{title}\n[Watch now](https://www.youtube.com/watch?v={video_id})",
                                        color=discord.Color.green(),
                                    )
                                    embed.set_thumbnail(url=thumbnail_url)
                                    await channel.send(embed=embed)

                                c.execute(
                                    "INSERT OR REPLACE INTO youtube_status (youtube_channel_id, last_video_id) VALUES (?, ?)",
                                    (youtube_channel_id, video_id),
                                )
                                conn.commit()
                except Exception as e:
                    logger.error(
                        f"Error checking YouTube channel {youtube_channel_id}: {e}",
                        exc_info=True,
                    )

            conn.close()
            await asyncio.sleep(300)  # Check every 5 minutes

    def add_commands(self):
        @app_commands.command(
            name="follow_youtube",
            description="Follow a YouTube channel to get video updates",
        )
        async def follow_youtube(
            interaction: discord.Interaction,
            youtube_channel_id: str,
            channel: discord.TextChannel = None,
        ):
            channel = channel or interaction.channel
            conn = get_connection()
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO followed_youtube_channels (youtube_channel_id, discord_channel_id) VALUES (?, ?)",
                (youtube_channel_id, channel.id),
            )
            conn.commit()
            conn.close()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Followed YouTube Channel",
                    description=f"Now following {youtube_channel_id}. Alerts will be sent to {channel.mention}.",
                    color=discord.Color.green(),
                )
            )
            logger.info(
                f"Now following {youtube_channel_id} for video updates in {channel.name}"
            )

        @app_commands.command(
            name="unfollow_youtube", description="Unfollow a YouTube channel"
        )
        async def unfollow_youtube(
            interaction: discord.Interaction, youtube_channel_id: str
        ):
            conn = get_connection()
            c = conn.cursor()
            c.execute(
                "DELETE FROM followed_youtube_channels WHERE youtube_channel_id = ?",
                (youtube_channel_id,),
            )
            c.execute(
                "DELETE FROM youtube_status WHERE youtube_channel_id = ?",
                (youtube_channel_id,),
            )
            conn.commit()
            conn.close()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unfollowed YouTube Channel",
                    description=f"No longer following {youtube_channel_id}.",
                    color=discord.Color.red(),
                )
            )
            logger.info(f"No longer following {youtube_channel_id}")

        self.bot.tree.add_command(follow_youtube)
        self.bot.tree.add_command(unfollow_youtube)


async def setup(bot):
    YouTubeModule(bot)
