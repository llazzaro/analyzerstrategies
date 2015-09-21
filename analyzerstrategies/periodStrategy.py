'''
Created on Dec 25, 2011

@author: ppa
'''
from pyStock.models import Action, Order
from analyzer.backtest.tick_subscriber.strategies.base_strategy import BaseStrategy
from analyzer.backtest.constant import CONF_STRATEGY_PERIOD, CONF_INIT_CASH

import logging
LOG=logging.getLogger()


class PeriodStrategy(BaseStrategy):
    ''' period strategy '''
    def __init__(self, config_dict):
        super(PeriodStrategy, self).__init__("periodStrategy")
        self.config_dict=config_dict

        assert int(config_dict[CONF_STRATEGY_PERIOD]) >= 1

        self.per_amount=max(1, round(int(config_dict[CONF_INIT_CASH]) / 100))  # buy 1/100 per time
        self.period=int(config_dict[CONF_STRATEGY_PERIOD])
        self.symbols=None
        self.counter=0

    def increase_and_check_counter(self):
        ''' increase counter by one and check whether a period is end '''
        self.counter += 1
        self.counter %= self.period
        if not self.counter:
            return True
        else:
            return False

    def tickUpdate(self, tick_dict):
        ''' consume ticks '''
        assert self.symbols
        assert self.symbols[0] in tick_dict.keys()
        symbol=self.symbols[0]
        tick=tick_dict[symbol]

        if self.increase_and_check_counter():
            self.place_order(Order(account=self.account,
                                  action=Action.BUY,
                                  is_market=True,
                                  symbol=symbol,
                                  price=tick.close,
                                  share=self.per_amount / float(tick.close)))
