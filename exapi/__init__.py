from .coincap import CoinCap
from .coinmarketcap import CoinMarketCap
from .ccxt_exapi import CCXT 

exs = {
    'CoinCap': {'PUBLIC': CoinCap},
    'CoinMarketCap': {'PUBLIC': CoinMarketCap()},
    }

exchanges = ['Binance', 'Bitfinex', 'Bitstamp', 'Bittrex',
             'CoinbasePro', 'Kraken', 'Kucoin',
             'Liquid', 'Poloniex']

for ex_name in exchanges:
    if ex_name == 'Kucoin':
        exs[ex_name] = {'PUBLIC': CCXT('Kucoin2')}       
    else:
        exs[ex_name] = {'PUBLIC': CCXT(ex_name)}

