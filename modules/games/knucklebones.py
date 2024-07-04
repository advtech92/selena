import discord
from discord import app_commands
import random
import logging
import sqlite3


class KnucklebonesGame:
    def __init__(self, player1, player2, bet=0):
        self.players = [player1, player2]
        self.turn = 0
        self.columns = {player1: [[], [], []], player2: [[], [], []]}
        self.scores = {player1: 0, player2: 0}
        self.bet = bet
        self.current_dice = None

    def roll_dice(self):
        self.current_dice = random.randint(1, 6)
        return self.current_dice

    def place_dice(self, player, dice, column):
        column -= 1  # Adjust for 1-based index
        self.columns[player][column].insert(0, dice)
        self.clear_matching_dice(player, dice, column)
        self.calculate_score(player)

    def clear_matching_dice(self, player, dice, column):
        opponent = self.other_player()
        opponent_column = self.columns[opponent][column]
        self.columns[opponent][column] = [d for d in opponent_column if d != dice]

    def calculate_score(self, player):
        total_score = 0
        for column in self.columns[player]:
            if column:
                column_score = sum(column) * len(column)
                total_score += column_score
        self.scores[player] = total_score

    def next_turn(self):
        self.turn = (self.turn + 1) % 2

    def current_player(self):
        return self.players[self.turn]

    def other_player(self):
        return self.players[(self.turn + 1) % 2]

    def is_game_over(self):
        return all(len(col) >= 3 for cols in self.columns.values() for col in cols)

    def winner(self):
        if self.scores[self.players[0]] > self.scores[self.players[1]]:
            return self.players[0]
        elif self.scores[self.players[1]] > self.scores[self.players[0]]:
            return self.players[1]
        else:
            return None  # It's a tie

    def render_board(self):
        board_str = "```\n"
        board_str += f"{self.other_player().display_name}'s Board\n"
        board_str += self.render_player_board(self.other_player(), True)
        board_str += "\n\n"
        board_str += f"{self.current_player().display_name}'s Board\n"
        board_str += self.render_player_board(self.current_player(), False)
        board_str += "```"
        return board_str

    def render_player_board(self, player, is_opponent):
        board_str = ""
        for col in self.columns[player]:
            if is_opponent:
                col_str = " | ".join(str(dice) for dice in col)
                board_str += f"| {col_str:^5} |\n"
            else:
                col_str = " | ".join(str(dice) for dice in col)
                board_str = f"| {col_str:^5} |\n" + board_str
        return board_str


