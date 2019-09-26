import sys
sys.path.insert(0, '/')
import logging
from flask_apispec import MethodResource, doc, use_kwargs as use_kwargs_doc
from flask_restful import abort
from webargs import fields, validate
from webargs.flaskparser import use_kwargs 
from marshmallow import missing
import exapi
from price_cacher import PriceCacher, PCError

cacher = PriceCacher()

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

credArgs = ['key', 'secret', 'passphrase']
def pruneArgs(args):
    return {k: v for k, v in args.items() if v is not missing and k not in credArgs}
def pruneCreds(args):
    return {k: v for k, v in args.items() if v is not missing and k in credArgs}

base_args = {
}
secure_args = {**base_args, **{
    'key': fields.Str(required=True, description='The API key for exchange authentication'),
    'secret': fields.Str(required=True, description='The API password / secret for exchange authentication'),
    'passphrase': fields.Str(required=False, description='The passphrase or user ID for exchange authentication, if needed')
}}

def addExchange(exchangeName, key, secret, passphrase=None):
    if exchangeName == 'Kucoin':
        ex = exapi.CCXT('Kucoin2', key=key, secret=secret, passphrase=passphrase)
    else:
        ex = exapi.CCXT(exchangeName, key=key, secret=secret, passphrase=passphrase)
    exapi.exs[exchangeName][key] = ex
    return ex

def get_secure_ex(exchangeName, kwargs):
    if kwargs.get('key') in exapi.exs[exchangeName]:
        log.debug(f'Using cached {exchangeName} CCXT object for {kwargs.get("key")}')
        ex = exapi.exs[exchangeName][kwargs.get('key')]
    else:
        log.debug(f'Creating new {exchangeName} CCXT object for {kwargs.get("key")}')
        ex = addExchange(exchangeName, **pruneCreds(kwargs))
    return ex

# ----------------------------------------------- Unsecured Resources

class Healthcheck(MethodResource):
    @doc(tags=['Healthcheck'], description='Endpoint for checking API health')
    def get(self):
        return {'message': 'exapi API is running'}

class OrderBookResource(MethodResource):
    get_args = {**base_args, **{
        'base': fields.Str(required=False, description='Base currency code'),
        'quote': fields.Str(required=False, description='Quote currency code'),
        'limit': fields.Integer(required=False, description='The maximum number of orders to retrieve'),
        'side': fields.Str(required=False,
                validate=validate.OneOf(['bids', 'asks']),
                description='The order book to retrieve'
        )
    }}
    @use_kwargs(get_args)
    @use_kwargs_doc(get_args, locations=['query'])
    @doc(tags=['Unsecured'], description='Retrieves the current order book at the exchange.')
    def get(self, exchangeName, **kwargs):
        ex = exapi.exs[exchangeName]['PUBLIC']
        return ex.get_orderbook(**pruneArgs(kwargs))

class CachedMidPriceResource(MethodResource):
    get_args = {**base_args, **{
        'base': fields.Str(required=False, description='Base currency code'),
        'quote': fields.Str(required=False, description='Quote currency code'),
    }}
    @use_kwargs(get_args)
    @use_kwargs_doc(get_args, locations=['query'])
    @doc(tags=['Unsecured'], description='Retrieves the current mid price from the order book at the exchange.')
    def get(self, exchangeName, **kwargs):
        try:
            return {
                'success': True,
                'price_str': str(cacher.get_price(exchangeName, **pruneArgs(kwargs))),
                'price_float': float(cacher.get_price(exchangeName, **pruneArgs(kwargs))),
            }
        except PCError as e:
            return {
                'success': False,
                'error': str(e),
            }

class HistoryResource(MethodResource):
    get_args = {**base_args, **{
        'base': fields.Str(required=False, description='Base currency code'),
        'quote': fields.Str(required=False, description='Quote currency code'),
        'limit': fields.Integer(required=False, description='The maximum number of trades to return'),
        'since': fields.Integer(required=False, description='Start time')
    }}
    @use_kwargs(get_args)
    @use_kwargs_doc(get_args, locations=['query'])
    @doc(tags=['Unsecured'], description='Retrieves recent trade history for the specified currency pair.')
    def get(self, exchangeName, **kwargs):
        ex = exapi.exs[exchangeName]['PUBLIC']
        return ex.get_history(**pruneArgs(kwargs))

