import discord
from discord import app_commands
from plexapi.server import PlexServer
import config


class PlexModule:
    def __init__(self, bot):
        self.bot = bot
        self.plex = PlexServer(config.PLEX_URL, config.PLEX_TOKEN)
        self.add_commands()

    def add_commands(self):
        @app_commands.command(
            name="list_libraries", description="List all Plex libraries"
        )
        async def list_libraries(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                libraries = self.plex.library.sections()
                library_names = [lib.title for lib in libraries]
                await interaction.followup.send(
                    f"Plex Libraries: {', '.join(library_names)}"
                )
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="search_library",
            description="Search for a movie in a library"
        )
        async def search_library(
            interaction: discord.Interaction, library: str, query: str
        ):
            await interaction.response.defer()
            try:
                lib = self.plex.library.section(library)
                results = lib.search(query)
                if not results:
                    await interaction.followup.send(
                        f"No results found for '{query}' in '{library}'"
                    )
                    return

                result_titles = [result.title for result in results]
                await interaction.followup.send(
                    f"Search results in {library}: {', '.join(result_titles)}"
                )
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="play_movie", description="Play a movie on a specified Plex "
            "client"
        )
        async def play_movie(
            interaction: discord.Interaction, client_name: str, movie_name: str
        ):
            await interaction.response.defer()
            try:
                client = next(
                    (c for c in self.plex.clients() if c.title == client_name),
                    None
                )
                if not client:
                    await interaction.followup.send(
                        f"No client found with the name '{client_name}'"
                    )
                    return

                movie = self.plex.library.section('Movies').get(movie_name)
                client.playMedia(movie)
                await interaction.followup.send(
                    f"Playing '{movie_name}' on '{client_name}'"
                )
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        self.bot.tree.add_command(list_libraries)
        self.bot.tree.add_command(search_library)
        self.bot.tree.add_command(play_movie)


async def setup(bot):
    PlexModule(bot)
