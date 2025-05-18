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

def scan_fastest_rpc():
    rpcs = [
        {
            "url": "https://rpc.soniclabs.com"
        },
        {
            "url": "https://sonic-rpc.publicnode.com"
        }
    ]

    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": ["latest", False],
        "id": 1
    }

    fastest_rpc = model.env_get('RPC')
    fastest_latency = -1

    for k, url in enumerate(rpcs):
        start = time.time()
        try:
            reponse = requests.post(url['url'], json=payload, timeout=5)
            latency = (time.time() - start) * 1000 # ms2

            if k == 0:
                fastest_rpc = url['url']
                fastest_latency = latency
            else:
                if fastest_latency < latency or fastest_latency == -1:
                    fastest_rpc = url['url']
                    fastest_latency = latency
        except Exception as e:
            print(f"{url['url']} - Failed: {e}")

    model.env_set("RPC", fastest_rpc)
    RPC = model.env_get('RPC')
    w3 = Web3(Web3.HTTPProvider(RPC))

    return fastest_rpc, fastest_latency

def check_connection():
    result = False

    rpc, latency = view.loading_thread(view.spinner_loading, "Checking fastest RPC", scan_fastest_rpc)
    view.response_message("WARN", f"Fastest RPC: {rpc} [{latency:.2f} ms]")

    if w3.is_connected():
        view.response_message("INFO", f"Connected to {rpc}.")
        result = True
    else:
        view.response_message("WARN", f"Failed to connect. Please check your internet connection and RPC Address [{RPC}]")

    return result

def check_balance(address):
    balance_wei = w3.eth.get_balance(address)

    balance_sonic = w3.from_wei(balance_wei, 'ether')
    price = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=sonic-3&vs_currencies=usd").json()['sonic-3']['usd']
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

def get_pair(token_address, paired):
    token0 = w3.to_checksum_address(token_address)
    token1 = w3.to_checksum_address(ADDRESS.token.wS.address) if paired == '' else w3.to_checksum_address(paired)

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

                user = view.user_input("Do you want to Get Price? [Y/n]", "Y")
                get_reserves(dex, data) if user == "Y" else view.main_menu()
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

            for block_num in range(latest_checked + 1, latest_block):
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

def buy_token(token_address):
    wS = w3.to_checksum_address(ADDRESS.token.wS.address)
    token = w3.to_checksum_address(token_address)

    token_data = Shadow().get_token(token)

    view.response_message("INFO", f"Token Detected: {token_data['name']} ({token_data['symbol']})")
    confirm = view.user_input(f"Are you sure to Buy {token_data['name']} ({token_data['symbol']})? [Y/n]", "Y")
    if confirm == "Y":
        buy_amount = view.user_input(f"Set your amount:")
        if float(buy_amount) > 0:
            view.response_message("INFO", f"Buy: {buy_amount} wS = 23 {token_data['name']} ({token_data['symbol']})")

    # return
    user = {
        "private": model.env_get("PRIVATE_KEY"),
        "public": model.env_get("PUBLIC_KEY")
    }

    path = [(wS, token, False)]

    router = w3.eth.contract(address=DEX.shadow.config.router.address, abi=DEX.shadow.config.router.abi.swapExactETHForTokens)

    # Infinity (8) CA: 0x888852d1c63c7b333efEb1c4C5C79E36ce918888

    amount_in_wei = w3.to_wei(buy_amount, 'ether')  # swap 1 wS
    # try:
    amounts = router.functions.getAmountsOut(amount_in_wei, path).call()

    amount_out_min = int(amounts[-1] * 0.95)  # slippage 5%

    tx = router.functions.swapExactETHForTokens(
        amount_out_min,
        path,
        user['public'],
        int(time.time()) + 60 * 3
    ).build_transaction({
        "from": user['public'],
        "value": amount_in_wei,
        "gasPrice": w3.to_wei("70", "gwei"),
        "nonce": w3.eth.get_transaction_count(user['public'])
    })

    signed_tx = w3.eth.account.sign_transaction(tx, user['private'])
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    print(f"TX sent: {w3.to_hex(tx_hash)}")


