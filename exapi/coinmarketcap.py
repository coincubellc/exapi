#!/usr/bin/env python3
from .exchange import Exchange


class CoinMarketCap(Exchange):
    name = 'CMC'
    _reqinterval = 60   # seconds
    _reqlimit = 10
    _baseurl = 'https://api.coinmarketcap.com/v1/'

    def __init__(self):
        super(CoinMarketCap, self).__init__()

    def _query(self, url, *args, **kwargs):
        ret = super(CoinMarketCap, self)._query('get', url, *args, **kwargs)
        return ret

    def get_market_cap(self, coin):
        url = self._baseurl + 'ticker/%s' % coin.upper()
        ret = self._query(url)
        return ret['mktcap']

    def get_market_cap_all(self):
        url = self._baseurl + 'ticker/'
        ret = self._query(url)
        return ret