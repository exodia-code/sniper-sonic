from web3 import Web3
from web3.exceptions import BadFunctionCallOutput

import re, time
import requests
import model, view

RPC = model.env_get('RPC')
w3 = Web3(Web3.HTTPProvider(RPC))

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

def wallet_has_bound():
    if model.env_get('PUBLIC_KEY'):
        return True
    else:
        view.bind_wallet("Your Wallet is not bound, bind first!")

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

    if wallet_has_bound() and bind_wallet:
        result = True

    if check_connection():
        result = True

    return result


def token_source_status(address):
    api_key = model.env_get('SONICSCAN_API_KEY')

    url = f"https://api.sonicscan.org/api?module=contract&action=getsourcecode&address={address}&apikey={api_key}"
    # url = f"https://api.sonicscan.org/api?module=contract&getsourcecode&address={address}&api_key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        view.response_message("ERR", f"Error: {response.status_code}")

def monitor_new_token():
    latest_checked = w3.eth.block_number
    # latest_checked = 23321523

    while True:
        latest_block = w3.eth.block_number
        # latest_block = 23321574

        if latest_block > latest_checked:
            view.response_message("STAT", f"Checking block {latest_checked + 1} ~ {latest_block}")

            for block_num in range(latest_checked + 1, latest_block + 1):
                block = w3.eth.get_block(block_num, full_transactions=True)

                for tx in block.transactions:
                    if tx.to is None: # cek apakah Contract_Creation
                        receipt = w3.eth.get_transaction_receipt(tx.hash)
                        contract_address = receipt.contractAddress
                        if contract_address:
                            view.response_message("INFO", f"Token atau kontrak baru ditemukan! CA: {contract_address}")

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

                                view.response_message("INFO", f"Token: {name} ({symbol}), Supply: {supply}")
                                token_source_status(contract_address)

                            except Exception as e:
                                view.response_message("WARN", f"Can't get metadata of {contract_address[:5]}...{contract_address[-5:]}: {str(e)}")

                            view.response_message("INFO", f"Continue checking...")

            latest_checked = latest_block


    # 23321523 ~ 23321574


            
