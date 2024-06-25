from dotenv import load_dotenv
import os

load_dotenv()

config = {
    'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN'),
    'GUILD_ID': int(os.getenv('DISCORD_GUILD_ID')),
    'DISCORD_CHANNEL_ID': int(os.getenv('DISCORD_CHANNEL_ID')),
    'TWITCH_CLIENT_ID': os.getenv('TWITCH_CLIENT_ID'),
    'TWITCH_CLIENT_SECRET': os.getenv('TWITCH_CLIENT_SECRET'),
    'modules': {
        'currency': {
            'enabled': True
        },
        'xp': {
            'enabled': True
        },
        'twitch': {
            'enabled': True
        }
    }
}
