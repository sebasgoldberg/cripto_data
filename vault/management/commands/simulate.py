import logging

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from decimal import Decimal

from django.core.management.base import BaseCommand

from django.conf import settings

from fetch_data.models import Price

logger = logging.getLogger(__name__)

from vault import *

class Command(BaseCommand):

    help = "Obtains the las price for a currency in the specified price currency."

    def add_arguments(self, parser):
        parser.add_argument('--currency', nargs='?', type=str, help="Currency", default='ETH')
        parser.add_argument('--ll', nargs='?', type=Decimal, help="Risk lower limit", default=Decimal(1.3))
        parser.add_argument('--tll', nargs='?', type=Decimal, help="Risk target lower limit", default=Decimal(1.35))
        parser.add_argument('--tul', nargs='?', type=Decimal, help="Risk target upper limit", default=Decimal(1.35))
        parser.add_argument('--ul', nargs='?', type=Decimal, help="Risk upper limit", default=Decimal(1.4))
        parser.add_argument('--wc', nargs='?', type=Decimal, help="Wallet initial colateral", default=Decimal(0))
        parser.add_argument('--wd', nargs='?', type=Decimal, help="Wallet initial DAI", default=Decimal(1470))
        parser.add_argument('--vc', nargs='?', type=Decimal, help="Vault initial locked colateral", default=Decimal(22))
        parser.add_argument('--vd', nargs='?', type=Decimal, help="Vault initial DAI debt", default=Decimal(1470))
        parser.add_argument('--repeat', nargs='?', type=int, 
            help="Repeat simulation n times using as input in the i-th simulation, the (i-1)-th simulation", 
            default=1)

    def print_state(self, text, vault: Vault, wallet: Wallet, price):
        self.stdout.write("-" * 40)
        self.stdout.write(text)
        self.stdout.write("Vault: {}".format(str(vault)))
        self.stdout.write("Wallet: {}".format(str(wallet)))
        self.stdout.write("Colateral price: {}: {}".format(price.timestamp, price.price))
        self.stdout.write("Total in DAI: {}".format(vault.get_value() + wallet.dai))
        self.stdout.write("-" * 40)

    def simulate(self, currency, ll, tll, tul, ul, wc, wd, vc, vd, repeat, *args, **kwargs):
        """
        Liquidation Price = Dai Debt*1.5/ETH colateral
        Risk = Dai Debt*ETH colateral/ETH Price
        Minimum ratio: Si Risk <= Minimum ratio, quiere decir que llegamos al Liquidation Price.

        La idea es la siguiente:
        - Cuando Risk <  LI * Minimum ratio:
            - Compramos ETH con una parte de nuestro DAI de forma que: Risk >= OI * Minimum ratio.
            - Depositamos el ETH comprado en nuestra bóveda.
        - Cuando Risk > LS * Minimum ratio:
            - Emitimos DAI de forma que: Risk <= OS * Minimum ratio
        """
        
        q = Price.objects.filter(currency=currency)

        wallet = Wallet(wc, wd)
        colateral_price = ColateralPrice.get_instance()
        colateral_price.set_price(q.first())
        vault = Vault(wallet, vc, vd)
        strategy = Strategy(vault, ll, tll, tul, ul)

        self.print_state("Before simulation", vault, wallet, q.first())

        for i in range(repeat):
            strategy.simulate(q)

        self.print_state("After simulation", vault, wallet, q.last())

            
    def handle(self, *args, **options):

        self.simulate(**options)
