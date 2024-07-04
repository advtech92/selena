import discord
import sqlite3
import logging
from datetime import datetime

class Profiles:
    ALLOWED_PRONOUNS = ["he/him", "she/her", "they/them", "ask me"]

    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'
        self.logger = logging.getLogger('Profiles')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)

        self.ensure_tables_exist()

    def ensure_tables_exist(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id TEXT,
            guild_id TEXT,
            pronouns TEXT,
            birthday TEXT,
            age INTEGER,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            is_global BOOLEAN DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_stats (
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            game TEXT NOT NULL,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id, game)
        );
        """)

        # Ensure the guild_id column exists in the game_stats table
        cursor.execute("PRAGMA table_info(game_stats);")
        columns = [info[1] for info in cursor.fetchall()]
        if 'guild_id' not in columns:
            cursor.execute("ALTER TABLE game_stats ADD COLUMN guild_id TEXT;")
        
        conn.commit()
        conn.close()
        self.logger.info('Profile and game stats tables ensured in database')

    async def record_win(self, user_id, guild_id, game):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO game_stats (user_id, guild_id, game, wins)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, guild_id, game)
            DO UPDATE SET wins = wins + 1
        """, (user_id, guild_id, game))
        conn.commit()
        conn.close()
        self.logger.info(f'Recorded win for user {user_id} in game {game} in guild {guild_id}')

    async def record_loss(self, user_id, guild_id, game):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO game_stats (user_id, guild_id, game, losses)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, guild_id, game)
            DO UPDATE SET losses = losses + 1
        """, (user_id, guild_id, game))
        conn.commit()
        conn.close()
        self.logger.info(f'Recorded loss for user {user_id} in game {game} in guild {guild_id}')

    async def update_profile(self, user_id, guild_id, pronouns=None, birthday=None, is_global=False):
        if pronouns and pronouns not in self.ALLOWED_PRONOUNS:
            raise ValueError("Invalid pronouns. Allowed values are: " + ", ".join(self.ALLOWED_PRONOUNS))
        age = self.calculate_age(birthday) if birthday else None
        if age is not None and age < 13:
            raise ValueError("You must be at least 13 years old to use Selena.")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO profiles (user_id, guild_id, pronouns, birthday, age, is_global)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, guild_id)
            DO UPDATE SET pronouns = COALESCE(?, pronouns), birthday = COALESCE(?, birthday), age = COALESCE(?, age), is_global = ?
        """, (user_id, guild_id, pronouns, birthday, age, is_global, pronouns, birthday, age, is_global))
        conn.commit()
        conn.close()
        self.logger.info(f'Updated profile for user {user_id} in guild {guild_id}')

    async def get_profile(self, user_id, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pronouns, birthday, age, xp, level, is_global FROM profiles 
            WHERE user_id = ? AND (guild_id = ? OR is_global = 1)
        """, (user_id, guild_id))
        row = cursor.fetchone()
        conn.close()
        return row

    async def get_game_stats(self, user_id, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT game, wins, losses FROM game_stats WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def calculate_age(self, birthday):
        if not birthday:
            return None
        today = datetime.today()
        birthdate = datetime.strptime(birthday, "%Y-%m-%d")
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age

    def setup(self, tree: discord.app_commands.CommandTree):
        @tree.command(name="set_profile", description="Set your profile information")
        async def set_profile_command(interaction: discord.Interaction):
            await interaction.response.send_message("Please select your pronouns and set your birthday:", view=ProfileView(self))

        @tree.command(name="profile", description="View your profile")
        async def profile_command(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            profile = await self.get_profile(user_id, guild_id)
            if profile:
                pronouns, birthday, age, xp, level, is_global = profile
                game_stats = await self.get_game_stats(user_id, guild_id)
                games_info = "\n".join([f"{game}: {wins}W/{losses}L" for game, wins, losses in game_stats])
                embed = discord.Embed(title=f"{interaction.user.display_name}'s Profile")
                embed.add_field(name="Pronouns", value=pronouns or "Not set", inline=True)
                embed.add_field(name="Birthday", value=birthday or "Not set", inline=True)
                embed.add_field(name="Age", value=age or "Not set", inline=True)
                embed.add_field(name="XP", value=xp, inline=True)
                embed.add_field(name="Level", value=level, inline=True)
                embed.add_field(name="Global Profile", value="Yes" if is_global else "No", inline=True)
                embed.add_field(name="Games", value=games_info or "No games played", inline=False)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Profile not found. Please set your profile using /set_profile.", ephemeral=True)

        if not tree.get_command("set_profile"):
            tree.add_command(set_profile_command)

        if not tree.get_command("profile"):
            tree.add_command(profile_command)


class ProfileView(discord.ui.View):
    def __init__(self, profiles):
        super().__init__()
        self.profiles = profiles
        self.add_item(PronounSelect(profiles))

    @discord.ui.button(label="Set Birthday", style=discord.ButtonStyle.primary)
    async def set_birthday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BirthdayModal(self.profiles))


class PronounSelect(discord.ui.Select):
    def __init__(self, profiles):
        self.profiles = profiles
        options = [discord.SelectOption(label=pronoun, value=pronoun) for pronoun in Profiles.ALLOWED_PRONOUNS]
        super().__init__(placeholder="Select your pronouns...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        try:
            await self.profiles.update_profile(user_id, guild_id, pronouns=self.values[0])
            await interaction.response.send_message(f"Your pronouns have been set to {self.values[0]}.", ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)


class BirthdayModal(discord.ui.Modal, title="Set Birthday"):
    birthday = discord.ui.TextInput(label="Your Birthday", placeholder="Enter your birthday (YYYY-MM-DD)...", required=True)

    def __init__(self, profiles):
        super().__init__()
        self.profiles = profiles

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        try:
            birthday = self.birthday.value
            await self.profiles.update_profile(user_id, guild_id, birthday=birthday)
            await interaction.response.send_message("Your birthday has been set.", ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)


def setup(bot):
    profiles = Profiles(bot)
    profiles.setup(bot.tree)
    bot.profiles = profiles
