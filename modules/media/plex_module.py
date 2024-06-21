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
            name="list_clients", description="List all available Plex clients"
        )
        async def list_clients(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                clients = self.plex.clients()
                if not clients:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="Plex Clients",
                            description="No clients found",
                            color=discord.Color.red()
                        )
                    )
                    return

                client_info = "\n".join(
                    [f"{client.title} (ID: {client.machineIdentifier})" for client in clients]  # noqa: E501
                )
                embed = discord.Embed(
                    title="Plex Clients",
                    description=client_info,
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="list_libraries", description="List all Plex libraries"
        )
        async def list_libraries(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                libraries = self.plex.library.sections()
                library_names = [lib.title for lib in libraries]
                embed = discord.Embed(
                    title="Plex Libraries",
                    description=", ".join(library_names),
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="search_library",
            description="Search for a movie or TV show in a library"
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
                        embed=discord.Embed(
                            title="Search Library",
                            description=f"No results found for '{query}' in '{library}'",  # noqa: E501
                            color=discord.Color.red()
                        )
                    )
                    return

                result_titles = [result.title for result in results]
                embed = discord.Embed(
                    title=f"Search results in {library}",
                    description=", ".join(result_titles),
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="play_movie",
            description="Play a movie on a specified Plex client"
        )
        async def play_movie(
            interaction: discord.Interaction, movie_name: str,
            client_name: str = None
        ):
            await interaction.response.defer()
            try:
                client = next(
                    (c for c in self.plex.clients() if c.title == client_name),
                    self.plex.clients()[0] if self.plex.clients() else None
                )
                if not client:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="Play Movie",
                            description="No clients available to play the movie",  # noqa: E501
                            color=discord.Color.red()
                        )
                    )
                    return

                movie = self.plex.library.section('Movies').get(movie_name)
                client.playMedia(movie)
                embed = discord.Embed(
                    title="Playing Movie",
                    description=f"Playing '{movie_name}' on '{client.title}'",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        @app_commands.command(
            name="play_tv_show",
            description="Play a TV show on a specified Plex client"
        )
        async def play_tv_show(
            interaction: discord.Interaction, library: str, show_name: str,
            season: int, episode: int, client_name: str = None
        ):
            await interaction.response.defer()
            try:
                client = next(
                    (c for c in self.plex.clients() if c.title == client_name),
                    self.plex.clients()[0] if self.plex.clients() else None
                )
                if not client:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="Play TV Show",
                            description="No clients available to play the TV show",  # noqa: E501
                            color=discord.Color.red()
                        )
                    )
                    return

                show = self.plex.library.section(library).get(show_name)
                episode = show.season(season).episode(episode)
                client.playMedia(episode)
                embed = discord.Embed(
                    title="Playing TV Show",
                    description=f"Playing '{show_name}' S{season}E{episode} on '{client.title}'",  # noqa: E501
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")

        self.bot.tree.add_command(list_clients)
        self.bot.tree.add_command(list_libraries)
        self.bot.tree.add_command(search_library)
        self.bot.tree.add_command(play_movie)
        self.bot.tree.add_command(play_tv_show)


async def setup(bot):
    PlexModule(bot)
