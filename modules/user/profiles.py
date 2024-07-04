import discord
import sqlite3
import logging


class Profiles:
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

    async def update_profile(self, user_id, guild_id, pronouns=None, age=None, is_global=False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO profiles (user_id, guild_id, pronouns, age, is_global)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, guild_id)
            DO UPDATE SET pronouns = COALESCE(?, pronouns), age = COALESCE(?, age), is_global = ?
        """, (user_id, guild_id, pronouns, age, is_global, pronouns, age, is_global))
        conn.commit()
        conn.close()
        self.logger.info(f'Updated profile for user {user_id} in guild {guild_id}')

    async def get_profile(self, user_id, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pronouns, age, xp, level, is_global FROM profiles 
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

    def setup(self, tree: discord.app_commands.CommandTree):
        @tree.command(name="set_profile", description="Set your profile information")
        async def set_profile_command(interaction: discord.Interaction, pronouns: str = None, age: int = None, is_global: bool = False):
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            await self.update_profile(user_id, guild_id, pronouns, age, is_global)
            await interaction.response.send_message("Your profile has been updated.", ephemeral=True)

        @tree.command(name="profile", description="View your profile")
        async def profile_command(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            profile = await self.get_profile(user_id, guild_id)
            if profile:
                pronouns, age, xp, level, is_global = profile
                game_stats = await self.get_game_stats(user_id, guild_id)
                games_info = "\n".join([f"{game}: {wins}W/{losses}L" for game, wins, losses in game_stats])
                embed = discord.Embed(title=f"{interaction.user.display_name}'s Profile")
                embed.add_field(name="Pronouns", value=pronouns or "Not set", inline=True)
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


def setup(bot):
    profiles = Profiles(bot)
    profiles.setup(bot.tree)
    bot.profiles = profiles
