import sys
sys.path.insert(0, '/')
from test_base import BaseTestCases, get_secure_ex

class TestBittrex(BaseTestCases.TestBase):
    
    def get_order_base(self):
            return 'BTC'
    
    def get_order_quote(self):
            return 'USDT'
        
    @classmethod
    def setUpClass(cls):
        cls.name = 'Bittrex'
        key = ''
        secret = ''
        cls.exch_a = get_secure_ex(cls.name, key, secret)
        cls.exch_b = None