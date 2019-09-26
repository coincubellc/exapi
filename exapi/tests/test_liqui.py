import sys
sys.path.insert(0, '/')
from test_base import BaseTestCases, get_secure_ex

@unittest.skip("Skipping until we get credentials and get_order is implemented")
class TestLiqui(BaseTestCases.TestBase):
    
    # overriding this because liqui doesn't have a withdraw method yet available
    def testWithdrawalBadKey(self):
        pass
    
    @classmethod
    def setUpClass(cls):
        cls.name = 'Liqui'
        key = ''
        secret = ''
        cls.exch_a = get_secure_ex(cls.name, key, secret)
        cls.exch_b = None