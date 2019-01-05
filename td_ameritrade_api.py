import requests
import json
import pandas as pd
api='https://api.tdameritrade.com/v1/'
acc=

class Portfolio:
    #Local Portfolio Object
    '''
    This object is made using basic python objects and Pandas Dataframes for keeping records of current trades, past trades, and general tracking of equity.
    - It allows you to store a value for current equity based on the most recent market update, and keeps track of the available amount of cash.
    - Keep track of trades by opening and closing them in the portfolio object.
    
    This is a pretty resilient object. It handles most of data inconsistency problems:
    - Varying market data updates handles if there was no trading for a particular symbol.
    - Inconsistent trading, time is completely date based, will work just fine with long periods of inactivity.
    - Equity records and trades can be exporting by using .to_csv() on the attribute of portfolio.
    '''
    
    #Define parameters guiding the portfolio aspect of strategy
    
    def __init__(self,starting_equity):
        self.current_equity=starting_equity#starting equity is the amount of cash we start with, it is assigned accordingly
        self.available_cash=starting_equity
        self.data=pd.DataFrame(index=None,columns=['Equity','Cash'])#storage of portfolio Equity and cash
        self.trades=pd.DataFrame(columns=['Enter Price','Position','Stop Price','Price','Ticker','Entry Date','Entry Order Price',
                                          'Exit Date','Exit Order','Exit Fill','Closed Equity','Rule','Total Equity','Converted','Profit','Exit Price'],index=None)#dataframe of current trades
        self.trade_log=pd.DataFrame(columns=['Enter Price','Position','Stop Price','Price','Ticker','Entry Date','Entry Order Price',
                                             'Exit Date','Exit Order','Exit Fill','Closed Equity','Rule','Total Equity','Converted','Profit','Exit Price'],index=None)#dataframe of all past trades

    def open_trade(self,ticker,enter_price,position,stop_price,date,order_price,exit_price):#portfolio method for creating trades
        self.trades.loc[len(self.trades)]=[enter_price,position,stop_price,order_price,ticker,date,order_price,None,None,None,None,None,None,None,None,exit_price]
        self.trades=self.trades.set_index(self.trades['Ticker'].values)
        self.available_cash=self.available_cash-abs(position)#update available cash
        self.data.at[date,'Cash']=self.available_cash#record amount
    
    def close_trade(self,ticker,exit_price,date,exit_order_price,rule):#portfolio method for closing trades
        profit=(((exit_price/self.trades.loc[ticker]['Enter Price'])*self.trades.loc[ticker]['Position']-self.trades.loc[ticker]['Position']))
        self.available_cash=self.available_cash+profit+abs(self.trades.loc[ticker]['Position'])#update the amount of cash we have after closing
        self.data.at[date,'Cash']=self.available_cash#update cash amount in portfolio's dataframe for record keeping
        self.trades.at[ticker,['Exit Date','Exit Order','Exit Fill','Closed Equity','Rule','Total Equity','Profit']]=[date,exit_order_price,exit_price,self.current_equity,rule,self.current_equity,profit]
        self.trade_log.loc[len(self.trade_log)]=self.trades.loc[ticker]
        self.trades=self.trades.drop(ticker)
    
    def update_equity(self,price_data,date):#using internal functions to change the value of portfolio with the day's price data
        intersecting_tickers=price_data[price_data.index.isin(self.trades.index)].index
        self.trades.at[intersecting_tickers,'Price']=price_data.loc[intersecting_tickers]['c']
        overall_equity=self.available_cash#initiate overall equity for calculationg
        overall_equity+=(((self.trades['Position']*(self.trades['Price']/self.trades['Enter Price']))-self.trades['Position'])+self.trades['Position'].abs()).sum()#for each trade add the calculated value based on close and position
        self.current_equity=overall_equity#updete the porfolio's value
        self.data.loc[date]=[overall_equity,self.available_cash]#update the dataframe for record keeping
        self.min_cash=self.current_equity*self.cash_residue_requirement




def get_auth():#function that uses the issued 3 month refresh token to get access to the server
    r=requests.post(api+'oauth2/token',data={'grant_type':'refresh_token','refresh_token':'<RefreshToken>','client_id':'SIMPLETRADE@AMER.OAUTHAP','redirect_uri':'http://localhost'})

    authorization_token='Bearer '+json.loads(r.content)['access_token']
    return authorization_token

def get_candle(symbol,frequencyType,frequency,endDate,startDate,bearer_token):#get the data for the symbol
    query=['apikey=SIMPLETRADE@AMER.OAUTHAP',#app's key
           'frequencyType='+str(frequencyType),#minute,hour,day candles
           'frequency='+str(frequency),#granularity of candles 1,2,3,4,5,10
           'endDate='+str(endDate),#integer milliseconds from 1970-01-01 00:00:00.000
           'startDate='+str(startDate)]#integer milliseconds from 1970-01-01 00:00:00.000
    query='&'.join(query)
    
    r=requests.get(api+'/marketdata/%s/pricehistory?'%(symbol)+query,headers={'Authorization':bearer_token})
    
    #get json trying to turn into DataFrame
    print(r.content)
    candle=json.loads(r.content)['candles']
    candle=pd.io.json.json_normalize(candle,None)
    candle=pd.DataFrame(data=candle)
    candle['symbol']=symbol
    return candle

def get_equity(account_number,bearer_token):#retrieve current account value
    r=requests.get(api+'accounts/'+str(account_number),headers={'Authorization':bearer_token})
    return json.loads(r.content)["securitiesAccount"]["currentBalances"]["liquidationValue"]

def post_option_order(duration,quantity,price,symbol,putCall,instruction,quantityType,acc,bearer_token,orderType='MARKET'):
    order_data={
        "duration": duration,#"'DAY' or 'GOOD_TILL_CANCEL' or 'FILL_OR_KILL'",
        "orderType": orderType,#"'MARKET' or 'LIMIT' or 'STOP' or 'STOP_LIMIT' or 'TRAILING_STOP' or 'MARKET_ON_CLOSE' or 'EXERCISE' or 'TRAILING_STOP_LIMIT' or 'NET_DEBIT' or 'NET_CREDIT' or 'NET_ZERO'",
        "quantity": quantity,
        "price": price,
        "orderLegCollection": [
                               {
                               "orderLegType": 'OPTION',
                               "legId": '0',
                               "instrument": {
                                "assetType": 'OPTION',
                                "symbol": symbol,
                                "putCall": putCall,#"'PUT' or 'CALL'",
                                },
                               "instruction": instruction,#"'BUY' or 'SELL' or 'BUY_TO_COVER' or 'SELL_SHORT' or 'BUY_TO_OPEN' or 'BUY_TO_CLOSE' or 'SELL_TO_OPEN' or 'SELL_TO_CLOSE' or 'EXCHANGE'",
                               "quantity": quantity,
                               "quantityType": quantityType,#"'ALL_SHARES' or 'DOLLARS' or 'SHARES'"
                               }
                               ],
                            "specialInstruction": 'ALL_OR_NONE',
                            "orderStrategyType": 'SINGLE'
    }

    r=requests.post(api+'accounts/%s/orders'%acc,data=json.dumps(order_data),headers={'Authorization':bearer_token,'Content-Type': 'application/json'})
    return json.loads(r.content)

