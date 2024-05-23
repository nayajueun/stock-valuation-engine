from valuation import Valuation
import os
import numpy as np
import yfinance as yf
import json
import pickle as pkl

# Load data
from loader import Loader
import pandas as pd
from utils import *
from datetime import datetime, timedelta, timezone

# Load data

class DataUpdater:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.financial_data = {
            'Ticker': [],
            'Name': [],
            'Country': [],
            'Financial Currency': [],
            'Sector Key': [],
            'Industry Key': [],
            'Market Cap': [],
            'Market Cap History': [],
            'Stock Price': [],
            'Dividends': [],
            'Current Asset': [],
            'Non Current Asset': [],
            'Total Liabilities': [],
            'Net Income': [],
            'ROIC': []
        }
        self.batch_size = 20


    def extract_data(self, sheet, sheet_cols, years, res):
        for col in sheet.columns:
            y = col.year
            if y not in years:
                continue
            idx = years.index(y)
            sheet_col = sheet[col]
            for interested in sheet_cols:
                res[interested][idx] = sheet_col.get(interested, np.nan)
        return res
    

    def get_trailing_data_from_bs_is(self, balance_sheet, income_stmt, 
                                     balance_sheet_cols=['Total Liabilities Net Minority Interest', 'Total Non Current Assets', 'Current Assets', 'Invested Capital'], 
                                     income_stmt_cols=['Net Income', 'EBIT', 'Tax Provision', 'Pretax Income']):
        all_cols = balance_sheet_cols + income_stmt_cols + ['ROIC']
        res = {key: [np.nan for _ in range(4)]  for key in all_cols}

        if balance_sheet.empty or income_stmt.empty:
            return {}
        
        recent_year = balance_sheet.iloc[:, 0].name.year
        curr_year = datetime.now().year
        if abs(curr_year - recent_year) > 1:  # if data is too outdated
            return {}

        years = [recent_year - i for i in range(4)]

        # Extract data for balance sheet
        res = self.extract_data(balance_sheet, balance_sheet_cols, years, res)
        
        # Extract data for income statement
        res = self.extract_data(income_stmt, income_stmt_cols, years, res)

        ebit = res['EBIT']
        tax_provision = res['Tax Provision']
        pretax_income = res['Pretax Income']
        invested_capital = res['Invested Capital']

        for i in range(len(years)):
            if np.isnan(ebit[i]) or np.isnan(tax_provision[i]) or np.isnan(pretax_income[i]) or np.isnan(invested_capital[i]) or pretax_income[i] <= 1e-6 or invested_capital[i] <= 1e-6:
                continue
            else:
                roic_value = ebit[i] * (1 - tax_provision[i] / pretax_income[i]) / invested_capital[i]
                res['ROIC'][i] = roic_value

        title_mapping = {
            'Total Liabilities Net Minority Interest': 'Total Liabilities',
            'Total Non Current Assets': 'Non Current Asset',
            'Current Assets': 'Current Asset'
        }

        # Apply the mapping to the data
        renamed_data = {title_mapping.get(old_title, old_title): values for old_title, values in res.items()}
        return renamed_data

    

    def get_trailing_data_from_info_hist(self, stock, trailing_years=4):
        today = datetime.now().date()

        dates = [today - timedelta(days=i * 365) for i in range(4)]

        
        data = {key: [np.nan for _ in range(trailing_years)] for key in ['Market Cap History', 'Stock Price', 'Dividends']}
        data['Market Cap History'][0] = stock.info.get('marketCap', np.nan)
        shares_outstanding = stock.info.get('sharesOutstanding', np.nan)
        dividends = stock.dividends.tz_convert(None)
        
        for i, date in enumerate(dates):
            start_date = date - timedelta(days=5)
            end_date = date + timedelta(days=5)
            stock_data = stock.history(start=start_date, end=end_date)
            
            
            if not stock_data.empty:
                closest_date = min(stock_data.index, key=lambda x: abs(x.date() - date))
                closest_date_value = stock_data.loc[closest_date]

                # Market cap = Close price * Shares Outstanding
                if np.isnan(data['Market Cap History'][i]):
                    data['Market Cap History'][i] = closest_date_value['Close'] * shares_outstanding if shares_outstanding else np.nan
                data['Stock Price'][i] = closest_date_value['Close']

            if not dividends.empty:
                div_start_date = pd.Timestamp(date)
                div_end_date = pd.Timestamp(date + timedelta(days=365))
                annual_dividends = dividends.loc[div_start_date:div_end_date].sum()
                data['Dividends'][i] = annual_dividends

        return data
    
    def append_financial_data(self, ticker='N/A', name='N/A', country='N/A', financial_currency='N/A', 
                              sector_key='N/A', industry_key='N/A', market_cap='N/A', 
                              market_cap_history=None, stock_price=None, dividends=None,
                              current_asset=None, non_current_asset=None, total_liabilities=None, 
                              net_income=None, roic=None):
        
        self.financial_data['Ticker'].append(ticker)
        self.financial_data['Name'].append(name)
        self.financial_data['Country'].append(country)
        self.financial_data['Financial Currency'].append(financial_currency)
        self.financial_data['Sector Key'].append(sector_key)
        self.financial_data['Industry Key'].append(industry_key)
        self.financial_data['Market Cap'].append(market_cap)
        self.financial_data['Market Cap History'].append(market_cap_history if market_cap_history is not None else [])
        self.financial_data['Stock Price'].append(stock_price)
        self.financial_data['Dividends'].append(dividends)
        self.financial_data['Current Asset'].append(current_asset)
        self.financial_data['Non Current Asset'].append(non_current_asset)
        self.financial_data['Total Liabilities'].append(total_liabilities)
        self.financial_data['Net Income'].append(net_income)
        self.financial_data['ROIC'].append(roic)


    def fetch_and_add_company(self, ticker_symbol, trailing_years=4):

        try:
            company = yf.Ticker(ticker_symbol)
            info = company.info
            income_stmt = company.income_stmt
            balance_sheet = company.balance_sheet
            mkt_cap = info.get('marketCap', np.nan)

            if not balance_sheet.empty and not income_stmt.empty:
            # # Initialize ROIC and net income after setting up the object
            # if not income_stmt.empty and not balance_sheet.empty:
                bs_is = self.get_trailing_data_from_bs_is(balance_sheet, income_stmt)
                if 'ROIC' not in bs_is or all(np.isnan(value) for value in bs_is['ROIC']):
                    return False
                
                info_his = self.get_trailing_data_from_info_hist(company)
                self.append_financial_data(ticker=ticker_symbol,
                                           name=info.get('longName', 'N/A'),
                                           country=info.get('country', 'N/A'),
                                           financial_currency=info.get('financialCurrency', 'N/A'),
                                           sector_key=info.get('sectorKey', 'N/A'),
                                           industry_key=info.get('industryKey', 'N/A'),
                                           market_cap=info_his['Market Cap History'][0],
                                           market_cap_history=info_his['Market Cap History'],
                                           stock_price=info_his['Stock Price'],
                                           dividends=info_his['Dividends'],
                                           current_asset=bs_is['Current Asset'],
                                           non_current_asset=bs_is['Non Current Asset'],
                                           total_liabilities=bs_is['Total Liabilities'],
                                           net_income=bs_is['Net Income'],
                                           roic=bs_is['ROIC']
                                           )
                    
                return True
                
        except Exception as e:
            print(f"Error initializing Valuation for {ticker_symbol}: {e}")

        return False

    def update_last_refresh_date(self):
        with open('last_update_date.txt', 'w') as file:
            # Write the current date as a string to the file
            file.write(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))


    def update_data(self, ticker_symbols):
        print(f"{len(ticker_symbols)} companies to be added in")
        val = Valuation()
        count = 0
        for idx, stock in enumerate(ticker_symbols):
            print(stock)
            added_row = self.fetch_and_add_company(stock)
            if added_row:
                count += 1

            if count == self.batch_size:
                df = pd.DataFrame(self.financial_data)
                df[['Final Value', 'Margin']] = df.apply(lambda row: val.valuate_row_2(row), axis=1)
                print(f"Processed {idx + 1} companies, and to be saved as .csv")
                save_to_csv(df, self.csv_file_path, mode='a')
                # Reset financial_data dictionary
                self.financial_data = {key: [] for key in self.financial_data}
                count = 0
        
        if count > 0:
            sp500_stock = yf.Ticker('^GSPC')
            sp500_info_his = self.get_trailing_data_from_info_hist(sp500_stock)
            self.append_financial_data(ticker='^GSPC',
                                       name='S&P 500',
                                       stock_price=sp500_info_his['Stock Price']
                                        )
            df = pd.DataFrame(self.financial_data)
            df[['Final Value', 'Margin']] = df.apply(lambda row: val.valuate_row_2(row), axis=1)
            
            save_to_csv(df, self.csv_file_path, mode='a')
            self.update_last_refresh_date()

        print(f"Financial data has been saved to {self.csv_file_path}")
        

if __name__ == '__main__':
    loader = Loader()
    ticker_symbols_to_update = loader.load_us_stocks()
    ls = list(ticker_symbols_to_update)
    with open("all_stocks.pkl", 'wb') as f:
        pkl.dump(ls, f)

    # ls = ['AAPL']
    updater = DataUpdater("financial_data.csv")
    updater.update_data(ticker_symbols=ls)

