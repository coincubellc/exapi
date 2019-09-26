import sys
sys.path.insert(0, '/')
from test_base import BaseTestCases, get_secure_ex

class TestBitfinex(BaseTestCases.TestBase):
    
    def get_order_base(self):
        return 'TRX'
    
    @classmethod
    def setUpClass(cls):
        cls.name = 'Bitfinex'
        key = ''
        secret = ''
        cls.exch_a = get_secure_ex(cls.name, key, secret)
        cls.exch_b = None