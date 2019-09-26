import sys
sys.path.insert(0, '/')
from test_base import BaseTestCases, get_secure_ex

class TestPoloniex(BaseTestCases.TestBase):
    
    @classmethod
    def setUpClass(cls):
        cls.name = 'Poloniex'
        key = ''
        secret = ''
        cls.exch_a = get_secure_ex(cls.name, key, secret)
        cls.exch_b = None