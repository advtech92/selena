import discord
from discord import app_commands
import sqlite3


class DataPrivacy:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'

    async def fetch_user_data(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_data WHERE user_id = ?", (user_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    async def delete_user_data(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_data WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="request_data", description="Request your stored data")
        async def request_data_command(interaction: discord.Interaction):
            user_id = interaction.user.id
            data = await self.fetch_user_data(user_id)
            if data:
                await interaction.response.send_message(f"Your data: {data}", ephemeral=True)
            else:
                await interaction.response.send_message("No data found for your user.", ephemeral=True)

        @tree.command(name="delete_data", description="Request deletion of your stored data")
        async def delete_data_command(interaction: discord.Interaction):
            user_id = interaction.user.id
            await self.delete_user_data(user_id)
            await interaction.response.send_message("Your data has been deleted.", ephemeral=True)

        if not tree.get_command("request_data"):
            tree.add_command(request_data_command)

        if not tree.get_command("delete_data"):
            tree.add_command(delete_data_command)


def setup(bot):
    data_privacy = DataPrivacy(bot)
    data_privacy.setup(bot.tree)
