from valuation import Valuation
from utils import *
import yfinance as yf

class PerformanceTester():
    def __init__(self) -> None:
        self.valuation = Valuation()

    
    # TODO: WRONG at the moment. Some of the factors used in the valuation for the past valuation is based on the current value.
    def test_performance(self):
        df = load_csv('financial_data.csv')
        for i in range(2, -1, -1):
            df[['Final Value', 'Margin']] = df.apply(lambda row, i=i: self.valuation.valuate_row_2(row, n=i), axis=1)
            df = df[df['Country'] == 'United States']
            df = df[df['Market Cap'] >= 1000000000]
            df = df.sort_values(by=['Margin'], ascending=False)
            print(df.head(10))

            stocks_to_buy = df.head(10)['Ticker'].to_list()
            data = yf.download(stocks_to_buy, ).resample('YE').last()['Adj Close']
            

if __name__ == '__main__':
    tester = PerformanceTester()
    tester.test_performance()