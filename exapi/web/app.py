#!/usr/bin/env python3
import sys
sys.path.insert(0, '/')
from flask import Flask
from flask_restful import Api, Resource, abort
from flask_apispec import FlaskApiSpec
from flask_cors import CORS
from webargs.flaskparser import parser
from resources import (CachedMidPriceResource, OrderBookResource, HistoryResource, Healthcheck, DetailsResource,
                       CandlesResource, BalancesResource, OrderResource, OrdersResource, WithdrawalResource,
                       MarketsResource, TradeResource, TradesResource, TransactionResource)


app = Flask(__name__)

# Suppress similar links and other garbage
app.config['ERROR_404_HELP'] = False

# Enable Cross Origin Resource Sharing for all domains on all routes
CORS(app)
api = Api(app)
docs = FlaskApiSpec(app)

resources = {
    # Unsecured
    '/<string:exchangeName>/orderbook' : OrderBookResource,
    '/<string:exchangeName>/midprice' : CachedMidPriceResource,
    '/<string:exchangeName>/history' : HistoryResource,
    '/<string:exchangeName>/details' : DetailsResource,
    '/<string:exchangeName>/candles' : CandlesResource,
    '/<string:exchangeName>/markets' : MarketsResource,
    '/health': Healthcheck,
    # Secured
    '/<string:exchangeName>/balances' : BalancesResource,
    '/<string:exchangeName>/order/<string:order_id>' : OrderResource,
    '/<string:exchangeName>/orders' : OrdersResource,
    '/<string:exchangeName>/withdrawal/test' : WithdrawalResource,
    '/<string:exchangeName>/trade/test' : TradeResource,
    '/<string:exchangeName>/trades' : TradesResource,
    '/<string:exchangeName>/transactions' : TransactionResource,
}

for key, value in resources.items():
    # Add API resources
    api.add_resource(value, key)
    # Register documentation
    docs.register(value)

# This error handler is necessary for webargs usage with Flask-RESTful.
@parser.error_handler
def handle_request_parsing_error(err, req):
    abort(422, errors=err.messages)

if __name__ == '__main__':
    print ("Starting server..")
