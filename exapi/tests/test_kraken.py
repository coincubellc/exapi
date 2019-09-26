import sys
sys.path.insert(0, '/')
from test_base import BaseTestCases, get_secure_ex

class TestKraken(BaseTestCases.TestBase):
    
    @classmethod
    def setUpClass(cls):
        cls.name = 'Kraken'
        key = ''
        secret = ''
        cls.exch_a = get_secure_ex(cls.name, key, secret)
        cls.exch_b = None