class DetailsResource(MethodResource):
    get_args = {**base_args, **{
        'base': fields.Str(required=False, description='Base currency code'),
        'quote': fields.Str(required=False, description='Quote currency code'),
    }}
    @use_kwargs(get_args)
    @use_kwargs_doc(get_args, locations=['query'])
    @doc(tags=['Unsecured'], description='Retrieves details for the specified currency pair.')
    def get(self, exchangeName, **kwargs):
        ex = exapi.exs[exchangeName]['PUBLIC']
        return ex.get_details(**pruneArgs(kwargs))

class MarketsResource(MethodResource):
    @doc(tags=['Unsecured'], description='Retrieves summary.')
    def get(self, exchangeName, **kwargs):
        ex = exapi.exs[exchangeName]['PUBLIC']
        try:
            markets = ex.get_markets()
        except:
            markets = {}
        return markets

class CandlesResource(MethodResource):
    get_args = {**base_args, **{
        'base': fields.Str(required=False, description='Base currency code'),
        'quote': fields.Str(required=False, description='Quote currency code'),
        'interval': fields.Str(required=False,
                               validate=validate.OneOf(['1m', '3m', '5m', '15m', '30m',
                                                        '1h', '2h', '4h', '6h', '8h',
                                                        '12h', '1d', '3d', '1w', '1M']),
                               missing='1h',
                               description='The aggregation duration for each candle returned'),
        'since' : fields.Integer(required=True, description='The start time (represented by the number of milliseconds since Jan 1, 1970) for result data'),
        'limit' : fields.Integer(required=False, description='The maximum number of results to return')
    }}
    @use_kwargs(get_args)
    @use_kwargs_doc(get_args, locations=['query'])
    @doc(tags=['Unsecured'], description='Retrieves candles. Not all exchanges support this method; HTTP status 404 will be returned if unavailable.')
    def get(self, exchangeName, **kwargs):
        ex = exapi.exs[exchangeName]['PUBLIC']
        args = pruneArgs(kwargs)
        # not every class has get_candles defined
        if hasattr(ex, 'get_candles') and callable(getattr(ex, 'get_candles')):
            return ex.get_candles(**args).to_json()
        abort(404)

# ----------------------------------------------- Secured Resources

class BalancesResource(MethodResource):
    @use_kwargs(secure_args)
    @use_kwargs_doc(secure_args, locations=['query'])
    @doc(tags=['Secured'], description='Retrieves all asset balances for the authenticated user.')
    def get(self, exchangeName, **kwargs):
        ex = get_secure_ex(exchangeName, kwargs)
        return ex.get_balances(**pruneArgs(kwargs))

class TradesResource(MethodResource):
    get_args = {**secure_args, **{
        'base': fields.Str(required=False, description='Base currency code'),
        'quote': fields.Str(required=False, description='Quote currency code'),
        'limit': fields.Integer(required=False, description='The maximum number of trades to return'),
        'since': fields.Integer(required=False, description='Start time'),
    }}
    @use_kwargs(get_args)
    @use_kwargs_doc(get_args, locations=['query'])
    @doc(tags=['Secured'], description='Retrieves user trade history')
    def get(self, exchangeName, **kwargs):
        ex = get_secure_ex(exchangeName, kwargs)
        return ex.get_trades(**pruneArgs(kwargs))

class TransactionResource(MethodResource):
    get_args = {**secure_args, **{
        'limit': fields.Integer(required=False, description='The maximum number of trades to return'),
        'since': fields.Integer(required=False, description='Start time')
    }}
    @use_kwargs(get_args)
    @use_kwargs_doc(get_args, locations=['query'])
    @doc(tags=['Secured'], description='Retrieves user transaction history')
    def get(self, exchangeName, **kwargs):
        ex = get_secure_ex(exchangeName, kwargs)
        return ex.get_transactions(**pruneArgs(kwargs))

