import discord
from discord import app_commands
import sqlite3


class TermsPrivacy:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'
        self.privacy_policy_url = "https://advtech92.github.io/selena-website/privacy_policy.html"
        self.terms_of_service_url = "https://advtech92.github.io/selena-website/terms_of_service.html"

    async def user_opt_out(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO opt_out_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()

    async def user_opt_in(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM opt_out_users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    async def is_user_opted_out(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM opt_out_users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="privacy_policy", description="Show the privacy policy")
        async def privacy_policy_command(interaction: discord.Interaction):
            embed = discord.Embed(title="Privacy Policy", url=self.privacy_policy_url, description="Read our privacy policy.", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @tree.command(name="terms_of_service", description="Show the terms of service")
        async def terms_of_service_command(interaction: discord.Interaction):
            embed = discord.Embed(title="Terms of Service", url=self.terms_of_service_url, description="Read our terms of service.", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @tree.command(name="opt_out", description="Opt out of using the bot")
        async def opt_out_command(interaction: discord.Interaction):
            user_id = interaction.user.id
            await self.user_opt_out(user_id)
            await interaction.response.send_message("You have opted out of using the bot.", ephemeral=True)

        @tree.command(name="opt_in", description="Opt back in to using the bot")
        async def opt_in_command(interaction: discord.Interaction):
            user_id = interaction.user.id
            await self.user_opt_in(user_id)
            await interaction.response.send_message("You have opted back in to using the bot.", ephemeral=True)

        if not tree.get_command("privacy_policy"):
            tree.add_command(privacy_policy_command)

        if not tree.get_command("terms_of_service"):
            tree.add_command(terms_of_service_command)

        if not tree.get_command("opt_out"):
            tree.add_command(opt_out_command)

        if not tree.get_command("opt_in"):
            tree.add_command(opt_in_command)


def setup(bot):
    terms_privacy = TermsPrivacy(bot)
    terms_privacy.setup(bot.tree)
