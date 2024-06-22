import asyncio
import logging

import discord
from discord import app_commands
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch

import config
from modules.data.db import get_connection

logger = logging.getLogger(__name__)


class TwitchModule:
    def __init__(self, bot):
        self.bot = bot
        self.twitch = Twitch(config.TWITCH_CLIENT_ID, config.TWITCH_CLIENT_SECRET)
        self.bot.loop.create_task(self.authenticate_twitch())
        self.bot.loop.create_task(self.check_live_streams())
        self.add_commands()

    async def authenticate_twitch(self):
        await self.twitch.authenticate_app([])  # Authenticate without scopes

    async def check_live_streams(self):
        while True:
            conn = get_connection()
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS live_status (
                    twitch_name TEXT PRIMARY KEY,
                    is_live BOOLEAN
                )
            """
            )
            conn.commit()

            c.execute("SELECT twitch_name, discord_channel_id FROM followed_channels")
            followed_channels = c.fetchall()

            for twitch_name, discord_channel_id in followed_channels:
                try:
                    user_info = await first(self.twitch.get_users(logins=[twitch_name]))
                    if not user_info:
                        continue

                    user_id = user_info.id
                    streams = await first(self.twitch.get_streams(user_id=[user_id]))
                    is_live = streams is not None

                    c.execute(
                        "SELECT is_live FROM live_status WHERE twitch_name = ?",
                        (twitch_name,),
                    )
                    row = c.fetchone()
                    was_live = row[0] if row else False

                    if is_live and not was_live:
                        channel = self.bot.get_channel(discord_channel_id)
                        if channel:
                            embed = discord.Embed(
                                title=f"{twitch_name} is Live!",
                                description=(
                                    f"**Title:** {streams.title}\n"
                                    f"**Game:** {streams.game_name}\n"
                                    f"**Viewers:** {streams.viewer_count}"
                                ),
                                color=discord.Color.green(),
                            )
                            embed.set_thumbnail(
                                url=streams.thumbnail_url.replace(
                                    "{width}", "320"
                                ).replace("{height}", "180")
                            )
                            await channel.send(embed=embed)

                    c.execute(
                        "INSERT OR REPLACE INTO live_status (twitch_name, is_live) VALUES (?, ?)",
                        (twitch_name, is_live),
                    )
                    conn.commit()

                except Exception as e:
                    logger.error(
                        f"Error checking live status for {twitch_name}: {e}",
                        exc_info=True,
                    )

            conn.close()
            await asyncio.sleep(300)  # Check every 5 minutes

    def add_commands(self):
        @app_commands.command(
            name="follow_twitch",
            description="Follow a Twitch channel to get live alerts",
        )
        async def follow_twitch(
            interaction: discord.Interaction,
            twitch_name: str,
            channel: discord.TextChannel = None,
        ):
            channel = channel or interaction.channel
            conn = get_connection()
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO followed_channels (twitch_name, discord_channel_id) VALUES (?, ?)",
                (twitch_name, channel.id),
            )
            conn.commit()
            conn.close()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Followed Twitch Channel",
                    description=f"Now following {twitch_name}. Alerts will be sent to {channel.mention}.",
                    color=discord.Color.green(),
                )
            )
            logger.info(f"Now following {twitch_name} for alerts in {channel.name}")

        @app_commands.command(
            name="unfollow_twitch", description="Unfollow a Twitch channel"
        )
        async def unfollow_twitch(interaction: discord.Interaction, twitch_name: str):
            conn = get_connection()
            c = conn.cursor()
            c.execute(
                "DELETE FROM followed_channels WHERE twitch_name = ?", (twitch_name,)
            )
            c.execute("DELETE FROM live_status WHERE twitch_name = ?", (twitch_name,))
            conn.commit()
            conn.close()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unfollowed Twitch Channel",
                    description=f"No longer following {twitch_name}.",
                    color=discord.Color.red(),
                )
            )
            logger.info(f"No longer following {twitch_name}")

        @app_commands.command(
            name="twitch_live", description="Check if a Twitch streamer is live"
        )
        async def twitch_live(interaction: discord.Interaction, streamer: str):
            await interaction.response.defer()
            try:
                logger.debug(f"Fetching user info for streamer: {streamer}")
                user_info = await first(self.twitch.get_users(logins=[streamer]))
                if not user_info:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="Twitch Live Check",
                            description=f"Streamer {streamer} not found.",
                            color=discord.Color.red(),
                        )
                    )
                    logger.info(f"Streamer {streamer} not found.")
                    return

                user_id = user_info.id
                logger.debug(f"Fetching stream info for user ID: {user_id}")
                streams = await first(self.twitch.get_streams(user_id=[user_id]))
                if streams:
                    embed = discord.Embed(
                        title=f"{streamer} is Live!",
                        description=(
                            f"**Title:** {streams.title}\n"
                            f"**Game:** {streams.game_name}\n"
                            f"**Viewers:** {streams.viewer_count}"
                        ),
                        color=discord.Color.green(),
                    )
                    embed.set_thumbnail(
                        url=streams.thumbnail_url.replace("{width}", "320").replace(
                            "{height}", "180"
                        )
                    )
                    await interaction.followup.send(embed=embed)
                    logger.info(f"Streamer {streamer} is live.")
                else:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title=f"{streamer} is not live",
                            description=f"{streamer} is currently offline.",
                            color=discord.Color.red(),
                        )
                    )
                    logger.info(f"Streamer {streamer} is offline.")
            except Exception as e:
                logger.error(f"Error in twitch_live command: {e}", exc_info=True)
                await interaction.followup.send(f"An error occurred: {e}")

        self.bot.tree.add_command(follow_twitch)
        self.bot.tree.add_command(unfollow_twitch)
        self.bot.tree.add_command(twitch_live)


async def setup(bot):
    TwitchModule(bot)
