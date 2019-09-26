import exapi
import logging
import time
import unittest
from pprint import pprint
from exapi.exchange import Exchange

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def addExchange(exchangeName, key, secret, passphrase=None):
    if exchangeName == 'Kraken':
        ex = exapi.Kraken(key=key, secret=secret, passphrase=passphrase)
    else:
        ex = exapi.CCXT(exchangeName, key=key, secret=secret, passphrase=passphrase)
    exapi.exs[exchangeName][key] = ex
    return ex

def get_secure_ex(exchangeName, key, secret, passphrase=None):
    if key in exapi.exs[exchangeName]:
        log.debug(f'Using cached {exchangeName} CCXT object for {key}')
        ex = exapi.exs[exchangeName][key]
    else:
        log.debug(f'Creating new {exchangeName} CCXT object for {key}')
        ex = addExchange(exchangeName, key, secret, passphrase)
    return ex

class BaseTestCases:
    
    class TestBase(unittest.TestCase):

# --------- public methods
        
        def testGetOrderBook(self):
            self.assertIsNotNone(self.exch_a.get_orderbook(base=self.get_order_base(), quote=self.get_order_quote(), limit=500),
                                 self.name + "_a get_orderbook failed")
             
        def testGetDetails(self):
            if self.exch_a.name in ['Kraken', 'Gemini']:
                self.assertIsNotNone(self.exch_a.get_details(base=self.get_order_base(), quote=self.get_order_quote()), self.name + "_a get_details failed")
            else:
                markets = self.exch_a._ccxt_query(self.exch_a, 'load_markets')
                self.assertIsNotNone(self.exch_a.get_details( markets, base=self.get_order_base(), quote=self.get_order_quote()), self.name + "_a get_details failed")
   
        def testGetHistory(self):
            self.assertIsNotNone(self.exch_a.get_history(limit=500), self.name + "_a get_history failed")

# --------- authenticated methods
            
        def testTradingEnabled(self):
            self.assertIs(self.exch_a.test_trading_enabled(), True, self.name + "_a test_trading_enabled enabled")
            if (self.exch_b is not None):
                self.assertIs(self.exch_b.test_trading_enabled(), False, self.name + "_b test_trading_enabled failed")
         
        def testWithdrawal(self):
            self.assertIs(self.exch_a.test_withdrawal(), False, self.name + "_a test_withdrawal failed")
            if (self.exch_b is not None):
                self.assertIs(self.exch_b.test_withdrawal(), True, self.name + "_b test_withdrawal enabled")
          
        def testGetBalances(self):
            balances = self.exch_a.get_balances()
            for k, v in list(balances.items()):
                if v['total'] == 0.0:
                    del balances[k]
            print(self.name + ' balances: ' + str(balances))
            self.assertIsNotNone(self.exch_a.get_balances(), self.name + "_a get_balances failed")
        
        def testPlaceOrderAndGetOrdersAndGetOrderAndCancel(self):
            ob = self.get_order_base()
            oq = self.get_order_quote()
            
            if self.exch_a.name in ['Kraken', 'Gemini']:
                details = self.exch_a.get_details(base=ob, quote=oq)
            else:
                markets = self.exch_a._ccxt_query(self.exch_a, 'load_markets')
                details = self.exch_a.get_details(markets, base=ob, quote=oq)
            
            print('---------------')
            pprint(details)
                    
            minTotal = details['min_val']
            print('Respecting minimum order total value of ' + str(minTotal))
                
            highballPrice = self.get_best_bid() * 2 
            qtyNeeded = minTotal / highballPrice
            if qtyNeeded < details['min_amt']:
                print('increasing quantity to meet min amount of ' + str(details['min_amt']))
                qtyNeeded = details['min_amt']                 
            
            highballPriceStr = str(highballPrice)
            if 'price_precision' in details:
                print('rounding highball price from ' + highballPriceStr, end='')
                highballPrice = Exchange.round(False, highballPrice, details['price_precision'])
                print(' to ' + str(highballPrice))
                
            qtyNeededStr = str(qtyNeeded)
            if 'amt_precision' in details and details['amt_precision'] is not None:
                print('rounding quantity from ' + qtyNeededStr, end='')
                qtyNeeded = Exchange.round(False, qtyNeeded, details['amt_precision'])
                print(' to ' + str(qtyNeeded))
                
# this logic is for buy order
#             total = qtyNeeded * highballPrice

