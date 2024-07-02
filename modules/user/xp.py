import discord
import sqlite3
import random
import logging
import asyncio


class XP:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'data/selena.db'
        self.logger = logging.getLogger('XP')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)
        self.cooldown = 10  # Cooldown time in seconds
        self.xp_range = (5, 15)  # Range of XP that can be earned per message
        self.user_cooldowns = {}

        self.ensure_table_exists()

    def ensure_table_exists(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            xp INTEGER NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        );
        """)
        conn.commit()
        conn.close()
        self.logger.info('XP table ensured in database')

    async def add_xp(self, guild_id, user_id, xp):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO xp (guild_id, user_id, xp)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET xp = xp + excluded.xp
        """, (guild_id, user_id, xp))
        conn.commit()
        conn.close()
        self.logger.debug(f'Added {xp} XP to user {user_id} in guild {guild_id}')

    async def get_xp(self, guild_id, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT xp FROM xp WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    async def handle_message(self, message):
        self.logger.debug(f'Received message from user {message.author.id} in guild {message.guild.id}')

        if message.author.bot:
            self.logger.debug('Message author is a bot, ignoring.')
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        if user_id in self.user_cooldowns and self.user_cooldowns[user_id] > asyncio.get_event_loop().time():
            self.logger.debug(f'User {user_id} is on cooldown')
            return

        xp = random.randint(*self.xp_range)
        await self.add_xp(guild_id, user_id, xp)
        self.user_cooldowns[user_id] = asyncio.get_event_loop().time() + self.cooldown
        self.logger.info(f'Added {xp} XP to user {user_id} in guild {guild_id}')

    def setup(self, tree: discord.app_commands.CommandTree):
        @tree.command(name="check_xp", description="Check your XP")
        async def check_xp_command(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            xp = await self.get_xp(guild_id, user_id)
            await interaction.response.send_message(embed=discord.Embed(description=f"You have {xp} XP.", color=discord.Color.green()))

        if not tree.get_command("check_xp"):
            tree.add_command(check_xp_command)

    async def setup_hook(self):
        self.bot.event(self.handle_message)
        self.logger.info('XP module setup complete and listener added')


def setup(bot):
    xp = XP(bot)
    xp.setup(bot.tree)
    bot.loop.create_task(xp.setup_hook())
