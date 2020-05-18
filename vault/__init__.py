
from decimal import Decimal

class ColateralPrice:

    instance = None

    @staticmethod
    def get_instance():
        if ColateralPrice.instance is None:
            ColateralPrice.instance = ColateralPrice()
        return ColateralPrice.instance

    def __init__(self, price=Decimal(0)):
        self.price = price

    def set_price(self, price):
        self.price = price

    def get_price(self):
        return self.price

    def get_buy_price(self):
        # Cuando uno quiere comprar tiene que pagar un poco más caro que en el precio de mercado.
        return self.get_price()


class Wallet:

    def __init__(self, colateral_ammount, dai_ammount):
        self.colateral = colateral_ammount
        self.dai = dai_ammount

    def __str__(self):
        return "Colateral: {}, DAI: {}".format(
            self.colateral, self.dai
        )

    def buy_colateral(self, colateral_ammount):
        dai_ammount = colateral_ammount * ColateralPrice.get_instance().get_buy_price()
        if dai_ammount > self.dai:
            raise Exception("DAI ammount in the wallet ({}), is lower than the DAI ammount required ({}), to buy {} ammount of colateral.".format(
                [self.dai, dai_ammount, colateral_ammount]
            ))
        self.colateral += colateral_ammount
        self.dai -= dai_ammount

    def withdraw_colateral(self, ammount):
        if ammount > self.colateral:
            raise Exception("Withdraw of colateral ammount {} is higher than the colateral ammount {} in wallet.".format(
                [ammount, self.colateral]
            ))
        self.colateral -= ammount

    def deposit_dai(self, ammount):
        self.dai += ammount


class Vault:

    def __init__(self, wallet: Wallet, colateral_locked, dai_debt, colateral_price: ColateralPrice, min_ratio=Decimal(1.5)):
        self.wallet = wallet
        self.colateral = colateral_locked
        self.dai_debt = dai_debt
        self.colateral_price = colateral_price
        self.min_ratio = min_ratio

    def __str__(self):
        return "Colateral locked: {}, Dai debt: {}, Risk: {}, Value in DAI: {}".format(
            self.colateral, self.dai_debt, self.get_risk(), self.get_value()
        )

    def get_colateral_needed_to_achieve_risk(self, risk_to_achive):
        return risk_to_achive * self.dai_debt / self.colateral_price.get_price() - self.colateral

    def get_dai_emission_to_achieve_risk(self, risk_to_achive):
        return self.colateral * self.colateral_price.get_price() / risk_to_achive - self.dai_debt

    def get_risk(self, dai_to_emit=Decimal(0)):
        # Risk = Dai Debt*ETH colateral/ETH Price
        dai_debt = self.dai_debt + dai_to_emit
        return self.colateral * self.colateral_price.get_price() / dai_debt

    def get_value(self):
        return self.colateral * self.colateral_price.get_price() - self.dai_debt

    def deposit_colateral(self, colateral_ammount):
        self.wallet.withdraw_colateral(colateral_ammount)
        self.colateral += colateral_ammount
        print('{}: Colateral deposited: {}'.format(self.colateral_price.get_price(), colateral_ammount))

    def is_in_liquidation_state(self, dai_to_emit=Decimal(0)):
        return self.get_risk(dai_to_emit) <= self.min_ratio

    def emit_dai(self, dai_ammount):
        if self.is_in_liquidation_state(dai_ammount):
            raise Exception("The DAI ammount to emit ({}) will generate a liquidation")
        self.dai_debt += dai_ammount
        self.wallet.deposit_dai(dai_ammount)
        print('{}: DAI emmited: {}'.format(self.colateral_price.get_price(), dai_ammount))


class Strategy:

    def __init__(self, vault: Vault, 
        risk_lower_limit=Decimal(1.3),
        risk_target_lower_limit=Decimal(1.35),
        risk_target_upper_limit=Decimal(1.35),
        risk_upper_limit=Decimal(1.4)
        ):

        self.vault = vault
        self.risk_lower_limit = risk_lower_limit
        self.risk_target_lower_limit = risk_target_lower_limit
        self.risk_target_upper_limit = risk_target_upper_limit
        self.risk_upper_limit = risk_upper_limit

    
    def get_risk_lower_limit(self):
        return self.risk_lower_limit * self.vault.min_ratio

    def get_risk_target_lower_limit(self):
        return self.risk_target_lower_limit * self.vault.min_ratio

    def buy_colateral(self):
        collateral_to_buy = self.vault.get_colateral_needed_to_achieve_risk(self.get_risk_target_lower_limit())
        self.vault.wallet.buy_colateral(collateral_to_buy)
        self.vault.deposit_colateral(collateral_to_buy)

    def get_risk_upper_limit(self):
        return self.risk_upper_limit * self.vault.min_ratio

    def get_risk_target_upper_limit(self):
        return self.risk_target_upper_limit * self.vault.min_ratio

    def emit_dai(self):
        dai_to_emit = self.vault.get_dai_emission_to_achieve_risk(self.get_risk_target_upper_limit())
        self.vault.emit_dai(dai_to_emit)

    def step(self):

        if self.vault.get_risk() < self.get_risk_lower_limit():
            self.buy_colateral()
        elif self.vault.get_risk() > self.get_risk_upper_limit():
            self.emit_dai()

    def simulate(self, prices_queryset, colateral_price: ColateralPrice):
        for price in prices_queryset:
            colateral_price.set_price(price.price)
            self.step()