#             avail = balances[oq]['available']
#             print('Available ' + oq + ' balance: ' + str(avail))
#                 
#             if avail < total:
#                 print("Couldn't test placing buy order because not enough available.")
#                 return
                
            balances = self.exch_a.get_balances()
            avail = 0
            if ob in balances:
                avail = balances[ob]['available']
                
            print('Available ' + ob + ' balance: ' + str(avail))
            if qtyNeeded > avail:
                print("Couldn't test placing sell order because not enough " + ob + " available.")
                return
                
            # orderid = '273436356'
            orderid = self.exch_a.order('sell', qtyNeeded, highballPrice, base=ob, quote=oq)
            print("Order ID " + orderid + " created")
            self.pause_if_needed()
            print("Getting all orders")
            pprint(self.exch_a.get_orders(ob, oq))
            print("Getting order ID " + orderid)
            order = self.exch_a.get_order(orderid, ob, oq)
            self.assertTrue(order['open'])
            pprint(order)
            print("Canceling order " + orderid)
            self.exch_a.cancel(orderid, ob, oq)
            self.pause_if_needed()
            order = self.exch_a.get_order(orderid, ob, oq)
            self.assertFalse(order['open'])
            # return
            
            # test cancel all of currencyPair            
            orderid = self.exch_a.order('sell', qtyNeeded, highballPrice, base=ob, quote=oq)
            print("Order ID " + orderid + " created")
            self.pause_if_needed()
            print("Getting order ID " + orderid)
            order = self.exch_a.get_order(orderid, ob, oq)
            self.assertTrue(order['open'])
            print("Canceling all orders of type " + ob + "/" + oq)
            self.exch_a.cancel(base=ob, quote=oq)
            self.pause_if_needed()
            print("Getting order ID " + orderid)
            order = self.exch_a.get_order(orderid, ob, oq)
            self.assertFalse(order['open'])
                
            # test cancel all of all currencyPairs
            orderid = self.exch_a.order('sell', qtyNeeded, highballPrice, base=ob, quote=oq)
            print("Order ID " + orderid + " created")
            self.pause_if_needed()
            print("Getting order ID " + orderid)
            order = self.exch_a.get_order(orderid, ob, oq)
            self.assertTrue(order['open'])
            print("Canceling all orders of all currency pairs")
            self.exch_a.cancel()
            self.pause_if_needed()
            print("Getting order ID " + orderid)
            order = self.exch_a.get_order(orderid, ob, oq)
            self.assertFalse(order['open'])

        # def testPlaceOrderBadKey(self):
        #     with self.assertRaises(APIKeyError) or self.assertRaises(AuthenticationError) as context:
        #         self.get_exch_a_bad().order('buy', 0.0000001, 0.000001,
        #                                     base=self.get_order_base(), quote=self.get_order_quote())
           
        # def testGetOrdersBadKey(self):
        #     with self.assertRaises(APIKeyError) or self.assertRaises(AuthenticationError) as context:
        #         self.get_exch_a_bad().get_orders(base=self.get_order_base(), quote=self.get_order_quote())
           
        # def testGetOrderBadKey(self):
        #     with self.assertRaises(APIKeyError) or self.assertRaises(AuthenticationError) as context:
        #         self.get_exch_a_bad().get_order('1', base=self.get_order_base(), quote=self.get_order_quote())
                  
        # def testCancelBadKey(self):
        #     with self.assertRaises(APIKeyError) or self.assertRaises(AuthenticationError) as context:
        #         self.get_exch_a_bad().cancel('1', base=self.get_order_base(), quote=self.get_order_quote())
#
#         def testWithdrawalBadKey(self):
#             with self.assertRaises(APIKeyError) as context:
#                  self.get_exch_a_bad().test_withdrawal()
#          
        # def testGetBalancesBadKey(self):
        #     with self.assertRaises(APIKeyError) or self.assertRaises(AuthenticationError) as context:
        #         self.get_exch_a_bad().get_balances()
# 
#         def testTradingEnabledBadKey(self):
#             with self.assertRaises(APIKeyError) as context:
#                  self.get_exch_a_bad().test_trading_enabled()

# ---------------------------------------- Manual execution; helpful methods
                
#         def testGetAllOrders(self):
#             print("Getting orders")
#             pprint(self.exch_a.get_orders(self.get_order_base(), self.get_order_quote()))
            # pprint(self.exch_a.get_order('a4ba5903e2a59dc4b1b85eae93313e39', self.get_order_base(), self.get_order_quote()))
            
#         def testCancelOrder(self):
#             self.exch_a.cancel('155351b6-5a8c-4b91-aa6f-c576af6faa45', base=self.get_order_base(), quote=self.get_order_quote())
        
# ---------------------------------------- Non-test (utility) methods
        
        def get_order_base(self):
            return 'ETH'
        
        def get_order_quote(self):
            return 'BTC'

        def pause_if_needed(self):
            if self.pause_after_operation():
                time.sleep(5)
            
        def pause_after_operation(self):
            return False
        
        def get_best_ask(self):
            orderbook = self.exch_a.get_orderbook(base=self.get_order_base(), quote=self.get_order_quote(), side='asks')
            price = orderbook['asks'][0][0]
            return price
        
        def get_best_bid(self):
            orderbook = self.exch_a.get_orderbook(base=self.get_order_base(), quote=self.get_order_quote(), side='bids')
            price = orderbook['bids'][0][0]
            return price

        exch_a_badkey = None
        
        def get_exch_a_bad(self):
            if self.exch_a_badkey is None:
                newkey = self.exch_a.key
                newkey = newkey[:-1] + ('r' if newkey[-1:] != 'r' else 's')
                self.exch_a_badkey = get_secure_ex(self.name, newkey, self.exch_a.secret, self.exch_a.passphrase)
            return self.exch_a_badkey
