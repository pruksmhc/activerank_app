import unittest
from feminist_api import *

class FeministAPI(unittest.TestCase):
	def test_ranking(self):
		self.assertNotEqual((None, None, None, None), get_ranking_for_company('zara'))
		self.assertNotEqual((None, None, None, None), get_ranking_for_company('facebook'))
		self.assertNotEqual((None, None, None, None), get_ranking_for_company('apple'))

if __name__ == '__main__':
    unittest.main()