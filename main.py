import ccxt
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time
import pandas as pd
import pandas_ta as ta
from stockstats import StockDataFrame as Sdf
import plotly.graph_objects as go
from api import *


def write_from_dict_to_json(what, file):
    # transform a dict to a json and write the json to a file
    with open(file, 'w') as f:
        f.write(json.dumps(what, indent = 4))
    print("WRITTEN")

def all_exchange():
    # To see all the exchanges available :
    return ccxt.exchanges

def show_market_graph(exchange, ticker, timeframe, limit_of_candle):

    # To analyse the candles of a ticker
    ohlcv = exchange.fetch_ohlcv(ticker, timeframe = timeframe, limit = limit_of_candle)
    
    # Create a var that will take the time of the data of the market
    # Time = []
    # for data in ohlcv:
    #     # Add 7200000 to be in my own UTC, 7200000ms = 2h
    #     time = (int(data[0]) + 7200000) / 1000
    #     Time.append(datetime.utcfromtimestamp(time).strftime('%H:%M'))

    # Graph will take the close values of the market in order 
    # to display them later
    Graph = []
    # A candle is diplay as ["time", "open", "high", "low", "close", "volume"]
    for candle in ohlcv:
        # The forth element display the "close" of the candle
        Graph.append(candle[4])

    plt.figure(figsize=(10, 7))
    plt.plot(Graph)
    plt.show()

def market_data(exchange, ticker, timeframe, limit_of_candle):
    
    ohlcv = exchange.fetch_ohlcv(ticker, timeframe = timeframe, limit = limit_of_candle)
    ohlcv = [[datetime.utcfromtimestamp(((int(candle[0]) + 7200000) / 1000)).strftime('%H:%M:%S')] + candle[1:] for candle in ohlcv]
    header = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = pd.DataFrame(ohlcv, columns = header)
    return df

def create_stock(historical_data):

    # Create StockData from historical data
    stock  = Sdf.retype(historical_data)
    return stock

def get_market_data(exchange, ticker, timeframe):

    # taking market data from API transform it into a panda dataframe
    # returnin the data under the table form accroding to the following header
    ohlcv = exchange.fetch_ohlcv(ticker, timeframe = timeframe, limit = 1)
    ohlcv = [[datetime.utcfromtimestamp(((int(candle[0]) + 7200000) / 1000)).strftime('%H:%M:%S')] + candle[1:] for candle in ohlcv]
    # Can be returned as pd database or list
    #
    # Bellow is returned as pd database :
    # header = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    # df = pd.DataFrame(ohlcv, columns = header)
    # return df
    #
    # Bellow is returned as list :
    return ohlcv

def get_market_value(exchange, ticker, timeframe):

    # returns the latest market value, as a float
    ohlcv = exchange.fetch_ohlcv(ticker, timeframe = timeframe, limit = 1)
    return ohlcv[0][4]

def get_market_open(exchange, ticker, timeframe):

    # returns the open market value of the lastest candle, as a float
    ohlcv = exchange.fetch_ohlcv(ticker, timeframe = timeframe, limit = 1)
    return ohlcv[0][1]
    
def get_ema_value(ema_length, exchange, ticker, timeframe):

    # returns the last value of the ema
    return create_stock(market_data(exchange, ticker, timeframe, int(3 * ema_length))).ta.ema(length = ema_length).iloc[-1]

def trend(exchange, ticker, timeframe):
    # returns 1 if uptrend and 0 if downtrend

    # trend var is defined as 1 by default
    trend = 1
    # diff represents if the EMA 9 is above or not the EMA 18
    diff = get_ema_value(9, exchange, ticker, timeframe) - get_ema_value(18, exchange, ticker, timeframe)

    if diff < 0:
        # diff < 0, the EMA 9 is bellow the EMA 18
        # so its a downtrend
        trend = 0

    return trend

def ema_cross(exchange, ticker, timeframe):
    # Return the value of the open of the market when the 
    # EMAs have crossed.
    
    diff = get_ema_value(9, exchange, ticker, timeframe) - get_ema_value(18, exchange, ticker, timeframe)

    # EMAs have crossed
    if diff == 0:
        open = get_market_open(exchange, ticker, timeframe)
        print("EMAs have crossed, and the open is :", open)
    else:
        print("EMAs have not crossed")
        

def long(exchange, ticker, timeframe, epsilon):
    # epsilon represents the margin of error of the market
    # because the market is mooving realy fast, sometimes the bot
    # does not manage to follow
    # therefore a margin must be used.

    # return 1 if a long can be taken and 0 if not
    # to_long equals 0 by default, for precaussion
    to_long = 0

    # market var takes the latest value of the market
    market = get_market_value(exchange, ticker, timeframe)
    # ema_9 var takes the latest value of the EMA 9
    ema_9 = get_ema_value(9, exchange, ticker, timeframe)
    # ema_18 var takes the latest value of the EMA 18
    ema_18 = get_ema_value(18, exchange, ticker, timeframe)
    # open takes the open of the latest candle
    open = get_market_open(exchange, ticker, timeframe)

    # verify if the market is in a uptrend
    if trend(exchange, ticker, timeframe):
        # the market is in a uptrend
        # we have to wait for the signal, a retest of the EMA 9
        if market <= (ema_9 + epsilon * ema_9) and market >= (ema_9 - epsilon * ema_9) and open >= ema_9:
            # there is a retest of the EMAs and the market 
            # has open above the EMAs
            to_long = 1

    return to_long