class Knucklebones:
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.logger = logging.getLogger('Knucklebones')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='log/selena.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
        self.logger.addHandler(handler)
        self.db_path = 'data/selena.db'

    def setup(self, tree: app_commands.CommandTree):
        @tree.command(name="start_knucklebones", description="Start a game of Knucklebones")
        async def start_knucklebones_command(interaction: discord.Interaction, opponent: discord.User = None, bet: int = 0):
            player1 = interaction.user
            player2 = opponent or self.bot.user
            if player1 == player2:
                await interaction.response.send_message("You cannot play against yourself!", ephemeral=True)
                return
            if bet > 0 and not await self.has_enough_kibble(player1.id, bet):
                await interaction.response.send_message("You do not have enough Kibble to place this bet.", ephemeral=True)
                return
            game = KnucklebonesGame(player1, player2, bet)
            thread = await interaction.channel.create_thread(name=f"Knucklebones: {player1.display_name} vs {player2.display_name}", type=discord.ChannelType.public_thread)
            self.games[thread.id] = game
            if bet > 0:
                await self.deduct_kibble(player1.id, bet)
                if player2 != self.bot.user:
                    await self.deduct_kibble(player2.id, bet)
            await thread.send(f"{player1.mention} has started a game of Knucklebones against {player2.mention}!\n{player1.mention}, it's your turn to roll the dice with `/roll_dice`.\n{game.render_board()}")

        @tree.command(name="roll_dice", description="Roll dice for your turn in Knucklebones")
        async def roll_dice_command(interaction: discord.Interaction):
            game = self.games.get(interaction.channel_id)
            if not game:
                await interaction.response.send_message("There is no game in progress in this thread.", ephemeral=True)
                return
            if interaction.user != game.current_player():
                await interaction.response.send_message("It's not your turn.", ephemeral=True)
                return
            dice = game.roll_dice()
            await interaction.response.send_message(f"{interaction.user.mention} rolled a {dice}! Use `/place_dice` to place it in a column.\n{game.render_board()}")

        @tree.command(name="place_dice", description="Place your rolled dice in a column")
        async def place_dice_command(interaction: discord.Interaction, column: int):
            game = self.games.get(interaction.channel_id)
            if not game:
                await interaction.response.send_message("There is no game in progress in this thread.", ephemeral=True)
                return
            if interaction.user != game.current_player():
                await interaction.response.send_message("It's not your turn.", ephemeral=True)
                return
            if column < 1 or column > 3:
                await interaction.response.send_message("Invalid column. Choose a column between 1 and 3.", ephemeral=True)
                return
            game.place_dice(interaction.user, game.current_dice, column)
            if game.is_game_over():
                winner = game.winner()
                if winner:
                    await self.award_kibble(winner.id, game.bet * 2)
                    await interaction.channel.send(f"{winner.mention} wins the game and {game.bet * 2} Kibble!\n{game.render_board()}")
                else:
                    await interaction.channel.send(f"The game is a tie!\n{game.render_board()}")
                del self.games[interaction.channel_id]
            else:
                game.next_turn()
                await interaction.response.send_message(f"{interaction.user.mention} placed the dice in column {column}.\nIt's now {game.current_player().mention}'s turn!\n{game.render_board()}")
                if game.current_player() == self.bot.user:
                    await self.play_bot_turn(interaction.channel, game)

        @tree.command(name="check_score", description="Check the current score in Knucklebones")
        async def check_score_command(interaction: discord.Interaction):
            game = self.games.get(interaction.channel_id)
            if not game:
                await interaction.response.send_message("There is no game in progress in this thread.", ephemeral=True)
                return
            scores = [f"{player.mention}: {score}" for player, score in game.scores.items()]
            await interaction.response.send_message("Current scores:\n" + "\n".join(scores))

        if not tree.get_command("start_knucklebones"):
            tree.add_command(start_knucklebones_command)

        if not tree.get_command("roll_dice"):
            tree.add_command(roll_dice_command)

        if not tree.get_command("place_dice"):
            tree.add_command(place_dice_command)

        if not tree.get_command("check_score"):
            tree.add_command(check_score_command)

    async def play_bot_turn(self, channel, game):
        dice = game.roll_dice()
        column = random.randint(1, 3)
        game.place_dice(self.bot.user, dice, column)
        if game.is_game_over():
            winner = game.winner()
            if winner:
                await self.award_kibble(winner.id, game.bet * 2)
                await channel.send(f"{winner.mention} wins the game and {game.bet * 2} Kibble!\n{game.render_board()}")
            else:
                await channel.send(f"The game is a tie!\n{game.render_board()}")
            del self.games[channel.id]
        else:
            game.next_turn()
            await channel.send(f"{self.bot.user.mention} rolled a {dice} and placed it in column {column}.\nIt's now {game.current_player().mention}'s turn!\n{game.render_board()}")

    async def has_enough_kibble(self, user_id, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT kibble FROM currency WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row and row[0] >= amount

    async def deduct_kibble(self, user_id, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE currency SET kibble = kibble - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()

    async def award_kibble(self, user_id, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE currency SET kibble = kibble + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()


def setup(bot):
    knucklebones = Knucklebones(bot)
    knucklebones.setup(bot.tree)
    bot.knucklebones_module = knucklebones
