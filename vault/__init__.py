
from decimal import Decimal

class CollateralPrice:

    instance = None

    @staticmethod
    def get_instance():
        if CollateralPrice.instance is None:
            CollateralPrice.instance = CollateralPrice()
        return CollateralPrice.instance

    def __init__(self, price=None, factor=Decimal(1)):
        self.price = price
        self.factor = factor

    def set_price(self, price):
        self.price = price

    def get_price(self):
        return self.price.price * self.factor

    def get_buy_price(self):
        # Cuando uno quiere comprar tiene que pagar un poco más caro que en el precio de mercado.
        return self.get_price()

    def get_timestamp(self):
        return self.price.timestamp
    
    def set_factor(self, factor):
        self.factor = factor

class BuyCollateralException(Exception):
    pass

class WithdrawCollateralException(Exception):
    pass

class Wallet:

    def __init__(self, collateral_ammount, dai_ammount):
        self.collateral = collateral_ammount
        self.dai = dai_ammount

    def __str__(self):
        return "Collateral: {}, DAI: {}".format(
            self.collateral, self.dai
        )

    def buy_collateral(self, collateral_ammount):
        dai_ammount = collateral_ammount * CollateralPrice.get_instance().get_buy_price()
        if dai_ammount > self.dai:
            raise BuyCollateralException("DAI ammount in the wallet ({}), is lower than the DAI ammount required ({}), to buy {} ammount of collateral.".format(
                self.dai, dai_ammount, collateral_ammount
            ))
        self.collateral += collateral_ammount
        self.dai -= dai_ammount

    def withdraw_collateral(self, ammount):
        if ammount > self.collateral:
            raise Exception("Withdraw of collateral ammount {} is higher than the collateral ammount {} in wallet.".format(
                ammount, self.collateral
            ))
        self.collateral -= ammount

    def deposit_dai(self, ammount):
        self.dai += ammount


class Vault:

    def __init__(self, wallet: Wallet, collateral_locked, dai_debt, min_ratio=Decimal(1.5)):
        self.wallet = wallet
        self.collateral = collateral_locked
        self.dai_debt = dai_debt
        self.collateral_price = CollateralPrice.get_instance()
        self.min_ratio = min_ratio

    def __str__(self):
        return "Collateral locked: {}, Dai debt: {}, Risk: {}, Value in DAI: {}".format(
            self.collateral, self.dai_debt, self.get_risk(), self.get_value()
        )

    def get_collateral_needed_to_achieve_risk(self, risk_to_achive):
        return risk_to_achive * self.dai_debt / self.collateral_price.get_price() - self.collateral

    def get_dai_emission_to_achieve_risk(self, risk_to_achive):
        return self.collateral * self.collateral_price.get_price() / risk_to_achive - self.dai_debt

    def get_risk(self, dai_to_emit=Decimal(0)):
        # Risk = Dai Debt*ETH collateral/ETH Price
        dai_debt = self.dai_debt + dai_to_emit
        return self.collateral * self.collateral_price.get_price() / dai_debt

    def get_value(self):
        return self.collateral * self.collateral_price.get_price() - self.dai_debt

    def deposit_collateral(self, collateral_ammount):
        self.wallet.withdraw_collateral(collateral_ammount)
        self.collateral += collateral_ammount
        print('{}: {}: Collateral deposited: {}'.format(
            self.collateral_price.get_timestamp(),
            self.collateral_price.get_price(),
            collateral_ammount
            ))

    def is_in_liquidation_state(self, dai_to_emit=Decimal(0)):
        return self.get_risk(dai_to_emit) <= self.min_ratio

    def emit_dai(self, dai_ammount):
        if self.is_in_liquidation_state(dai_ammount):
            raise Exception("The DAI ammount to emit ({}) will generate a liquidation".format(dai_ammount))
        self.dai_debt += dai_ammount
        self.wallet.deposit_dai(dai_ammount)
        print('{}: {}: DAI emmited: {}'.format(
            self.collateral_price.get_timestamp(),
            self.collateral_price.get_price(),
            dai_ammount
            ))


class Strategy:

    def __init__(self, vault: Vault, 
        risk_lower_limit=Decimal(1.3),
        risk_target_lower_limit=Decimal(1.35),
        risk_target_upper_limit=Decimal(1.35),
        risk_upper_limit=Decimal(1.4),
        max_collateral_price=None
        ):

        self.vault = vault
        self.risk_lower_limit = risk_lower_limit
        self.risk_target_lower_limit = risk_target_lower_limit
        self.risk_target_upper_limit = risk_target_upper_limit
        self.risk_upper_limit = risk_upper_limit
        self.max_collateral_price = max_collateral_price

    
    def get_risk_lower_limit(self):
        return self.risk_lower_limit * self.vault.min_ratio

    def get_risk_target_lower_limit(self):
        return self.risk_target_lower_limit * self.vault.min_ratio

    def buy_collateral(self):
        
        if self.max_collateral_price is not None:
            if CollateralPrice.get_instance().get_buy_price() > self.max_collateral_price:
                return

        collateral_to_buy = self.vault.get_collateral_needed_to_achieve_risk(self.get_risk_target_lower_limit())

        try:
            self.vault.wallet.buy_collateral(collateral_to_buy)
            self.vault.deposit_collateral(collateral_to_buy)
        except BuyCollateralException as e:
            # TODO IMPORTANTE: Agregar notificación.
            # Significa que no se pudo comprar collateral, lo que implica que no se pudo
            # aumentar el riesgo de liquidación. Si el problema continúa podría llegar
            # al precio de liquidación.
            pass


    def get_risk_upper_limit(self):
        return self.risk_upper_limit * self.vault.min_ratio

    def get_risk_target_upper_limit(self):
        return self.risk_target_upper_limit * self.vault.min_ratio

    def emit_dai(self):
        dai_to_emit = self.vault.get_dai_emission_to_achieve_risk(self.get_risk_target_upper_limit())
        self.vault.emit_dai(dai_to_emit)

    def step(self):

        if self.vault.get_risk() < self.get_risk_lower_limit():
            self.buy_collateral()
        elif self.vault.get_risk() > self.get_risk_upper_limit():
            self.emit_dai()

    def simulate(self, prices_queryset):
        collateral_price = CollateralPrice.get_instance()
        for price in prices_queryset:
            collateral_price.set_price(price)
            self.step()