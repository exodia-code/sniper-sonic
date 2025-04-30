import dotenv
import os

dotenv.load_dotenv()

env_path = '.env'

def refresh():
    dotenv.load_dotenv(override=True)

    public_key = env_get('PUBLIC_KEY')

def env_set(key, value):
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            pass

    dotenv.set_key(env_path, key, value)
    refresh()

def env_get(key, default=None):
    return os.getenv(key, default)

public_key = env_get('PUBLIC_KEY')
