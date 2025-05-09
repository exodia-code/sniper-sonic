from core.util.BaseDex import BaseDex
import core.view as view

class Metropolis(BaseDex):
    def __init__(self):
        super().__init__()

    def get_token(self, token_address):
        contract = self.w3.eth.contract(address=token_address, abi=self.DEX.shadow.config.getTokenContract.abi)

        data = {
            "name": contract.functions.name().call(),
            "symbol": contract.functions.symbol().call(),
            "decimals": contract.functions.decimals().call()
        }

        return data
    
    def get_pair_token(self, factory, token0, token1):
        factory_address = factory.address
        contract = self.w3.eth.contract(address=factory_address, abi=factory.abi.getPair)

        try:
            pair_address = contract.functions.getPair(token0, token1).call()
            if pair_address == "0x0000000000000000000000000000000000000000":
                return False, "blank pair"
            return True, pair_address
        except Exception as e:
            return False, e
        
    def get_reserves(self, config, pair_address):
        pair_contract = self.w3.eth.contract(address=pair_address, abi=config.abi)

        token0_address = pair_contract.functions.token0().call()
        token1_address = pair_contract.functions.token1().call()
        token0 = self.get_token(token0_address)
        token1 = self.get_token(token1_address)
        
        reserves = pair_contract.functions.getReserves().call()
        res0, res1 = reserves[0], reserves[1]

        res0_std = res0 / 10**token0["decimals"]
        res1_std = res1 / 10**token1["decimals"]

        price0in1 = res1_std / res0_std
        price1in0 = res0_std / res1_std

        view.response_message("WARN", f"Price 1 {token0["symbol"]} = ~{price0in1} {token1["symbol"]}")
        view.response_message("WARN", f"Price 1 {token1["symbol"]} = ~{price1in0} {token0["symbol"]}")

        return reserves[0], reserves[1]