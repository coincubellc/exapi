import sys
sys.path.insert(0, '/')
from test_base import BaseTestCases, get_secure_ex

class TestCoinbasePro(BaseTestCases.TestBase):
    
    @classmethod
    def setUpClass(cls):
        cls.name = 'CoinbasePro'
        key = ''
        secret = ''
        passphrase = ''
        cls.exch_a = get_secure_ex(cls.name, key, secret, passphrase)
        cls.exch_b = None