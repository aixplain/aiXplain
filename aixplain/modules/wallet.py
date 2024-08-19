from typing import Union


class Wallet:
    def __init__(self, totalBalance: Union[int, float], reservedBalance: Union[int, float]):
        self.totalBalance = totalBalance
        self.reservedBalance = reservedBalance
