from dotenv import load_dotenv
import os

load_dotenv()

config = {
    'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN'),
    'GUILD_ID': int(os.getenv('DISCORD_GUILD_ID')),
    'DISCORD_CHANNEL_ID': int(os.getenv('DISCORD_CHANNEL_ID')),
    'YOUTUBE_API_KEY': os.getenv('YOUTUBE_API_KEY'),
    'TWITCH_CLIENT_ID': os.getenv('TWITCH_CLIENT_ID'),
    'TWITCH_CLIENT_SECRET': os.getenv('TWITCH_CLIENT_SECRET'),
    'BUNGIE_API_KEY': os.getenv('BUNGIE_API_KEY'),
    'OAUTH_URL': os.getenv('OAUTH_URL'),
    'OAUTH_CLIENT_ID': os.getenv('OAUTH_CLIENT_ID'),
    'modules': {
        'currency': {'enabled': True},
        'xp': {'enabled': True},
        'birthday': {'enabled': True},
        'destiny2': {'enabled': False},
        'music': {'enabled': True},
        'youtube': {'enabled': True},
        'twitch': {'enabled': True},
        'update': {'enabled': True},
        'data_privacy': {'enabled': True},
        'term_privacy': {'enabled': True}
    }
}
