import os
import model
import controller
import time, datetime

# TEMPLATE / LAYOUT / STYLING

def user_input(msg=""):
    answer = input(f"{msg}\n> ")
    return answer
    
def get_time_now():
    return datetime.datetime.now().strftime("%H:%M:%S")

def response_message(status, msg):
    switch = {
        "INFO": "\033[34m",
        "STAT": "\033[92m",
        "WARN": "\033[93m",
        "ERR": "\033[91m",
    }

    color = switch.get(status)
    

    print(f"[{get_time_now()}] {color}[{status}]\033[92m {msg}")

# MENU / PAGING ============================================

def main_menu():
    os.system('cls')
    print(f"\033[92m{"+":-<50}+")
    print(f"|{"SNIPER BOT | By: Exodia":^49}|")
    print(f"|{"(Sonic Network)":^49}|")
    print(f"{"+":-<50}+")
    list_menu()
    redirect(f"main.{user_input()}")

def list_menu():
    menu = [
        "Bind Wallet",
        "Check Balance",
        "Monitor New Token",
    ]

    if model.env_get('PUBLIC_KEY'):
        menu[0] = f"Unbind ({model.env_get('PUBLIC_KEY')[:5]}...{model.env_get('PUBLIC_KEY')[-5:]})"
    else:
        menu[0] = "Bind Wallet"

    print(f"\n[0] {menu[0]}\n")
    for i, m in enumerate(menu):
        if i != 0:
            print(f"\033[92m[{i}] {m}")

def redirect(user):
    switch = {
        "main.0": bind_wallet,
        "main.1": check_balance,
        "main.2": monitor_new_token,
    }

    switch.get(user, main_menu)()

def bind_wallet(custom_msg=None):
    if model.env_get('PUBLIC_KEY'):
        model.env_set('PUBLIC_KEY', '')
        main_menu()
    else:
        address = user_input(custom_msg or "Input your Address / Public Key:")
        isEVM = controller.is_evm_address(address)

        if isEVM:
            model.env_set('PUBLIC_KEY', address)
            main_menu()
        else:
            bind_wallet("Please input correct EVM Address:")

def check_balance():
    if controller.init_connection():
        balance, total_price = controller.check_balance(model.env_get('PUBLIC_KEY'))
        response_message("INFO", f"Your balance: {round(balance, 5)} S (~${total_price})")

def monitor_new_token():
    if controller.init_connection():
        controller.monitor_new_token()
    