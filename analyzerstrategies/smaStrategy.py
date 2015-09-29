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
import math
import logging

from pyStock.models import Action, Order
from analyzer.backtest.tick_subscriber.strategies.base_strategy import BaseStrategy
from analyzer.pyTaLib.indicator import Sma

LOG=logging.getLogger()


class SMAStrategy(BaseStrategy):

    def __init__(self, config, symbols):
        super(SMAStrategy, self).__init__("smaStrategy", symbols)
        self.config=config

        # order id
        self.stop_orderrId=None
        self.stop_orderr=None
        self.buy_order=None

        self.__smaShort=Sma(10)
        self.__smaMid=Sma(60)
        self.__smaLong=Sma(300)

        # state of privious day
        self.__previousTick=None
        self.__previousSmaShort=None
        self.__previousSmaMid=None
        self.__previousSmaLong=None

    def __buyIfMeet(self, tick, symbol):
        ''' place buy order if conditions meet '''
        # place short sell order
        if (self.__smaShort.getLastValue() < self.__smaLong.getLastValue() or self.__smaMid.getLastValue() < self.__smaLong.getLastValue()):
            if tick.close / self.__previousTick.close < 0.9:
                return

            if self.__previousSmaShort > self.__previousSmaLong and self.__smaShort.getLastValue() < self.__smaLong.getLastValue():
                # assume no commission fee for now
                self.__placeSellShortOrder(tick, symbol)

            elif self.__previousSmaLong > self.__previousSmaShort > self.__previousSmaMid and self.__smaLong.getLastValue() > self.__smaMid.getLastValue() > self.__smaShort.getLastValue():
                # assume no commission fee for now
                self.__placeSellShortOrder(tick, symbol)

        # place buy order
        if (self.__smaShort.getLastValue() > self.__smaLong.getLastValue() or self.__smaMid.getLastValue() > self.__smaLong.getLastValue()):
            if tick.close / self.__previousTick.close > 1.1:
                return

            if self.__previousSmaShort < self.__previousSmaLong and self.__smaShort.getLastValue() > self.__smaLong.getLastValue():
                # assume no commission fee for now
                self.__placeBuyOrder(tick, symbol)

            elif self.__previousSmaLong < self.__previousSmaShort < self.__previousSmaMid and self.__smaLong.getLastValue() < self.__smaMid.getLastValue() < self.__smaShort.getLastValue():
                # assume no commission fee for now
                self.__placeBuyOrder(tick, symbol)

    def __placeSellShortOrder(self, tick, symbol):
        ''' place short sell order'''
        share=math.floor(self.getAccountCopy().getCash() / float(tick.close))
        sellShortOrder=Order(accountId=self.accountId,
                                  action=Action.SELL_SHORT,
                                  is_market=True,
                                  symbol=symbol,
                                  share=share)
        if self.placeOrder(sellShortOrder):
            self.buy_order=sellShortOrder

            # place stop order
            stopOrder=Order(accountId=self.accountId,
                          action=Action.BUY_TO_COVER,
                          is_stop=True,
                          symbol=symbol,
                          price=tick.close * 1.05,
                          share=share)
            self.__placeStopOrder(stopOrder)

    def __placeBuyOrder(self, tick, symbol):
        ''' place buy order'''
        share=math.floor(self.getAccountCopy().getCash() / float(tick.close))
        buyOrder=Order(accountId=self.accountId,
                                  action=Action.BUY,
                                  is_market=True,
                                  symbol=symbol,
                                  share=share)
        if self.placeOrder(buyOrder):
            self.buy_order=buyOrder

            # place stop order
            stopOrder=Order(accountId=self.accountId,
                          action=Action.SELL,
                          is_stop=True,
                          symbol=symbol,
                          price=tick.close * 0.95,
                          share=share)
            self.__placeStopOrder(stopOrder)

    def __placeStopOrder(self, order):
        ''' place stop order '''
        orderId=self.placeOrder(order)
        if orderId:
            self.stop_orderrId=orderId
            self.stop_orderr=order
        else:
            LOG.error("Can't place stop order %s" % order)

    def __sellIfMeet(self, tick, symbol):
        ''' place sell order if conditions meet '''
        if self.stop_orderr.action == Action.BUY_TO_COVER and self.__previousSmaShort < self.__previousSmaMid and self.__previousSmaShort < self.__previousSmaLong\
                and (self.__smaShort.getLastValue() > self.__smaLong.getLastValue() or self.__smaShort.getLastValue() > self.__smaMid.getLastValue()):
            self.placeOrder(Order(accountId=self.accountId,
                                  action=Action.BUY_TO_COVER,
                                  is_market=True,
                                  symbol=symbol,
                                  share=self.stop_orderr.share))
            self.tradingEngine.cancelOrder(symbol, self.stop_orderrId)
            self.__clearStopOrder()

        elif self.stop_orderr.action == Action.SELL and self.__previousSmaShort > self.__previousSmaMid and self.__previousSmaShort > self.__previousSmaLong\
                and (self.__smaShort.getLastValue() < self.__smaLong.getLastValue() or self.__smaShort.getLastValue() < self.__smaMid.getLastValue()):
            self.placeOrder(Order(accountId=self.accountId,
                                  action=Action.SELL,
                                  is_market=True,
                                  symbol=symbol,
                                  share=self.stop_orderr.share))
            self.tradingEngine.cancelOrder(symbol, self.stop_orderrId)
            self.__clearStopOrder()

    def order_executed(self, order):
        ''' call back for executed order '''
        for orderId in order.keys():
            if orderId == self.stop_orderrId:
                LOG.debug("smaStrategy stop order canceled %s" % orderId)
                # stop order executed
                self.__clearStopOrder()
                break

    def __clearStopOrder(self):
        ''' clear stop order status '''
        self.stop_orderrId=None
        self.stop_orderr=None

    def __adjustStopOrder(self, tick, symbol):
        ''' update stop order if needed '''
        if not self.stop_orderrId:
            return

        if self.stop_orderr.action == Action.SELL:
            orgStopPrice=self.buy_order.price * 0.95
            newStopPrice=max(((tick.close + orgStopPrice) / 2), tick.close * 0.85)
            newStopPrice=min(newStopPrice, tick.close * 0.95)

            if newStopPrice > self.stop_orderr.price:
                self.tradingEngine.cancelOrder(symbol, self.stop_orderrId)
                stopOrder=Order(accountId=self.accountId,
                                  action=Action.SELL,
                                  is_stop=True,
                                  symbol=symbol,
                                  price=newStopPrice,
                                  share=self.stop_orderr.share)
                self.__placeStopOrder(stopOrder)

        elif self.stop_orderr.action == Action.BUY_TO_COVER:
            orgStopPrice=self.buy_order.price * 1.05
            newStopPrice=min(((orgStopPrice + tick.close) / 2), tick.close * 1.15)
            newStopPrice=max(newStopPrice, tick.close * 1.05)

            if newStopPrice < self.stop_orderr.price:
                self.tradingEngine.cancelOrder(symbol, self.stop_orderrId)
                stopOrder=Order(accountId=self.accountId,
                                  action=Action.BUY_TO_COVER,
                                  is_stop=True,
                                  symbol=symbol,
                                  price=newStopPrice,
                                  share=self.stop_orderr.share)
                self.__placeStopOrder(stopOrder)

    def update_previous_state(self, tick):
        ''' update privous state '''
        self.__previousTick=tick
        self.__previousSmaShort=self.__smaShort.getLastValue()
        self.__previousSmaMid=self.__smaMid.getLastValue()
        self.__previousSmaLong=self.__smaLong.getLastValue()

    def tick_update(self, tickDict):
        ''' consume ticks '''
        assert self.symbols
        assert self.symbols[0] in tickDict.keys()
        symbol=self.symbols[0]
        tick=tickDict[symbol]

        LOG.debug("tickUpdate symbol %s with tick %s, price %s" % (symbol, tick.time, tick.close))
        # update sma
        self.__smaShort(tick.close)
        self.__smaMid(tick.close)
        self.__smaLong(tick.close)

        # if not enough data, skip to reduce risk -- SKIP NEWLY IPOs
        if not self.__smaLong.getLastValue() or not self.__smaMid.getLastValue() or not self.__smaShort.getLastValue():
            self.updatePreviousState(tick)
            return

        # don't have any holdings
        if not self.stop_orderrId:
            self.__buyIfMeet(tick, symbol)

        # already have some holdings
        else:
            self.__sellIfMeet(tick, symbol)
            self.__adjustStopOrder(tick, symbol)

        self.updatePreviousState(tick)
