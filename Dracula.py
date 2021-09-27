
from freqtrade.strategy.hyper import CategoricalParameter, DecimalParameter

from numpy.lib import math
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame, Series
# --------------------------------

# Add your lib to import here
# import talib.abstract as ta
import pandas as pd
import talib.abstract as taa
import ta
from functools import reduce
import numpy as np


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
##   the timeframe (should be 5m).                                                                         ##
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
        "buy_rsi_protection_rsi_max": 30,
        "buy_btc_lost_protection": True,
        "buy_use_bb": True,
    }

    # Sell hyperspace params:
    sell_params = {
        "sell_rsi_limit": 70,
    }
    # ROI table:
    minimal_roi = {
        "0": 10
    }

    info_timeframe = "5m"
    # Stoploss:
    stoploss = -0.2
    min_lost = -0.005

    buy_btc_lost_protection = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    buy_rsi_protection = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    buy_rsi_protection_rsi_max = DecimalParameter(
        0, 100, decimals=4, default=80, space='buy')

    sell_with_rsi = CategoricalParameter([True, False], default=True, space='sell', optimize=False, load=True)
    sell_rsi_limit = DecimalParameter(
        0, 100, decimals=4, default=80, space='sell')
    # Buy hypers
    timeframe = '1m'
    
    # Trailing stoploss (not used)
    trailing_stop = False
    trailing_only_offset_is_reached = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.1
    custom_info = {}

    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe['bb_bbh_i'] = ta.volatility.bollinger_hband_indicator(close=dataframe["close"], window=15)
        dataframe['bb_bbl_i'] = ta.volatility.bollinger_lband_indicator(close=dataframe["close"], window=15)
        dataframe['bb_bbh'] = ta.volatility.bollinger_hband(close=dataframe["close"], window=15)
        dataframe['bb_bbl'] = ta.volatility.bollinger_lband(close=dataframe["close"], window=15)
        dataframe['bb_bbt'] = (dataframe['bb_bbh'] - dataframe['bb_bbl']) / dataframe['bb_bbh']
        dataframe['rsi'] = taa.RSI(dataframe, timeperiod=14)

        dataframe['healthy'] = dataframe['close']  > dataframe['close'].shift(120)
        btc_info_tf = self.dp.get_pair_dataframe("BTC/BUSD", timeframe=self.timeframe)
        dataframe['btc_open'] = btc_info_tf['open']
        dataframe['btc_close'] = btc_info_tf['close']
        btc_info_tf['rsi'] = taa.RSI(btc_info_tf, timeperiod=14)
        btc_shift = btc_info_tf['close'].shift(2)
        dataframe['btc_lost'] = (btc_info_tf['close'] - btc_shift) / pd.concat([btc_shift, btc_info_tf['close']]).max(level=0)
        dataframe['btc_healthy'] = (dataframe['btc_lost'] > self.min_lost)
        
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []

        conditions.append(dataframe['volume'] > 0)
        conditions.append(dataframe['bb_bbl_i'].shift(1) == 1)
        conditions.append((dataframe['open'] < dataframe['close']))
        conditions.append((dataframe['close'] - dataframe['open']) > ((dataframe['open'].shift(1) - dataframe['close'].shift(1)) * 0.7))
        conditions.append((dataframe['bb_bbt'] > 0.02))
        # if not last_candle['healthy']: 
        #     conditions.append(dataframe["rsi"] < 25)
        #conditions.append(dataframe['bb_bbh_i'].rolling(min_periods=1, window=5).sum() > 1)
        # if self.buy_rsi_protection.value:
        #     conditions.append(dataframe["rsi"] < self.buy_rsi_protection_rsi_max.value)
        if self.buy_btc_lost_protection.value:
            conditions.append((dataframe['btc_open'] < dataframe['btc_close']))

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'buy'] = 1

        
        return dataframe


    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        item_sell_logic = []
        item_sell_logic.append(dataframe['bb_bbh_i'].shift(1) == 1)
        #item_sell_logic.append(dataframe['bb_bbh_i'] == 0)
        #if last_candle['healthy']: 
        # item_sell_logic.append((dataframe["rsi"] >= self.sell_rsi_limit.value))
        item_sell_logic.append(dataframe['close'] < dataframe['open'])
        item_sell_logic.append(dataframe['volume'] > 0)
        conditions.append(reduce(lambda x, y: x & y, item_sell_logic))
        
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'sell'] = 1

        return dataframe