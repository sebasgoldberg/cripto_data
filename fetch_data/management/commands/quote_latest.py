import logging

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from decimal import Decimal

from django.core.management.base import BaseCommand

from django.conf import settings

from fetch_data.models import Price

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    help = "Obtains the las price for a currency in the specified price currency."

    def add_arguments(self, parser):
        parser.add_argument('--currency', nargs='?', type=str, default="ETH")
        parser.add_argument('--price_currency', nargs='?', type=str, default="DAI")

    def quote_latest(self, currency, price_currency):
        
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        parameters = {
            'symbol': currency,
            'convert': price_currency,
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': settings.X_CMC_PRO_API_KEY,
        }

        session = Session()
        session.headers.update(headers)

        response = session.get(url, params=parameters)
        currency_data = json.loads(response.text)['data'][currency]
        quote_data = currency_data['quote'][price_currency]
        Price.objects.create(
                # data.ETH
            currency=currency,
            num_market_pairs=int(currency_data['num_market_pairs']),
            circulating_supply=Decimal(currency_data['circulating_supply']),
            total_supply=Decimal(currency_data['total_supply']),
            last_updated=currency_data['last_updated'],

            # data.ETH.quote.DAI
            price=Decimal(quote_data['price']),
            price_currency=price_currency,
            volume_24h=Decimal(quote_data['volume_24h']),
            percent_change_1h=Decimal(quote_data['percent_change_1h']),
            percent_change_24h=Decimal(quote_data['percent_change_24h']),
            percent_change_7d=Decimal(quote_data['percent_change_7d']),
            market_cap=Decimal(quote_data['market_cap']),
            last_price_updated=quote_data['last_updated'],
        )
            
    def handle(self, *args, **options):

        self.quote_latest(options['currency'], options['price_currency'])
