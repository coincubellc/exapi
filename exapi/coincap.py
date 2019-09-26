#!/usr/bin/env python3
from .exchange import Exchange


class CoinCap(Exchange):
    name = 'CC'
    _reqinterval = 60   # seconds
    _reqlimit = 10
    _baseurl = 'http://www.coincap.io/'

    def __init__(self):
        super(CoinCap, self).__init__()

    def _query(self, url, *args, **kwargs):
        ret = super(CoinCap, self)._query('get', url, *args, **kwargs)
        return ret

    def get_market_cap(self, coin):
        url = self._baseurl + 'page/%s' % coin.upper()
        ret = self._query(url)
        return ret['mktcap']