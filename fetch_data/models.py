from django.db import models

VOLUME_MAX_DIGITS=22
VOLUME_DECIMALS_PLACES=6

PERCENT_MAX_DIGITS=11
PERCENT_DECIMALS_PLACES=8

PRICE_MAX_DIGITS=30
PRICE_DECIMALS_PLACES=20

SYMBOL_MAX_LENGTH=10


class Price(models.Model):

    timestamp = models.DateTimeField(auto_now_add=True)

    # data.ETH
    currency = models.CharField(max_length=SYMBOL_MAX_LENGTH) # data.ETH
    num_market_pairs = models.IntegerField()
    circulating_supply = models.DecimalField(max_digits=VOLUME_MAX_DIGITS, decimal_places=VOLUME_DECIMALS_PLACES)
    total_supply = models.DecimalField(max_digits=VOLUME_MAX_DIGITS, decimal_places=VOLUME_DECIMALS_PLACES)
    last_updated = models.DateTimeField()

    # data.ETH.quote.DAI
    price = models.DecimalField(max_digits=PRICE_MAX_DIGITS, decimal_places=PRICE_DECIMALS_PLACES)
    price_currency = models.CharField(max_length=SYMBOL_MAX_LENGTH) # data.ETH.quote.DAI
    volume_24h = models.DecimalField(max_digits=VOLUME_MAX_DIGITS, decimal_places=VOLUME_DECIMALS_PLACES)
    percent_change_1h = models.DecimalField(max_digits=PERCENT_MAX_DIGITS, decimal_places=PERCENT_DECIMALS_PLACES)
    percent_change_24h = models.DecimalField(max_digits=PERCENT_MAX_DIGITS, decimal_places=PERCENT_DECIMALS_PLACES)
    percent_change_7d = models.DecimalField(max_digits=PERCENT_MAX_DIGITS, decimal_places=PERCENT_DECIMALS_PLACES)
    market_cap = models.DecimalField(max_digits=VOLUME_MAX_DIGITS, decimal_places=VOLUME_DECIMALS_PLACES)
    last_price_updated = models.DateTimeField()

    def __str__(self):
        return '{}: 1 {} == {} {}'.format(
            self.timestamp,
            self.currency,
            self.price,
            self.price_currency
            )