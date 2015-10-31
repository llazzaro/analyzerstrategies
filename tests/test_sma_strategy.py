import random
import unittest

from pyStock.models import (
    Exchange,
    Stock,
    Account,
    Owner,
)
from pyStock.models.money import Currency

from analyzer.backtest.constant import (
    SELL,
    BUY_TO_COVER,
)
from analyzerstrategies.sma_strategy import SMAStrategy


class TestSMAStrategy(unittest.TestCase):
    def setUp(self):
        pesos = Currency(name='Pesos', code='ARG')
        merval = Exchange(name='Merval', code='MERV', currency=pesos)
        owner = Owner(name='test user')
        self.account = Account(owner=owner)
        self.security = Stock(symbol='YPF', exchange=merval)
        self.tick = {'pattern': None, 'data': {'volume30d': '12165.08453826', 'timestamp': '1446070419', 'high': '305', 'ask': 302.7022, 'last': '302.632', 'bid': 301.0001, 'low': '294.51', 'volume': '437.07501250'}, 'type': 'message', 'security': self.security, 'channel': b'BTC'}

    def test_quotes_feeder(self):
        strategy = SMAStrategy(account=self.account, config=None, securities=[self.security], store=None)
        # not enough data to return action.
        self.assertTrue(strategy.update(self.tick) is None)
        tick = self.tick
        for i in range(0, 340):
            tick['data']['last'] = random.uniform(300, 350)
            action = strategy.update(tick)
            if action is not None:
                self.assertNotEquals(action, SELL)
                self.assertNotEquals(action, BUY_TO_COVER)
