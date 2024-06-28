# xp.py
import discord
from discord import app_commands
import sqlite3
import random


class XP:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'

    def calculate_level(self, xp):
        level = 1
        while xp >= 5 * (level ** 2) + 50 * level + 100:
            level += 1
        return level

    async def add_xp(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        earned_xp = random.randint(5, 15)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO guild_xp (guild_id, user_id, xp, level) 
            VALUES (?, ?, ?, 1) 
            ON CONFLICT(guild_id, user_id) 
            DO UPDATE SET xp = xp + ?
        """, (guild_id, user_id, earned_xp, earned_xp))
        conn.commit()
        cursor.execute("SELECT xp, level FROM guild_xp WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        xp, level = cursor.fetchone()
        new_level = self.calculate_level(xp)
        if new_level > level:
            cursor.execute("UPDATE guild_xp SET level = ? WHERE guild_id = ? AND user_id = ?", (new_level, guild_id, user_id))
        conn.commit()
        conn.close()

        await interaction.response.send_message(f"You earned {earned_xp} XP! You now have {xp} XP and are level {new_level}.", ephemeral=False)

    async def check_xp(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT xp, level FROM guild_xp WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        result = cursor.fetchone()
        conn.close()

        if result:
            xp, level = result
            await interaction.response.send_message(f"You have {xp} XP and are level {level}.", ephemeral=False)
        else:
            await interaction.response.send_message("You don't have any XP yet.", ephemeral=False)

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="earn_xp", description="Earn XP")
        async def earn_xp_command(interaction: discord.Interaction):
            await self.add_xp(interaction)

        @tree.command(name="check_xp", description="Check your XP and level")
        async def check_xp_command(interaction: discord.Interaction):
            await self.check_xp(interaction)

        if not tree.get_command("earn_xp"):
            tree.add_command(earn_xp_command)

        if not tree.get_command("check_xp"):
            tree.add_command(check_xp_command)
