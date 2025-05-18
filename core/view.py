from eth_account import Account
import os, sys, time, datetime, threading
import core.model as model
import core.controller as controller

# TEMPLATE / LAYOUT / STYLING

def user_input(msg="", default=None):
    answer = input(f"{msg}\n> ")
    if answer == "" and default:
        return default
    return answer
    
def get_time_now():
    return datetime.datetime.now().strftime("%H:%M:%S")

def response_message(status, msg):
    switch = {
        "INFO": "\033[34m", # Biru
        "STAT": "\033[92m", # Hijau
        "WARN": "\033[93m", # Kuning
        "ERRO": "\033[91m", # Merah
    }

    color = switch.get(status)
    
    print(f"[{get_time_now()}] {color}[{status}] {msg}\033[92m")

def hidden_address(addr):
    return f"{addr[:5]}...{addr[-5:]}"

def spinner_loading(stop_event, title):
    spinner = ["|", "/", "-", "\\"]
    idx = 0
    while not stop_event.is_set():
        print(f"\r{title} {spinner[idx % len(spinner)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    print("")

def loading_thread(target_task, title, background_task):
    stop_event = threading.Event()

    thread_event = threading.Thread(target=target_task, args=(stop_event, title,))
    thread_event.start()

    result = background_task()

    stop_event.set()
    thread_event.join()

    return result


# MENU / PAGING ============================================
def main_menu(cls=True, isFromMain=False):
    if isFromMain:
        rpc, latency = loading_thread(spinner_loading, "Checking fastest RPC", controller.scan_fastest_rpc)

    if cls:
        os.system('cls')
    print(f"\033[92m{"+":-<70}+")
    print(f"|{"SNIPER BOT | By: Exodia":^69}|")
    print(f"|{"(Sonic Mainnet)":^69}|")
    print(f"|{f'rpc: {rpc} [{latency:.2f} ms]':^69}|") if isFromMain else None
    print(f"{"+":-<70}+")
    list_menu()
    redirect(f"main.{user_input()}")

def list_menu():
    menu = [
        "Connect Wallet",
        "Bind Wallet (only use Public Key)",
        "Check Balance",
        "Scan new token",
        "Get Pair",
        "Buy Token",
        "Sell Token",
    ]

    address, is_connected = model.wallet_is_connected()
    if is_connected:
        menu[0] = f"\033[34mDisconnect [Wallet Connected ({hidden_address(address)})]\033[92m"
    else:
        menu[0] = "Connect Wallet"

    if model.wallet_has_bound():
        menu[1] = f"\033[34mUnbind ({hidden_address(model.get_public_key())})\033[92m"
    else:
        menu[1] = "Bind Wallet (only use Public Key)"

    print(f"\n{"":>1}[0] {menu[0]}\n")
    for i, m in enumerate(menu):
        if i != 0:
            print(f"\033[92m{"":>1}[{i}] {m}")
    print(f"\n[99] Exit")

def redirect(user):
    switch = {
        "main.0": connect_wallet,
        "main.1": bind_wallet,
        "main.2": check_balance,
        "main.3": scan_new_token,
        "main.4": get_pair,
        "main.5": buy_token,
        "main.6": sell_token,
        "main.99": exit,
    }

    switch.get(user, main_menu)()

def bind_wallet(custom_msg=None):
    if model.wallet_has_bound():
        model.unbind_wallet()
        main_menu()
    else:
        address = user_input(custom_msg or "Input your Address / Public Key:")

        if controller.is_evm_address(address):
            model.bind_wallet(address)
            main_menu()
        else:
            bind_wallet("Please input correct EVM Address:")

def connect_wallet(custom_msg=None):
    address, connected = model.wallet_is_connected()
    if connected:
        model.disconnect_wallet()
        main_menu()
    else:
        pk = user_input(custom_msg or "Input your \033[91mPrivate Key:\033[92m")

        if controller.is_valid_private_key(pk):
            model.connect_wallet(pk[2:])
            main_menu()
        else:
            connect_wallet("Please input correct \033[91mPrivate Key:\033[92m")

def check_balance():
    if controller.init_connection():
        balance, total_price = controller.check_balance(model.get_public_key())
        response_message("INFO", f"Your balance: {round(balance, 5)} S (~${total_price})")
        main_menu(False)

def scan_new_token():
    if controller.init_connection():
        controller.scan_new_token()

def get_pair():
    token_address = user_input("Input token address:")
    paired = user_input("Pair with? [Default: Wrapped Sonic (wS)]")
    controller.get_pair(token_address, paired)
    
def buy_token():
    token_address = user_input("Input token address:")
    controller.buy_token(token_address)
    
def sell_token():
    # token_address = user_input("Input token address:")
    token_address = "0x888852d1c63c7b333efEb1c4C5C79E36ce918888"
    controller.sell_token(token_address)