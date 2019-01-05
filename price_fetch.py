from . import td_ameritrade_api
import datetime as dt
import time
import pandas as pd

token=get_auth()#authorize ourselves

market_open=int(time.mktime(dt.datetime.now().replace(hour=9,minute=30,second=0).timetuple()))#declare market open time

while dt.datetime.now().hour()<21:
    for symbol in ['UPWK','AAPL','SNAP','AIG']:
        get_candle(symbol,
                   'minute',
                   1,
                   int(time.mktime(dt.datetime.now().timetuple())),
                   market_open).to_csv('%s.csv'%symbol)
                   
else:
    quit()
