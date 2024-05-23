from pytickersymbols import PyTickerSymbols
from valuation import Valuation
import pandas as pd
from yahoo_fin import stock_info as si
from pytickersymbols import PyTickerSymbols

class Loader:
    def __init__(self):
        pass

    def load_us_stocks(self, sp500=True, nasdaq=True, dow=True, others=True):
        
        stock_data = PyTickerSymbols()
        stock_set = set()
        # gather stock symbols from major US exchanges
        if sp500:
            sp500_stocks = stock_data.get_stocks_by_index('S&P 500')
            sp500_tickers = [stock['symbol'] for stock in sp500_stocks if 'symbol' in stock]
            stock_set = stock_set.union(set(sp500_tickers))

        if nasdaq:
            nasdaq_stocks = stock_data.get_stocks_by_index('NASDAQ 100')
            nasdaq_tickers = [stock['symbol'] for stock in nasdaq_stocks if 'symbol' in stock]
            stock_set = stock_set.union(set(nasdaq_tickers))

        if dow:
            dow_stocks = stock_data.get_stocks_by_index('DOW JONES')
            dow_tickers = [stock['symbol'] for stock in dow_stocks if 'symbol' in stock]
            stock_set = stock_set.union(set(dow_tickers))

        if others:
            other_tickers = si.tickers_other()
            stock_set = stock_set.union(set(other_tickers))
            
        my_list = ['W', 'R', 'P', 'Q']
        del_set = set()
        sav_set = set()

        for symbol in stock_set:
            if len( symbol ) > 4 and symbol[-1] in my_list:
                del_set.add( symbol )
            else:
                sav_set.add( symbol )

        print( f'Removed {len( del_set )} unqualified stock symbols...' )
        print( f'There are {len( sav_set )} qualified stock symbols...' )
        return sav_set


    def load_allstock_KRX(self):
        krx_url = 'https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        stk_data = pd.read_html(krx_url, header=0, encoding='euc-kr')[0]
        stk_data = stk_data[['회사명', '종목코드']]
        stk_data = stk_data.rename(columns={'회사명': 'Name', '종목코드': 'Code'})
        stk_data['Code'] = stk_data['Code'].apply(lambda input: '0' * (6 - len(str(input))) + str(input) + '.KS')

        return stk_data['Code'].to_list()