def short(exchange, ticker, timeframe, epsilon):
    # epsilon represents the margin of error of the market
    # because the market is mooving realy fast, sometimes the bot
    # does not manage to follow
    # therefore a margin must be used.

    # return 1 if a short can be taken and 0 if not
    # to_short equals 0 by default, for precaussion
    to_short = 0

    # market var takes the latest value of the market
    market = get_market_value(exchange, ticker, timeframe)
    # ema_9 var takes the latest value of the EMA 9
    ema_9 = get_ema_value(9, exchange, ticker, timeframe)
    # ema_18 var takes the latest value of the EMA 18
    ema_18 = get_ema_value(18, exchange, ticker, timeframe)
    # open takes the open of the latest candle
    open = get_market_open(exchange, ticker, timeframe)

    # verify if the market is in a downtrend
    if not trend(exchange, ticker, timeframe):
        # the market is in a downtrend
        # we have to wait for the signal, a retest of the EMA 9
        # for now, only a retest of the EMA 9
        if market >= (ema_9 - epsilon*ema_9) and market <= (ema_9 + epsilon * ema_9) and open <= ema_9:
            # there is a retest of the EMA 9
            to_short = 1

    return to_short

def to_take_profit(exchange, ticker, timeframe):
    # This function will calculate the tp
    # thanks to the fibonacci extensions.
    # For that, we will need to have the movement
    # before the market retest the EMA 9.
    # The call will be given when there is a retest of the EMA 9.
    
    # If up trend
    if trend(exchange, ticker, timeframe):
        pass

def to_stop_loss(market, exchange, ticker, timeframe, ema_40_when_order, type_of_order):
    # the var type_of_order will specify ether its a short
    # or a long.
    # according to this var the sl will take place.
    # type_of_order = 1 => long
    # type_of_order = 0 => short
    #
    # Return 1 if the market has reached the stop loss target,
    # returns 0 if not

    # The EMA 40 will be the stop loss, if its touched,
    # the position should be closed.
    ema_40 = ema_40_when_order
    
    if type_of_order == 1:
        # then the user took a long
        if market <= ema_40:
            # market touches the EMA 40
            return 1

    if type_of_order == 0:
        # the user took a short
        if market >= ema_40:
            return 1

    return 0




def main():

    # Available functions :
    #
    # Show all exchange available on ccxt library
    # print(all_exchange())
    #
    # Show the graph of the market
    # show_market_graph(ccxt.bybit(), "BTCUSDT", "1m", 50)
    #
    # Show the market data
    # market_data(exchange, "BTC/BUSD", "5m", 40)
    #
    # Show the lastest candle of the market
    # get_market_data(exchange, ticker, timeframe)
    #
    # Show the latest value of the market
    # get_market_value(exchange, "BTC/BUSD", "15m")
    #
    # Show the latest value of the ema, lenght variable
    # get_ema_value(9, exchange, "BTC/BUSD", "5m")
    #
    # Show some data of the exchange
    # markets = exchange.load_markets()
    # print(markets)
    # write_from_dict_to_json(markets, "markets.json")


    # Connecting to my account on bybit
    # exchange = ccxt.bybit({
    #     'apiKey': api_public,
    #     'secret': api_private,
    #     'password': password
    # })
    
    # balance = exchange.fetch_balance()
    # print("Content of the account :",balance["total"]["USDT"], "USDT")

    exchange = ccxt.bybit()
    # Define which market ( which coin )
    ticker = "SOLUSDT"
    # Define the unit time
    ut = "1m"
    # define the margin of error
    epsilon = 0.0002
    while 1:
        # take for every seconde the value of the market
        market = get_market_value(exchange, ticker, ut)

        # Display if a LONG is available
        if long(exchange, ticker, ut, epsilon):
            print("LONG at :", datetime.now())
            print("Price :", market, "USDT")
            ema_40_when_order = get_ema_value(40, exchange, ticker, ut)
            print("STOP LOSS :", ema_40_when_order)

            while not to_stop_loss(market, exchange, ticker, ut, ema_40_when_order, 1):
                print("long in process...")
                time.sleep(1)
        else:
            print("NO LONG")

        # Display if a SHORT is available
        if short(exchange, ticker, ut, epsilon):            
            print("SHORT at :", datetime.now())
            print("Price :", market, "USDT")
            ema_40_when_order = get_ema_value(40, exchange, ticker, ut)
            print("STOP LOSS :", ema_40_when_order)

            while not to_stop_loss(market, exchange, ticker, ut, ema_40_when_order, 1):
                print("short in process...")
                time.sleep(1)
        else:
            print("NO SHORT")
        
        print('\n')
        # to respect the law
        time.sleep(1)

if __name__ == "__main__":
    main()