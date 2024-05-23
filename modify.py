from update import DataUpdater
from utils import *

if __name__ == '__main__':
    df = load_csv("financial_data_copy.csv")
    ticker_symbols_to_update = df['Ticker'].tolist()

    updater = DataUpdater("financial_data.csv")
    updater.update_data(ticker_symbols_to_update) 
