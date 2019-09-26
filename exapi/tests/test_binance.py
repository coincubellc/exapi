import sys
sys.path.insert(0, '/')
from test_base import BaseTestCases, get_secure_ex

class TestBinance(BaseTestCases.TestBase):
    
    # disabling this because Binance doesn't distinguish between an 
    # invalid API key and a valid key that doesn't have trading permission - CPB
    def testTradingEnabledBadKey(self):
        pass
    
    @classmethod
    def setUpClass(cls):
        cls.name = 'Binance'
        key = ''
        secret = ''
        cls.exch_a = get_secure_ex(cls.name, key, secret)
        cls.exch_b = None