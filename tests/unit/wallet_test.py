from aixplain.factories import WalletFactory
import pytest

def test_wallet():
    factory = WalletFactory()
    with pytest.raises(Exception):
        wallet = factory.get()
    total_balance_str= f"Total Balance: {wallet.totalBalance}."
    reserved_balance_str= f"Reserved Balance: {wallet.reservedBalance}."
    assert str(total_balance_str) == "Total Balance: 5."
    assert str(reserved_balance_str=="Reserced Balance: 0.")


