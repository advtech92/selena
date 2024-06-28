# currency.py
import discord
from discord import app_commands
import sqlite3
import random


class Currency:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'

    async def earn_kibble(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        earned = random.randint(1, 10)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO guild_currency (guild_id, user_id, balance) 
            VALUES (?, ?, ?) 
            ON CONFLICT(guild_id, user_id) 
            DO UPDATE SET balance = balance + ?
        """, (guild_id, user_id, earned, earned))
        conn.commit()
        cursor.execute("SELECT balance FROM guild_currency WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        balance = cursor.fetchone()[0]
        conn.close()

        await interaction.response.send_message(f"You earned {earned} Kibble! You now have {balance} Kibble.", ephemeral=False)

    async def balance(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM guild_currency WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        result = cursor.fetchone()
        conn.close()

        balance = result[0] if result else 0
        await interaction.response.send_message(f"You have {balance} Kibble.", ephemeral=False)

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="earn_kibble", description="Earn Kibble currency")
        async def earn_kibble_command(interaction: discord.Interaction):
            await self.earn_kibble(interaction)

        @tree.command(name="balance", description="Check your Kibble balance")
        async def balance_command(interaction: discord.Interaction):
            await self.balance(interaction)

        if not tree.get_command("earn_kibble"):
            tree.add_command(earn_kibble_command)

        if not tree.get_command("balance"):
            tree.add_command(balance_command)
