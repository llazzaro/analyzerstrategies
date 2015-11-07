'''
Created on July 08, 2013

This strategy leverage 10/50/200 days Simple Moving Average(SMA) as short/mid/long term trend


When to Sell:
1 when stop order is hit
2 if the 10 < 50 or 10 < 200, place sell order

Stop order:
1 when buy order is placed, set stop order to be 5%
2 as time goes, increase stop price to be min(max(half of the profit, 85% of current price), 95% of current price)
3 never decrease limit price

When to Buy:
1 if 10 < 200 && 50 < 200, skip
2 if previous day price jump more than 10%, skip
3 if the previous day 10 < 200, and today 10 > 200, place buy order
4 if previous day 200 < 10 < 50, and today 200 < 50 < 10, place buy order
5 always place a stop order


@author: ppa
'''
import logging
import datetime

import pandas as pd
import numpy as np

from pyStock.models import Action
from analyzer.constant import (
    BUY,
    SELL_SHORT,
    SELL,
    BUY_TO_COVER,
)
from analyzer.tick_subscriber.strategies.base_strategy import BaseStrategy
from pandas_talib import SMA, SETTINGS

SETTINGS.join = False
log=logging.getLogger(__name__)


class SMAStrategy(BaseStrategy):

    def __init__(self, account, config, library):
        super(SMAStrategy, self).__init__("smaStrategy", account)
        self.config=config
        self.account = account
        self.library = library

        self.quotes = pd.DataFrame(columns=('timestamp', 'volume', 'bid', 'ask', 'last', 'high', 'low'))

    def check_buy(self, security):
        # place short sell order
        if (self.sma_short.iloc[-1] < self.sma_long.iloc[-1] or self.sma_mid.iloc[-1] < self.sma_long.iloc[-1]):

            # -2 refers to previous value
            if self.quotes.iloc[-1]['last'] / self.quotes.iloc[-2]['last'] < 0.9:
                return None

            if self.sma_short.iloc[-2] > self.sma_long.iloc[-2] and self.sma_short.iloc[-1] < self.sma_long.iloc[-1]:
                return SELL_SHORT

            elif self.sma_long.iloc[-2] > self.sma_short.iloc[-2] > self.sma_mid.iloc[-2] and self.sma_long.iloc[-1] > self.sma_mid.iloc[-1] > self.sma_short.iloc[-1]:
                return SELL_SHORT

        # place buy order
        if (self.sma_short.iloc[-1] > self.sma_long.iloc[-1] or self.sma_mid.iloc[-1] > self.sma_long.iloc[-1]):
            if self.quotes.iloc[-1]['last'] / self.quotes.iloc[-2]['last'] > 1.1:
                return None

            if self.sma_short.iloc[-2] < self.sma_long.iloc[-2]and self.sma_short.iloc[-1] > self.sma_long.iloc[-1]:
                return BUY

            elif self.sma_long.iloc[-2] < self.sma_short.iloc[-2] < self.sma_mid.iloc[-2] and self.sma_long.iloc[-1] < self.sma_mid.iloc[-1] < self.sma_short.iloc[-1]:
                return BUY

    def check_sell(self, tick, security):
        if self.stop_order.action == Action.BUY_TO_COVER and self.__previousSmaShort < self.__previousSmaMid and self.__previousSmaShort < self.__previousSmaLong\
                and (self.sma_short.iloc[-1] > self.sma_long.iloc[-1] or self.sma_short.iloc[-1] > self.sma_mid.iloc[-1]):
            return BUY_TO_COVER

        elif self.stop_orderr.action == Action.SELL and self.__previousSmaShort > self.__previousSmaMid and self.__previousSmaShort > self.__previousSmaLong\
                and (self.sma_short.iloc[-1] < self.sma_long.iloc[-1] or self.sma_short.iloc[-1] < self.sma_mid.iloc[-1]):
            return SELL

    def update(self, tick):
        security = tick['security']
        quote_time = datetime.datetime.fromtimestamp(int(tick['data']['timestamp']))
        last_price = tick['data']['last']
        log.debug("tick update security %s with tick %s, price %s" % (security.symbol, quote_time, last_price))
        # update sma

        # appending new row to df is not efficient
        data = tick['data']
        row = [quote_time, float(data['volume']), float(data['bid']), float(data['ask']), float(data['last']), float(data['high']), float(data['low'])]
        new_serie = pd.Series(row, index=['datetime', 'volume', 'bid', 'ask', 'last', 'high', 'low'])
        self.quotes = self.quotes.append(new_serie, ignore_index=True)

        self.sma_short = SMA(self.quotes, timeperiod=10, key='last')
        self.sma_mid = SMA(self.quotes, timeperiod=60, key='last')
        self.sma_long = SMA(self.quotes, timeperiod=200, key='last')

        if np.isnan(self.sma_long.iloc[-1]) or np.isnan(self.sma_mid.iloc[-1]) or np.isnan(self.sma_short.iloc[-1]):
            log.info('not enough data, skip to reduce risk')
            return None

        action = None
        if security.symbol not in self.account.holdings:
            action = self.check_buy(security)

        # already have some holdings
        else:
            action = self.check_sell(security)

        log.info('strategy action {0}'.format(action))
        return action
