#!/usr/bin/env python3
import logging
import pandas as pd
import ccxt
from .exchange import Exchange

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class CCXT(Exchange):

    def __init__(self, exchange, key=None, secret=None, passphrase=None):
        super(CCXT, self).__init__()
        self.name = exchange
        self.key = key
        self.secret = secret
        self.passphrase = passphrase
        exchange_class = getattr(ccxt, self.name.lower())
        self.exchange = exchange_class({
            'apiKey': key,
            'secret': secret,
            'password': passphrase,
            'uid': passphrase,
            'timeout': 30000,
            'enableRateLimit': True,
            'verbose': True,
        })
        self._ccxt_query('fetch_markets')
        log.info(ccxt.__version__)
        log.info(f'{exchange} Instantiated')

    def _ccxt_query(self, method, *args, **kwargs):
        return super(CCXT, self)._ccxt_query(self.exchange, method, *args, **kwargs)
                    
    # Public calls
    def get_orderbook(self, base='ETH', quote='BTC', limit=100, side=None):
        '''
        returns orderbook as {'bids','asks': (price, amount)}
        specify limit/side to limit results.
        side can optionally be 'bids' or 'asks' for only respective book
        '''
        if self.exchange.has['fetchL2OrderBook']:
            symbol = f'{base.upper()}/{quote.upper()}'
            ret = self._ccxt_query('fetch_l2_order_book', symbol, limit)

            if ret:
                orderbook = {'bids': [], 'asks': []}
                if side != 'asks':
                    for bid in ret['bids']:
                        orderbook['bids'].append((float(bid[0]), float(bid[1])))
                if side != 'bids':
                    for ask in ret['asks']:
                        orderbook['asks'].append((float(ask[0]), float(ask[1])))
                return orderbook
            else:
                return None
        else:
            log.debug(f'Method get_orderbook() unavailable for {self.exchange.name}')
            return []

    def get_history(self, base='ETH', quote='BTC', limit=50, since=None):
        '''
        specify limit/since to limit results.
        since is timestamp in milliseconds
        '''
        now = self.exchange.milliseconds()
        if not since:
            since = self.exchange.milliseconds() - 86400000  # -1 day from now

        all_trades = []
        symbol = f'{base.upper()}/{quote.upper()}'
        while since < now:
            trades = self._ccxt_query('fetch_trades', symbol, since, limit)
            if trades and len(trades):
                if since == trades[-1]['timestamp']:
                    break
                since = trades[-1]['timestamp']
                all_trades += trades
            else:
                break
        
        # Reverse so newest first
        all_trades.reverse()
        df = pd.DataFrame(all_trades, columns=(
            'price', 'amount', 'timestamp', 'side', 'type', 'fee',
            'cost', 'order', 'id'))
        df.timestamp = pd.to_datetime(df.timestamp, unit='ms', utc=True)

        history = df.to_dict('records')
        return history

    def get_candles(self, base='BTC', quote='USD', interval='1h', since=None, limit=1000):
        """
        returns candles oldest to newest
        start is optional start datetime
        limit is optional integer limit
        """
        now = self.exchange.milliseconds()
        if not since:
            since = self.exchange.milliseconds() - 86400000  # -1 day from now

        if self.exchange.has['fetchOHLCV']:
            symbol = f'{base.upper()}/{quote.upper()}'
            all_candles = []
            while since < now:
                candles = self._ccxt_query('fetch_ohlcv', 
                                 symbol, 
                                 interval,
                                 since,
                                 limit
                                 )
                if candles and len(candles):
                    if since == candles[-1][0]:
                        break
                    since = candles[-1][0]
                    all_candles += candles
                else:
                    break

        c = pd.DataFrame(all_candles, columns=('timestamp', 'open', 'high',
                                       'low', 'close', 'volume'))
        c.timestamp = pd.to_datetime(c.timestamp, unit='ms')
        c = c.set_index('timestamp')
        c = c.reset_index().drop_duplicates(subset='timestamp', keep='first').set_index('timestamp')
        return c

    def get_markets(self):
        # Get pairs
        markets = self._ccxt_query('load_markets')
        symbols = [symbol for symbol in markets.keys() if '/' in symbol]
        return symbols

    def get_details(self, base='ETH', quote='BTC'):
        """
        Returns dict of:
            'min_amt' - the minimum quantity of the base currency we want to buy or sell
            'min_price' - the minimum amount of the quote currency we can ask or bid
            'min_val' - the minimum total amount of the order (quantity * price)
            'amt_precision' - the increment in the base currency quantity
            'price_precision' - the increment in the price
        """
        symbol = f'{base.upper()}/{quote.upper()}'

        info = self._ccxt_query('load_markets')[symbol]

        details = {}
        min_amount = info['limits']['amount']['min']
        if not min_amount:
            min_amount = 0
        min_price = info['limits']['price']['min']
        if not min_price:
            min_price = 0

        if self.name == "CoinbasePro":
            if base.upper() != 'BTC':
                min_amount = 1

        min_val = min_amount * min_price
        d = {
            'min_amt': min_amount,
            'max_amt': info['limits']['amount']['max'],
            'min_price' : min_price,
            'max_price': info['limits']['price']['max'],
            'min_val': min_val,
            'amt_precision': info['precision']['amount'],
            'price_precision': info['precision']['price'],
        }
        if 'lot' in info:
            d['lot'] = info['lot']
        if 'cost' in info['limits']:
            min_value = info['limits']['cost']['min']
            if min_value:
                d['min_val'] = min_value
        details[quote] = {base: d}
        return details[quote][base]

    # Private calls
    def get_balances(self):
        # Fetch balances
        balances = self._ccxt_query('fetch_balance')

        if balances:
            del balances['info']
            del balances['free']
            del balances['used']
            del balances['total']
            bals = {}
            for cur, bal in balances.items():
                bals[cur] = {
                    'total': bal['total'],
                    'reserved': bal['used'],
                    'available': bal['free'],
                    }
            return bals
        else:  
            log.debug('Balance query failed.')
            return None

    def get_trades(self, base=None, quote=None, limit=1000, since=None):
        symbol = None
        if base and quote:
            symbol = f'{base.upper()}/{quote.upper()}'

        if self.name == 'Poloniex':
            # End in seconds 10 days from since
            days = 10
            end = int(since/1000) + 24 * 60 * 60 * days
            params = {'end': end}
            trades = self._ccxt_query('fetch_my_trades', symbol, since, limit, params)
        else:
            trades = self._ccxt_query('fetch_my_trades', symbol, since, limit)
            
        t = pd.DataFrame(
                trades, 
                columns=(
                    'id', 
                    'timestamp', 
                    'datetime', 
                    'symbol', 
                    'order', 
                    'type', 
                    'side', 
                    'price', 
                    'amount', 
                    'cost', 
                    'fee')
                )

        t = t.reset_index().drop_duplicates(subset='timestamp', keep='first').set_index('datetime')
        t = t.sort_index()
        return t.to_json()

    def get_transactions(self, limit=1000, since=None):

        if self.exchange.has['fetchTransactions']:
            txs = self._ccxt_query('fetch_transactions', None, since, limit)

        else:
            txs = []
            deposits = self._ccxt_query('fetch_deposits', None, since, limit)
            withdrawals = self._ccxt_query('fetch_withdrawals', None, since, limit)
            txs += deposits
            txs += withdrawals             

        t = pd.DataFrame(
                txs, 
                columns=(
                    'id', 
                    'txid',
                    'timestamp', 
                    'datetime', 
                    'address', 
                    'tag', 
                    'type', 
                    'amount', 
                    'currency', 
                    'status', 
                    'updated', 
                    'fee')
                )
        t.datetime = pd.to_datetime(t.timestamp, unit='ms')
        t = t.reset_index().drop_duplicates(subset='timestamp', keep='first').set_index('datetime')
        t = t.sort_index()
        return t.to_json()

    def get_order(self, order_id, base=None, quote=None):

        symbol = ''
        if base and quote:
            symbol = f'{base.upper()}/{quote.upper()}'

        order = self._ccxt_query('fetch_order', order_id, symbol)

        if order:
            o = {
                'timestamp': pd.to_datetime(order['timestamp'], unit='ms', utc=True),
                'base': order['symbol'].split('/')[0],
                'quote': order['symbol'].split('/')[1],
                'side': order['side'],
                'price': order['price'],
                'amount': order['amount'],
                'filled': order['filled'],
                'unfilled': order['remaining'],
                'avg_price': order['cost'],
                'open': order['status'] == 'open',
                'status': order['status']
            }
            return o
        else:
            return None

    def get_orders(self, base=None, quote=None):

        if self.exchange.has['fetchOpenOrders']:
            if base and quote:
                symbol = f'{base.upper()}/{quote.upper()}'
                orders = self._ccxt_query('fetch_open_orders', symbol)
            else:
                orders = self._ccxt_query('fetch_open_orders')

        open_orders = {}
        for order in orders:
            open_orders[order['id']] = {
                'timestamp': pd.to_datetime(order['timestamp'], unit='ms', utc=True),
                'base': order['symbol'].split('/')[0],
                'quote': order['symbol'].split('/')[1],
                'side': order['side'],
                'price': order['price'],
                'amount': order['amount'],
                'filled': order['filled'],
                'unfilled': order['remaining'],
                'avg_price': order['cost'],
                'open': order['status'] == 'open',
                'status': order['status']
            }
        return open_orders

    def order(self, side, amount, price, base='ETH', quote='BTC',
        type='limit'):
        # Place order
        symbol = f'{base.upper()}/{quote.upper()}'
        log.debug(f'Placing order for {symbol}')
        self._ccxt_query('load_markets')
        details = self.get_details(base=base, quote=quote)

        price = self.exchange.price_to_precision(symbol, price)
        if 'lot' in details:
            lot_amount = amount - amount % details['lot']
            amount = round(lot_amount, 8)
        amount = self.exchange.amount_to_precision(symbol, amount)

        return self._ccxt_query('create_order', symbol, type, 
                                side, amount, price)['id']


    def cancel(self, order_id=None, base=None, quote=None):
        # If no argument supplied, cancel all orders
        symbol = ''
        # Cancel order_id
        if base and quote:
            symbol = f'{base.upper()}/{quote.upper()}'

        resp = self._ccxt_query('cancel_order', order_id, symbol)
        if not resp:
            return False
        return True

    def test_trading_enabled(self): 
        """
        Verify if trading is enabled for user API Key
        Response details: Function should return True if trading is enabled.
        and False if trading isn't enabled, and raise an exception if any error occurs during the testing process.
        """
        price = self.get_orderbook(base='ETH', quote='BTC', limit=10, side='bids')['bids'][0][0]
        price = price * 0.7

        symbol = 'ETH/BTC'
        self._ccxt_query('load_markets')
        price = self.exchange.price_to_precision(symbol, price)
        
        try:
            order_id = self.exchange.create_order(symbol, 'limit', 'buy', 1, price)['id']
        except ccxt.InsufficientFunds:
            return True
        except ccxt.InvalidOrder:
            return True
        except ccxt.AuthenticationError:
            return False
        except ccxt.PermissionDenied:
            return False
        except ccxt.ExchangeError as e:
            log.debug(e)
            return True
        
        if order_id is not None:
            log.debug(f'Deleting order {order_id}')
            self.cancel(order_id, 'ETH', 'BTC')

        return True

    def test_withdrawal(self):
        try:
            self.exchange.withdraw('BTC', 0.00000001, '1NtT5GttSPfg9Pm1dPoASaD2YSGeTqWLFC')
        except ccxt.AuthenticationError:
            return False
        except ccxt.PermissionDenied:
            return False
        except ccxt.ExchangeError:
            return False
        except Exception as e:
            log.warn(e)
            return e
        return True