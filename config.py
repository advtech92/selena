from dotenv import load_dotenv
import os

load_dotenv()

config = {
    'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN'),
    'GUILD_ID': int(os.getenv('DISCORD_GUILD_ID')),
    'DISCORD_CHANNEL_ID': int(os.getenv('DISCORD_CHANNEL_ID')),
    'BUNGIE_API_KEY': os.getenv('BUNGIE_API_KEY'),
    'OAUTH_URL': os.getenv('OAUTH_URL'),
    'OAUTH_CLIENT_ID': os.getenv('OAUTH_CLIENT_ID'),
    'modules': {
        'currency': {
            'enabled': True
        },
        'xp': {
            'enabled': True
        },
        'birthday': {
            'enabled': True
        },
        'destiny2': {
            'enabled': True
        }
    }
}
