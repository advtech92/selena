import discord
from discord import app_commands
import random
import logging
import sqlite3
from cryptography.fernet import Fernet
import datetime
import asyncio


class WordleGame:
    def __init__(self, user, word, date):
        self.user = user
        self.word = word
        self.date = date
        self.guesses = []

    def guess_word(self, guess):
        self.guesses.append(guess)
        return self.check_guess(guess)

    def check_guess(self, guess):
        feedback = ['⬛'] * 5
        for i, letter in enumerate(guess):
            if letter == self.word[i]:
                feedback[i] = '🟩'
            elif letter in self.word:
                feedback[i] = '🟨'
        return ''.join(feedback)

    def is_complete(self):
        return self.guesses and self.guesses[-1] == self.word

    def render_board(self):
        return "\n".join([f"Guess {i+1}: {guess} -> {self.check_guess(guess)}" for i, guess in enumerate(self.guesses)])


class Wordle:
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.logger = logging.getLogger('Wordle')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)
        self.db_path = 'data/selena.db'

        self.key = self.load_key()
        self.cipher_suite = Fernet(self.key)
        self.words = self.load_words()

        self.ensure_table_exists()

    def load_key(self):
        with open('data/wordlist.key', 'rb') as key_file:
            return key_file.read()

    def load_words(self):
        with open('data/encrypted_word_list.bin', 'rb') as f:
            encrypted_words = f.read().splitlines()
        return [self.cipher_suite.decrypt(word).decode() for word in encrypted_words]

    def ensure_table_exists(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wordle (
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            word TEXT NOT NULL,
            guesses TEXT,
            PRIMARY KEY (user_id, date)
        );
        """)
        conn.commit()
        conn.close()

    def get_today_word(self):
        today = datetime.date.today()
        word_index = (today - datetime.date(2022, 1, 1)).days % len(self.words)
        return self.words[word_index]

    async def start_game(self, interaction):
        user_id = str(interaction.user.id)
        today = datetime.date.today().isoformat()
        word = self.get_today_word()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM wordle WHERE user_id = ? AND date = ?", (user_id, today))
        row = cursor.fetchone()

        if row:
            await interaction.response.send_message("You have already played today's Wordle.", ephemeral=True)
            return
        else:
            cursor.execute("INSERT INTO wordle (user_id, date, word) VALUES (?, ?, ?)", (user_id, today, word))
            conn.commit()
            conn.close()

            thread = await interaction.channel.create_thread(name=f"Wordle: {interaction.user.display_name}", type=discord.ChannelType.public_thread)
            self.games[thread.id] = WordleGame(interaction.user, word, today)
            initial_message = await thread.send(f"{interaction.user.mention}, welcome to today's Wordle! Start guessing the 5-letter word.", view=WordleView(self.bot))
            self.games[thread.id].message = initial_message
            await interaction.response.send_message("Game started in a new thread!", ephemeral=True)

    async def guess_word(self, interaction, guess):
        game = self.games.get(interaction.channel_id)
        if not game:
            await interaction.response.send_message("There is no game in progress in this thread.", ephemeral=True)
            return

        if len(guess) != 5:
            await interaction.response.send_message("Your guess must be a 5-letter word.", ephemeral=True)
            return

        feedback = game.guess_word(guess.lower())
        if game.is_complete():
            await self.update_game_message(game, interaction, f"{interaction.user.mention} guessed the word! The word was **{game.word}**.\n{game.render_board()}")
            del self.games[interaction.channel_id]
            await self.record_win(interaction.user.id)
            await interaction.channel.send("This thread will be archived in 2 minutes.")
            await asyncio.sleep(120)
            await interaction.channel.archive()
        else:
            await self.update_game_message(game, interaction, f"{interaction.user.mention} guessed **{guess}**. Feedback: {feedback}\n{game.render_board()}")

    async def update_game_message(self, game, interaction, content, view=None):
        try:
            await game.message.edit(content=content, view=view)
        except discord.NotFound:
            game.message = await interaction.channel.send(content=content, view=view)

    async def record_win(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO wordle_stats (user_id, wins)
            VALUES (?, 1)
            ON CONFLICT(user_id)
            DO UPDATE SET wins = wins + 1
        """, (user_id,))
        conn.commit()
        conn.close()

    async def record_loss(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO wordle_stats (user_id, losses)
            VALUES (?, 1)
            ON CONFLICT(user_id)
            DO UPDATE SET losses = losses + 1
        """, (user_id,))
        conn.commit()
        conn.close()

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="start_wordle", description="Start a game of Wordle")
        async def start_wordle_command(interaction: discord.Interaction):
            await self.start_game(interaction)

        if not tree.get_command("start_wordle"):
            tree.add_command(start_wordle_command)


class WordleView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Guess Word", style=discord.ButtonStyle.primary)
    async def guess_word_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GuessInput(self.bot))


class GuessInput(discord.ui.Modal, title="Wordle Guess"):
    guess = discord.ui.TextInput(label="Your Guess", placeholder="Enter a 5-letter word...", max_length=5)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await self.bot.wordle_module.guess_word(interaction, self.guess.value)


def setup(bot):
    wordle = Wordle(bot)
    wordle.setup(bot.tree)
    bot.wordle_module = wordle
