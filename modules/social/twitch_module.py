import discord
from discord import app_commands
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
import logging
import config

logger = logging.getLogger(__name__)


class TwitchModule:
    def __init__(self, bot):
        self.bot = bot
        self.twitch = Twitch(config.TWITCH_CLIENT_ID,
                             config.TWITCH_CLIENT_SECRET)
        self.bot.loop.create_task(self.authenticate_twitch())
        self.add_commands()

    async def authenticate_twitch(self):
        await self.twitch.authenticate_app([])

    def add_commands(self):
        @app_commands.command(
            name="twitch_live",
            description="Check if a Twitch streamer is live"
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
                            color=discord.Color.red()
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
                        color=discord.Color.green()
                    )
                    embed.set_thumbnail(
                        url=streams.thumbnail_url.replace('{width}', '320').replace('{height}', '180')
                    )
                    await interaction.followup.send(embed=embed)
                    logger.info(f"Streamer {streamer} is live.")
                else:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title=f"{streamer} is not live",
                            description=f"{streamer} is currently offline.",
                            color=discord.Color.red()
                        )
                    )
                    logger.info(f"Streamer {streamer} is offline.")
            except Exception as e:
                logger.error(f"Error in twitch_live command: {e}", exc_info=True)
                await interaction.followup.send(f"An error occurred: {e}")

        self.bot.tree.add_command(twitch_live)


async def setup(bot):
    TwitchModule(bot)