class OrderResource(MethodResource):
    get_args = {**secure_args, **{
        'base': fields.Str(required=True, description='Base currency code'),
        'quote': fields.Str(required=True, description='Quote currency code'),
    }}
    @use_kwargs(get_args)
    @use_kwargs_doc(get_args, locations=['query'])
    @doc(tags=['Secured'], description='Retrieves an order previously posted by the authenticated user (open or closed)')
    def get(self, exchangeName, **kwargs):
        ex = get_secure_ex(exchangeName, kwargs)
        try:
            return ex.get_order(**pruneArgs(kwargs))
        except Exception as e:
            if 'not exist' in str(e):
                abort(404)
            raise e
    
    delete_args = {**secure_args, **{
        'base': fields.Str(required=False, description='Base currency code'),
        'quote': fields.Str(required=False, description='Quote currency code'),
    }}
    @use_kwargs(delete_args)
    @use_kwargs_doc(delete_args, locations=['query'])
    @doc(tags=['Secured'], description='Cancel an open order (and allow the exchange to delete it if needed)')
    def delete(self, exchangeName, **kwargs):
        ex = get_secure_ex(exchangeName, kwargs)
        return ex.cancel(**pruneArgs(kwargs))

class OrdersResource(MethodResource):
    get_args = {**secure_args, **{
        'base': fields.Str(required=False, description='Base currency code'),
        'quote': fields.Str(required=False, description='Quote currency code'),
        'type' : fields.Str(required=True,
                            validate=validate.OneOf(['open']),
                            description='Type of orders to retrieve')
    }}
    @use_kwargs(get_args)
    @use_kwargs_doc(get_args, locations=['query'])
    @doc(tags=['Secured'], description='Retrieves all orders previously posted by the authenticated user with the specified type.')
    def get(self, exchangeName, type, **kwargs):
        ex = get_secure_ex(exchangeName, kwargs)
        if type == 'open':
            return ex.get_orders(**pruneArgs(kwargs))
        abort(404)
    
    post_args = {**secure_args, **{
        'side': fields.Str(required=True,
                            validate=validate.OneOf(['buy', 'sell']),
                            description='Whether to post a buy order or a sell order'),
        'amount': fields.Float(required=True,
                               description='The quantity of the currency used in the order'),
        'price': fields.Decimal(required=False,
                                description='The price required if posting a limit order; ignored for market orders'),
        'base': fields.Str(required=True, description='Base currency code'),
        'quote': fields.Str(required=True, description='Quote currency code'),
        'type': fields.Str(required=False,
                            validate=validate.OneOf(['limit', 'market']),
                            missing='limit',
                            description='Whether to post a limit order or a market order'),
    }}
    @use_kwargs(post_args)
    @use_kwargs_doc(post_args, locations=['query'])
    @doc(tags=['Secured'], description='Posts a new order to the exchange.')
    def post(self, exchangeName, **kwargs):
        ex = get_secure_ex(exchangeName, kwargs)
        log.debug(ex)
        log.debug(kwargs)
        return ex.order(**pruneArgs(kwargs))
    
class WithdrawalResource(MethodResource):
    @use_kwargs(secure_args)
    @use_kwargs_doc(secure_args, locations=['query'])
    @doc(tags=['Secured'], description='Returns whether a withdrawal is allowed for the authenticated user.')
    # change to "post" if desired
    def get(self, exchangeName, **kwargs):
        ex = get_secure_ex(exchangeName, kwargs)
        return ex.test_withdrawal(**pruneArgs(kwargs))
    
class TradeResource(MethodResource):
    @use_kwargs(secure_args)
    @use_kwargs_doc(secure_args, locations=['query'])
    @doc(tags=['Secured'], description='Returns whether trading is enabled for the authenticated user.')
    def get(self, exchangeName, **kwargs):
        ex = get_secure_ex(exchangeName, kwargs)
        return ex.test_trading_enabled(**pruneArgs(kwargs))

