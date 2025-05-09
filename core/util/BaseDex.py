from core.data.JSONModel import Dex
from core.data.JSONModel import Address
import core.model as model
import core.view as view
from web3 import Web3

class BaseDex:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(model.env_get('RPC')))
        self.DEX = Dex().data
        self.ADDRESS = Address().data

    def get_pair_token(self, token_address):
        pass