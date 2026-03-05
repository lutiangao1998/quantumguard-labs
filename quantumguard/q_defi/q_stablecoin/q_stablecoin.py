from typing import Dict, Any

class QStablecoin:
    def __init__(self):
        self.collateral_pools: Dict[str, Dict[str, float]] = {}
        self.stablecoin_supply: Dict[str, float] = {}
        self.collateral_ratios: Dict[str, float] = {}

    def set_collateral_ratio(self, stablecoin: str, ratio: float):
        if not (1.0 < ratio < 2.0): # Typically overcollateralized, e.g., 150%
            raise ValueError("Collateral ratio must be between 1.0 and 2.0 (e.g., 1.5 for 150%)")
        self.collateral_ratios[stablecoin] = ratio

    def mint(self, user: str, stablecoin: str, amount: float, collateral_asset: str, collateral_amount: float, collateral_price: float):
        if stablecoin not in self.collateral_ratios:
            raise ValueError("Stablecoin not configured")
        
        required_collateral_value = amount * collateral_price * self.collateral_ratios[stablecoin]
        if collateral_amount * collateral_price < required_collateral_value:
            raise ValueError("Insufficient collateral")

        if stablecoin not in self.collateral_pools:
            self.collateral_pools[stablecoin] = {}
        self.collateral_pools[stablecoin][collateral_asset] = self.collateral_pools[stablecoin].get(collateral_asset, 0) + collateral_amount
        self.stablecoin_supply[stablecoin] = self.stablecoin_supply.get(stablecoin, 0) + amount
        print(f"User {user} minted {amount} {stablecoin} with {collateral_amount} {collateral_asset}")

    def redeem(self, user: str, stablecoin: str, amount: float, collateral_asset: str, collateral_amount: float):
        if stablecoin not in self.stablecoin_supply or self.stablecoin_supply[stablecoin] < amount:
            raise ValueError("Insufficient stablecoin supply or user balance")
        if stablecoin not in self.collateral_pools or self.collateral_pools[stablecoin].get(collateral_asset, 0) < collateral_amount:
            raise ValueError("Insufficient collateral in pool")

        self.collateral_pools[stablecoin][collateral_asset] -= collateral_amount
        self.stablecoin_supply[stablecoin] -= amount
        print(f"User {user} redeemed {amount} {stablecoin} and received {collateral_amount} {collateral_asset}")

    def get_stablecoin_supply(self, stablecoin: str) -> float:
        return self.stablecoin_supply.get(stablecoin, 0)

    def get_collateral_amount(self, stablecoin: str, collateral_asset: str) -> float:
        return self.collateral_pools.get(stablecoin, {}).get(collateral_asset, 0)

