
from freqtrade.strategy.hyper import DecimalParameter

from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
# --------------------------------

import talib.abstract as taa
import talib
import ta
from functools import reduce


###########################################################################################################
##                Dracula by 6h057                                                                       ##
##                                                                                                       ##
##    Strategy for Freqtrade https://github.com/freqtrade/freqtrade                                      ##
##                                                                                                       ##
###########################################################################################################
##               GENERAL RECOMMENDATIONS                                                                 ##
##                                                                                                       ##
##   For optimal performance, suggested to use between 1  open trade, with unlimited stake.              ##
##   A pairlist with  80 pairs. Volume pairlist works well.                                              ##
##   Prefer stable coin (USDT, BUSDT etc) pairs, instead of BTC or ETH pairs.                            ##
##   Highly recommended to blacklist leveraged tokens (*BULL, *BEAR, *UP, *DOWN etc).                    ##
##   Ensure that you don't override any variables in you config.json. Especially                         ##
##   the timeframe (must be 1m).                                                                         ##
##                                                                                                       ##
###########################################################################################################
###########################################################################################################
##               DONATIONS                                                                               ##
##                                                                                                       ##
##                                                                                                       ##
###########################################################################################################

class Dracula(IStrategy):

    # Buy hyperspace params:
    buy_params = {
        "buy_bbt": 0.035,
    }

    # Sell hyperspace params:
    sell_params = {
    }
    # ROI table:
    minimal_roi = {
        "0": 10
    }

    info_timeframe = "5m"
    # Stoploss:
    stoploss = -0.2
    min_lost = -0.005

    buy_bbt = DecimalParameter(
        0, 100, decimals=4, default=0.023, space='buy')

    # Buy hypers
    timeframe = '1m'
    
    # Trailing stoploss (not used)
    trailing_stop = False
    trailing_only_offset_is_reached = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.1
    custom_info = {}
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe['bb_bbh_i'] = ta.volatility.bollinger_hband_indicator(close=dataframe["high"], window=20)
        dataframe['bb_bbl_i'] = ta.volatility.bollinger_lband_indicator(close=dataframe["low"], window=20)
        dataframe['bb_bbh'] = ta.volatility.bollinger_hband(close=dataframe["close"], window=20)
        dataframe['bb_bbl'] = ta.volatility.bollinger_lband(close=dataframe["close"], window=20)
        dataframe['bb_bbt'] = (dataframe['bb_bbh'] - dataframe['bb_bbl']) / dataframe['bb_bbh']

        dataframe['ema'] = taa.EMA(dataframe, timeperiod=150)
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []

        conditions.append(dataframe['volume'] > 0)
        conditions.append(dataframe['bb_bbl_i'].shift(1) == 1)
        conditions.append(dataframe['ema'].shift(1) < dataframe['close'].shift(1))
        conditions.append((dataframe['open'] < dataframe['close']))
        conditions.append((dataframe['bb_bbt'] > self.buy_bbt.value))

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'buy'] = 1

        
        return dataframe


    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        item_sell_logic = []
        item_sell_logic.append(dataframe['bb_bbh_i'].shift(1) == 1)
        item_sell_logic.append(dataframe['close'] < dataframe['open'])
        item_sell_logic.append(dataframe['volume'] > 0)
        conditions.append(reduce(lambda x, y: x & y, item_sell_logic))
        item_sell_logic = []
        item_sell_logic.append(dataframe['close'] < dataframe['open'])
        item_sell_logic.append(dataframe['ema'] > (dataframe['close'] * 1.07))
        item_sell_logic.append(dataframe['volume'] > 0)
        conditions.append(reduce(lambda x, y: x & y, item_sell_logic))
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'sell'] = 1

        return dataframe