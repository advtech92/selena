import discord
import random
import logging
import sqlite3
from datetime import datetime
from discord.ext import tasks
from discord import app_commands
from cryptography.fernet import Fernet


class WordleGame:
    def __init__(self, user_id, guild_id, target_word):
        self.user_id = user_id
        self.guild_id = guild_id
        self.target_word = target_word
        self.guesses = []
        self.max_attempts = 6

    def make_guess(self, guess):
        if len(guess) != 5 or not guess.isalpha():
            raise ValueError("Invalid guess. Must be a 5-letter word.")

        feedback = ["⬜"] * 5
        for i, char in enumerate(guess):
            if char == self.target_word[i]:
                feedback[i] = "🟩"
            elif char in self.target_word:
                feedback[i] = "🟨"

        self.guesses.append((guess, "".join(feedback)))
        return feedback

    def is_game_over(self):
        return len(self.guesses) >= self.max_attempts or any(guess == self.target_word for guess, _ in self.guesses)

    def is_winner(self):
        return any(guess == self.target_word for guess, _ in self.guesses)

    def render_game(self):
        game_board = "\n".join([f"{guess}: {feedback}" for guess, feedback in self.guesses])
        return f"```\n{game_board}\n```"


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

        # Load the word list
        self.load_word_list()
        self.ensure_table_exists()

    def load_word_list(self):
        with open('data/wordlist.key', 'rb') as key_file:
            key = key_file.read()
        cipher_suite = Fernet(key)

        with open('data/encrypted_word_list.bin', 'rb') as f:
            encrypted_words = f.read().splitlines()

        self.word_list = [cipher_suite.decrypt(word).decode() for word in encrypted_words]

    def ensure_table_exists(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wordle_games (
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            date TEXT NOT NULL,
            target_word TEXT NOT NULL,
            guesses TEXT,
            PRIMARY KEY (user_id, guild_id, date)
        );
        """)
        conn.commit()
        conn.close()

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="start_wordle", description="Start a new game of Wordle")
        async def start_wordle_command(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            date_str = datetime.utcnow().strftime('%Y-%m-%d')

            # Check if the user has already played today's game
            if self.has_played_today(user_id, guild_id, date_str):
                await interaction.response.send_message("You have already played today's Wordle. Try again tomorrow!", ephemeral=True)
                return

            target_word = random.choice(self.word_list)
            game = WordleGame(user_id, guild_id, target_word)
            self.games[user_id] = game

            # Save the game to the database
            self.save_game(user_id, guild_id, date_str, target_word)

            await interaction.response.send_message(f"New game of Wordle started!\n{game.render_game()}\nMake your guess using /guess_wordle [word]")

        @tree.command(name="guess_wordle", description="Make a guess in your Wordle game")
        async def guess_wordle_command(interaction: discord.Interaction, guess: str):
            user_id = str(interaction.user.id)
            game = self.games.get(user_id)
            if not game:
                await interaction.response.send_message("You don't have an active game. Start one using /start_wordle.", ephemeral=True)
                return

            try:
                feedback = game.make_guess(guess.lower())
                if game.is_game_over():
                    if game.is_winner():
                        await self.bot.profiles.record_win(user_id, str(interaction.guild.id), "wordle")
                        await interaction.response.send_message(f"Congratulations! You guessed the word {game.target_word}!\n{game.render_game()}")
                    else:
                        await self.bot.profiles.record_loss(user_id, str(interaction.guild.id), "wordle")
                        await interaction.response.send_message(f"Game over! The word was {game.target_word}.\n{game.render_game()}")
                    del self.games[user_id]
                else:
                    await interaction.response.send_message(f"{game.render_game()}\nYour guess: {guess}\nFeedback: {''.join(feedback)}")
            except ValueError as e:
                await interaction.response.send_message(str(e), ephemeral=True)

        @tree.command(name="end_wordle", description="End your current game of Wordle")
        async def end_wordle_command(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            if user_id in self.games:
                del self.games[user_id]
                await interaction.response.send_message("Your game has been ended.")
            else:
                await interaction.response.send_message("You don't have an active game to end.", ephemeral=True)

        if not tree.get_command("start_wordle"):
            tree.add_command(start_wordle_command)

        if not tree.get_command("guess_wordle"):
            tree.add_command(guess_wordle_command)

        if not tree.get_command("end_wordle"):
            tree.add_command(end_wordle_command)

    def has_played_today(self, user_id, guild_id, date_str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM wordle_games WHERE user_id = ? AND guild_id = ? AND date = ?", (user_id, guild_id, date_str))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def save_game(self, user_id, guild_id, date_str, target_word):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO wordle_games (user_id, guild_id, date, target_word) VALUES (?, ?, ?, ?)", (user_id, guild_id, date_str, target_word))
        conn.commit()
        conn.close()


def setup(bot):
    wordle = Wordle(bot)
    wordle.setup(bot.tree)
    bot.wordle_module = wordle
