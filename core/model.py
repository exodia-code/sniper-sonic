from eth_account import Account
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

    try:
        dotenv.set_key(env_path, key, value)
        refresh()
    except Exception as e:
        return False

    return True

def env_get(key, default=None):
    return os.getenv(key, default)

def connect_wallet(pk):
    try:
        env_set('PRIVATE_KEY', pk)
        env_set('PUBLIC_KEY', Account.from_key(pk).address)
    except Exception:
        return False
    return True

def disconnect_wallet():
    env_set('PRIVATE_KEY', '')
    env_set('PUBLIC_KEY', '')

    return True

def wallet_is_connected():
    if env_get('PRIVATE_KEY'):
        return Account.from_key(env_get("PRIVATE_KEY")).address, True
    else:
        return None, False

def bind_wallet(address):
    return env_set('PUBLIC_KEY', address)

def unbind_wallet():
    return env_set('PUBLIC_KEY', '')

def wallet_has_bound():
    if env_get('PUBLIC_KEY'):
        return True
    else:
        return False

def get_public_key():
    return env_get('PUBLIC_KEY')
