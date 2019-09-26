import logging
from time import time, sleep
from threading import RLock
from decimal import Decimal as dec
import exapi

GRACE_TIME = 5  # seconds to sleep on exception
API_RETRIES = 2

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class PCError(Exception):
    pass


class PriceCacher(object):
    def __init__(self, cachetime=60):
        self.cachetime = cachetime
        self.rlock = RLock()
        self.cache = {}

    def get_price(self, ex, base, quote, limit=10):
        # return cached price if not expired
        try:
            if self.cache[ex][quote][base]['expiry'] > time():
                log.debug(f'Retrieving cached price for {ex}: {quote}/{base}')
                log.debug(self.cache[ex][quote][base]['price'])
                return self.cache[ex][quote][base]['price']
        except KeyError:
            pass
        with self.rlock:
            # re-attempt in case of queued requests
            try:
                if self.cache[ex][quote][base]['expiry'] > time():
                    log.debug(f'Retrieving cached price for {ex}: {quote}/{base}')
                    log.debug(self.cache[ex][quote][base]['price'])
                    return self.cache[ex][quote][base]['price']
            except KeyError:
                pass

            for i in range(API_RETRIES):
                try:
                    ob = exapi.exs[ex]['PUBLIC'].get_orderbook(base, quote, limit=limit)
                    log.debug(ob)
                    # Mid price (midway between best bid and ask)
                    c = {
                        'price': dec(ob['bids'][0][0] + ob['asks'][0][0]) / 2,
                        'expiry': time() + self.cachetime
                    }
                    try:
                        self.cache[ex][quote][base] = c
                    except KeyError:
                        try:
                            self.cache[ex][quote] = {
                                base: c
                            }
                        except KeyError:
                            self.cache[ex] = {
                                quote: {base: c}
                            }
                    return self.cache[ex][quote][base]['price']
                except Exception as e:
                    log.debug('[PC] %s %s/%s: %s' % (ex, base, quote, e))
                    if i + 1 < API_RETRIES:
                        sleep(GRACE_TIME)
                    else:
                        try:
                            p = self.cache[ex][quote][base]['price']
                        except KeyError:
                            tb = e
                        else:
                            log.warn('[PC] Returning stale data for %s %s/%s' % (ex, base, quote))
                            return p
            raise PCError(tb)