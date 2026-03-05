from typing import Dict, Any

class QLending:
    def __init__(self):
        self.assets: Dict[str, float] = {}
        self.borrows: Dict[str, Dict[str, float]] = {}
        self.deposits: Dict[str, Dict[str, float]] = {}
        self.interest_rates: Dict[str, float] = {}
        self.collateral_factors: Dict[str, float] = {}

    def set_asset_price(self, asset: str, price: float):
        self.assets[asset] = price

    def set_interest_rate(self, asset: str, rate: float):
        self.interest_rates[asset] = rate

    def set_collateral_factor(self, asset: str, factor: float):
        self.collateral_factors[asset] = factor

    def deposit(self, user: str, asset: str, amount: float):
        if asset not in self.deposits:
            self.deposits[asset] = {}
        self.deposits[asset][user] = self.deposits[asset].get(user, 0) + amount
        print(f"User {user} deposited {amount} {asset}")

    def withdraw(self, user: str, asset: str, amount: float):
        if asset not in self.deposits or self.deposits[asset].get(user, 0) < amount:
            raise ValueError("Insufficient deposit")
        self.deposits[asset][user] -= amount
        print(f"User {user} withdrew {amount} {asset}")

    def borrow(self, user: str, borrow_asset: str, borrow_amount: float, collateral_asset: str, collateral_amount: float):
        if borrow_asset not in self.assets or collateral_asset not in self.assets:
            raise ValueError("Unknown asset")
        if borrow_asset not in self.interest_rates or collateral_asset not in self.collateral_factors:
            raise ValueError("Asset not configured for lending")

        collateral_value = collateral_amount * self.assets[collateral_asset] * self.collateral_factors[collateral_asset]
        borrow_value = borrow_amount * self.assets[borrow_asset]

        if borrow_value > collateral_value:
            raise ValueError("Insufficient collateral")

        if borrow_asset not in self.borrows:
            self.borrows[borrow_asset] = {}
        self.borrows[borrow_asset][user] = self.borrows[borrow_asset].get(user, 0) + borrow_amount
        self.deposit(user, collateral_asset, collateral_amount) # Simulate collateral deposit
        print(f"User {user} borrowed {borrow_amount} {borrow_asset} with {collateral_amount} {collateral_asset} as collateral")

    def repay(self, user: str, borrow_asset: str, repay_amount: float):
        if borrow_asset not in self.borrows or self.borrows[borrow_asset].get(user, 0) < repay_amount:
            raise ValueError("No outstanding loan or repay amount too high")
        self.borrows[borrow_asset][user] -= repay_amount
        print(f"User {user} repaid {repay_amount} {borrow_asset}")

    def get_user_borrow_limit(self, user: str) -> float:
        total_collateral_value = 0
        for asset, deposits_by_user in self.deposits.items():
            if user in deposits_by_user and asset in self.assets and asset in self.collateral_factors:
                total_collateral_value += deposits_by_user[user] * self.assets[asset] * self.collateral_factors[asset]
        return total_collateral_value

    def get_user_total_borrowed_value(self, user: str) -> float:
        total_borrowed_value = 0
        for asset, borrows_by_user in self.borrows.items():
            if user in borrows_by_user and asset in self.assets:
                total_borrowed_value += borrows_by_user[user] * self.assets[asset]
        return total_borrowed_value

    def liquidate(self, liquidator: str, user: str, collateral_asset: str, borrow_asset: str, repay_amount: float):
        # Simplified liquidation logic for prototype
        user_borrowed_value = self.get_user_total_borrowed_value(user)
        user_borrow_limit = self.get_user_borrow_limit(user)

        if user_borrowed_value < user_borrow_limit: # Not underwater
            raise ValueError("User's loan is not eligible for liquidation")
        
        # Perform liquidation: repay borrow_asset, seize collateral_asset
        self.repay(user, borrow_asset, repay_amount)
        # Logic to transfer collateral from user to liquidator
        print(f"User {user} liquidated by {liquidator} for {repay_amount} {borrow_asset}")

