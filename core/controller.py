from web3 import Web3
from web3.exceptions import BadFunctionCallOutput
from eth_account import Account

import re, time
import requests
import core.model as model
import core.view as view
from core.data.JSONModel import Dex, Address
from core.util.dex.Shadow import Shadow
from core.util.dex.Metropolis import Metropolis

RPC = model.env_get('RPC')
w3 = Web3(Web3.HTTPProvider(RPC))
DEX = Dex().data
ADDRESS = Address().data

def is_evm_address(address):
    # Cek Format Basic
    if not isinstance(address, str):
        return False
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False

    # cek setelah 0x is_hexadecimal?
    hex_part = address[2:]
    match = re.fullmatch(r'[0-9a-fA-F]{40}', hex_part)
    return bool(match)

def is_valid_private_key(pk):
    try:
        # hapus "0x" jika ada
        if pk.startswith("0x"):
            pk = pk[2:]
        
        if len(pk) != 64:
            return False

        # konversi ke Account
        account = Account.from_key(pk)
        return True

    except Exception:
        return False

def check_connection():
    result = False
    view.response_message("STAT", f"Checking connection to [{RPC}].")

    if w3.is_connected():
        view.response_message("INFO", f"Connected to {RPC}.")
        result = True
    else:
        view.response_message("WARN", f"Failed to connect. Please check your internet connection and RPC Address [{RPC}]")

    return result

def check_balance(address):
    balance_wei = w3.eth.get_balance(address)

    balance_sonic = w3.from_wei(balance_wei, 'ether')
    price = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=sonic&vs_currencies=usd").json()['sonic']['usd']
    total_price = round(price * float(balance_sonic), 2)

    return balance_sonic, total_price

def init_connection(bind_wallet=False, connect_wallet=False):
    result = False
    if model.wallet_has_bound() and bind_wallet:
        result = True

    if check_connection():
        result = True

    return result

def get_reserves(dex, pair_address):
    switch = {
        "shadow": Shadow().get_reserves,
        "metropolis": Metropolis().get_reserves
    }   

    reserve0, reserve1 = switch.get(dex.slug)(dex.config.pairContract, pair_address)

def get_pair(token_address):
    token0 = w3.to_checksum_address(token_address)
    token1 = w3.to_checksum_address(ADDRESS.token.wS.address)

    for k, dex in DEX.items():
        for version, factory in dex.config.factories.items():
            view.response_message('STAT', f"Checking in {dex.name} ({version})")

            switch = {
                "shadow": Shadow().get_pair_token,
                "metropolis": Metropolis().get_pair_token
            }   

            result, data = switch.get(k)(factory, token0, token1)

            if result:
                view.response_message("INFO", f"Pair Found in {dex.name} ({version}).")
                view.response_message("INFO", f"Pair Address: {data}")
                get_reserves(dex, data)
            else:
                view.response_message("ERRO", f"Value Error : [{data}]\n")

def token_source_status(address):
    api_key = model.env_get('SONICSCAN_API_KEY')

    url = f"https://api.sonicscan.org/api?module=contract&action=getsourcecode&address={address}&apikey={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()['result'][0]

        if data['SourceCode'] != "" and data['ABI'] != "Contract source code not verified":
            view.response_message('INFO', f"Contract source code verified!")
            get_pair(address)
        else:
            view.response_message("ERRO", "Contract source code not verified!")
    else:
        view.response_message("ERRO", f"Error: {response.status_code}")

def scan_new_token():
    latest_checked = w3.eth.block_number
    # latest_checked = 379085

    while True:
        latest_block = w3.eth.block_number
        # latest_block = 379100

        if latest_block > latest_checked:
            view.response_message("STAT", f"Checking block {latest_checked + 1} ~ {latest_block}")

            for block_num in range(latest_checked + 1, latest_block + 1):
                block = w3.eth.get_block(block_num, full_transactions=True)

                for tx in block.transactions:
                    if tx.to is None: # cek apakah Contract_Creation
                        receipt = w3.eth.get_transaction_receipt(tx.hash)
                        contract_address = receipt.contractAddress
                        if contract_address:
                            view.response_message("INFO", f"New Contract has been Found! CA: {contract_address}")

                            erc20_abi = [
                                {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                            ]

                            try:
                                token_contract = w3.eth.contract(address=contract_address, abi=erc20_abi)
                                name = token_contract.functions.name().call()
                                symbol = token_contract.functions.symbol().call()
                                decimals = token_contract.functions.decimals().call()
                                supply = token_contract.functions.totalSupply().call() / (10 ** decimals)

                                metadata = True

                            except Exception as e:
                                view.response_message("WARN", f"Can't get metadata of {contract_address[:5]}...{contract_address[-5:]}: {str(e)}")
                                metadata = False

                            view.response_message("INFO", f"Continue checking in block {latest_block}...")
            latest_checked = latest_block

        if 'metadata' in locals() and metadata:
            view.response_message("INFO", f"Token: {name} ({symbol}), Supply: {supply}")
            token_source_status(contract_address)



    # 12085540 ~ 12085550 ~ 12085560 | Shadow (OIL)
    # 379085 ~ 379091 ~ 379100 | Metropolis (GOGLZ)


            