def sell_token(token_address):

    wS = w3.to_checksum_address(ADDRESS.token.wS.address)
    token = w3.to_checksum_address(token_address)

    token_data = Shadow().get_token(token)

    abi = [
        {
            "inputs":[
                {
                    "internalType":"address",
                    "name":"account",
                    "type":"address"
                }
            ],
            "name":"balanceOf",
            "outputs":[
                {
                    "internalType":"uint256",
                    "name":"",
                    "type":"uint256"
                }
            ],
            "stateMutability":"view",
            "type":"function"
        },
        {
            "constant": False,
            "inputs": [
                {
                    "name": "spender",
                    "type": "address"},
                {
                    "name": "amount",
                    "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [
                {
                    "name": "",
                    "type": "bool"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [
                {
                    "name": "owner",
                    "type": "address"
                },
                {
                    "name": "spender",
                    "type": "address"
                }
            ],
            "name": "allowance",
            "outputs": [
                {
                    "name": "",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]

    contract = w3.eth.contract(address=token, abi=abi)
    balance = contract.functions.balanceOf(model.get_public_key()).call() / 10**token_data['decimals']



    view.response_message("INFO", f"Token Balance: {balance} {token_data['name']} ({token_data['symbol']})")
    if balance == 0:
        view.response_message("ERRO", f"Balance is 0 can't sell.")
        view.main_menu(False)

    while True:
        # amount = view.user_input(f"Set amount to sell [max/half/custom|%]:")
        amount = "max"
        if isinstance(amount, (int, float)):
            if amount > balance:
                view.response_message("ERRO", f"Out of balance {token_data['name']} ({token_data['symbol']})!")
                view.main_menu(False)
                break
            else:
                amount = float(amount)
                break
        elif isinstance(amount, str):
            if amount == "max":
                amount = balance
                break
            elif amount == "half":
                amount = balance / 2
                break
            elif "%" in amount:
                amount = balance * float(amount.replace("%", "").strip()) / 100
                break
            else:
                view.response_message("ERRO", "Invalid input!")
                continue
    
    # amount = int(amount)
    print(f"Sell: {amount} {token_data['name']} ({token_data['symbol']})")

    amount_wei = int(amount * (10 ** token_data['decimals']))

    # wallet_address = model.get_public_key()
    user = {
        "private": model.env_get("PRIVATE_KEY"),
        "public": model.env_get("PUBLIC_KEY")
    }

    view.response_message("STAT", "Waiting Approval status.")

    # approval
    approve_tx = contract.functions.approve(
        DEX.shadow.config.router.address,
        amount_wei
    ).build_transaction({
        "from": user['public'],
        "nonce": w3.eth.get_transaction_count(user['public']),
        "gasPrice": w3.to_wei("70", "gwei"),
    })

    signed_approve = w3.eth.account.sign_transaction(approve_tx, model.env_get("PRIVATE_KEY"))
    approve_tx_hash = w3.eth.send_raw_transaction(signed_approve.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(approve_tx_hash)

    while True:
        time.sleep(1)
        if receipt["status"] == 1:
            view.response_message("WARN", "Approved token to Router.")
            break
            
    allowance = contract.functions.allowance(user['public'], DEX.shadow.config.router.address).call()
    print(f"Allowance: {allowance} - {amount_wei}")

    router = w3.eth.contract(address=DEX.shadow.config.router.address, abi=DEX.shadow.config.router.abi.swapExactTokensForTokens)
    path = [
        {
            "from": token,
            "to": wS,
            "stable": False
        }
    ]
    amount_out_min = int(router.functions.getAmountsOut(amount_wei, path).call()[-1] * 0.9)

    view.response_message("INFO", f"Building TX.")
    view.response_message("INFO", f"Amounts Out Minimum: {amount_out_min}")
    # view.response_message("INFO", f"Path: {token} -> {wS} | False")

    try:
        tx = router.functions.swapExactTokensForTokens(
            amount_wei,
            amount_out_min,
            path,
            user['public'],
            int(time.time()) + 60 * 10
        ).build_transaction({
            "from": user['public'],
            "nonce": w3.eth.get_transaction_count(user['public']),
            "gasPrice": w3.to_wei("55", "gwei"),
            "gas": 500000
        })

        signed_tx = w3.eth.account.sign_transaction(tx, user['private'])
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"TX Hash: {tx_hash.hex()}")
    except Exception as e:
        view.response_message("ERRO", f"Error: {e}")

    # view.response_message("STAT", f"Try to estimating gas.")

    # try:
    #     estimated_gas = w3.eth.estimate_gas(tx)
    #     view.response_message("WARN", f"Estimated Gas: {estimated_gas}")
    #     # tx["gas"] = int(estimated_gas * 1.2)
    # except Exception as e:
    #     print("Estimate gas failed:", e)
    #     return

    # Infinity (8) CA: 0x888852d1c63c7b333efEb1c4C5C79E36ce918888
    # EGGS CA: 0xf26Ff70573ddc8a90Bd7865AF8d7d70B8Ff019bC

