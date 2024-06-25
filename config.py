from dotenv import load_dotenv
import os

load_dotenv()

config = {
    'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN'),
    'GUILD_ID': int(os.getenv('DISCORD_GUILD_ID')),
    'modules': {
        'currency': {
            'enabled': True
        }
    }
}
