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
        self.columns[player][column].insert(0, dice)  # Place at the top of the column
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
        return all(len(col) == 3 for col in self.columns[self.players[0]]) or all(len(col) == 3 for col in self.columns[self.players[1]])

    def winner(self):
        if self.scores[self.players[0]] > self.scores[self.players[1]]:
            return self.players[0]
        elif self.scores[self.players[1]] > self.scores[self.players[0]]:
            return self.players[1]
        else:
            return None  # It's a tie

    def render_board(self):
        board_str = "```\n"
        board_str += f"{self.players[1].display_name}'s Board\n"
        board_str += self.render_player_board(self.players[1], True)
        board_str += "---------\n"  # Separator between boards
        board_str += f"{self.players[0].display_name}'s Board\n"
        board_str += self.render_player_board(self.players[0], False)
        board_str += "```"
        return board_str

    def render_player_board(self, player, is_opponent):
        board_str = ""
        board_str += "  ".join([f"{sum(col)}" for col in self.columns[player]]) + "\n"  # Column totals
        for row in range(3):
            for col in range(3):
                if is_opponent:
                    dice = self.columns[player][col]
                else:
                    dice = list(reversed(self.columns[player][col]))
                if len(dice) > row:
                    board_str += f"| {dice[row]} "
                else:
                    board_str += "|   "
            board_str += "|\n"
        board_str += f"Score: {self.scores[player]}\n"  # Player's total score
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
            initial_message = await thread.send(f"{player1.mention} has started a game of Knucklebones against {player2.mention}!\n{player1.mention}, it's your turn to roll the dice.", view=RollDiceView(self.bot))
            self.games[thread.id].message = initial_message
            await interaction.response.send_message("Game started in a new thread!", ephemeral=True)

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

        if not tree.get_command("check_score"):
            tree.add_command(check_score_command)

    async def update_game_message(self, game, interaction, content, view=None):
        try:
            await game.message.edit(content=content, view=view)
        except discord.NotFound:
            game.message = await interaction.channel.send(content=content, view=view)

    async def play_bot_turn(self, channel, game):
        dice = game.roll_dice()
        column = random.randint(1, 3)
        game.place_dice(self.bot.user, dice, column)
        if game.is_game_over():
            winner = game.winner()
            if winner:
                await self.award_kibble(winner.id, game.bet * 2)
                await self.update_game_message(game, channel, f"{winner.mention} wins the game and {game.bet * 2} Kibble!\n{game.render_board()}")
            else:
                await self.update_game_message(game, channel, f"The game is a tie!\n{game.render_board()}")
            del self.games[channel.id]
        else:
            game.next_turn()
            await self.update_game_message(game, channel, f"{self.bot.user.mention} rolled a {dice} and placed it in column {column}.\nIt's now {game.current_player().mention}'s turn!\n{game.render_board()}", view=RollDiceView(self.bot))

    async def has_enough_kibble(self, user_id, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM guild_currency WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row and row[0] >= amount

    async def deduct_kibble(self, user_id, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE guild_currency SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()

    async def award_kibble(self, user_id, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE guild_currency SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()


class RollDiceView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Roll Dice", style=discord.ButtonStyle.primary)
    async def roll_dice_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.bot.knucklebones_module.games.get(interaction.channel_id)
        if not game:
            await interaction.response.send_message("There is no game in progress in this thread.", ephemeral=True)
            return
        if interaction.user != game.current_player():
            await interaction.response.send_message("It's not your turn.", ephemeral=True)
            return
        dice = game.roll_dice()
        await interaction.response.edit_message(content=f"{interaction.user.mention} rolled a {dice}! Choose a column to place it in.\n{game.render_board()}", view=PlaceDiceView(self.bot, dice))


class PlaceDiceView(discord.ui.View):
    def __init__(self, bot, dice):
        super().__init__(timeout=None)
        self.bot = bot
        self.dice = dice

    @discord.ui.button(label="Column 1", style=discord.ButtonStyle.secondary)
    async def column_1_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.place_dice(interaction, 1)

    @discord.ui.button(label="Column 2", style=discord.ButtonStyle.secondary)
    async def column_2_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.place_dice(interaction, 2)

    @discord.ui.button(label="Column 3", style=discord.ButtonStyle.secondary)
    async def column_3_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.place_dice(interaction, 3)

    async def place_dice(self, interaction, column):
        game = self.bot.knucklebones_module.games.get(interaction.channel_id)
        if not game:
            await interaction.response.send_message("There is no game in progress in this thread.", ephemeral=True)
            return
        if interaction.user != game.current_player():
            await interaction.response.send_message("It's not your turn.", ephemeral=True)
            return
        game.place_dice(interaction.user, self.dice, column)
        if game.is_game_over():
            winner = game.winner()
            if winner:
                await self.bot.knucklebones_module.award_kibble(winner.id, game.bet * 2)
                await self.bot.knucklebones_module.update_game_message(game, interaction, f"{winner.mention} wins the game and {game.bet * 2} Kibble!\n{game.render_board()}")
            else:
                await self.bot.knucklebones_module.update_game_message(game, interaction, f"The game is a tie!\n{game.render_board()}")
            del self.bot.knucklebones_module.games[interaction.channel_id]
        else:
            game.next_turn()
            await self.bot.knucklebones_module.update_game_message(game, interaction, f"{interaction.user.mention} placed {self.dice} in column {column}.\nIt's now {game.current_player().mention}'s turn!\n{game.render_board()}", view=RollDiceView(self.bot))
            if game.current_player() == self.bot.user:
                await self.bot.knucklebones_module.play_bot_turn(interaction.channel, game)
            else:
                await interaction.channel.send(f"{game.current_player().mention}, it's your turn to roll the dice.", view=RollDiceView(self.bot))


def setup(bot):
    knucklebones = Knucklebones(bot)
    knucklebones.setup(bot.tree)
    bot.knucklebones_module = knucklebones
