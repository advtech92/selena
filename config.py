from dotenv import load_dotenv
import os

load_dotenv()

config = {
    'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN'),
    'GUILD_ID_1': int(os.getenv('DISCORD_GUILD_ID')),
    'GUILD_ID_2': int(os.getenv('DISCORD_GUILD_ID_2')),
    'DISCORD_CHANNEL_ID': int(os.getenv('DISCORD_CHANNEL_ID')),
    'YOUTUBE_API_KEY': os.getenv('YOUTUBE_API_KEY'),
    'TWITCH_CLIENT_ID': os.getenv('TWITCH_CLIENT_ID'),
    'TWITCH_CLIENT_SECRET': os.getenv('TWITCH_CLIENT_SECRET'),
    'BUNGIE_API_KEY': os.getenv('BUNGIE_API_KEY'),
    'OAUTH_URL': os.getenv('OAUTH_URL'),
    'OAUTH_CLIENT_ID': os.getenv('OAUTH_CLIENT_ID'),
    'modules': {
        'music': {'enabled': True},
        'terms_privacy': {'enabled': True},
        'data_privacy': {'enabled': True}
    }
}
