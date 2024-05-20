from valuation import Valuation
import os
import numpy as np
import yfinance as yf
import json

# Load data
from loader import Loader
import pandas as pd
from utils import *

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
            'Current Asset': [],
            'Non Current Asset': [],
            'Total Liabilities': [],
            'Net Income': [],
            'ROIC': [],
            'Final Value': [],
            'Margin': []
        }
        self.batch_size = 20


    def get_income_roic(self, balance_sheet, income_stmt, trailing_years=4):
            
        if balance_sheet.empty or income_stmt.empty:
            return {}
        
        try:
            invested_capital = balance_sheet.iloc[:, :trailing_years].loc[['Invested Capital']]
            curr_income_stmt = income_stmt.iloc[:, :trailing_years]
            table = curr_income_stmt.loc[['Net Income', 'EBIT', 'Tax Provision', 'Pretax Income']]
            print()
            table = table.transpose()
            table['Invested Capital'] = invested_capital.transpose()
            #TODO: any is not a right way to do.
            if (table['Pretax Income'] <= 1e-6).any() or (table['Invested Capital'] <= 1e-6).any():
                return {}
            
            table['ROIC'] = table['EBIT'] * (1 - table['Tax Provision'] / table['Pretax Income']) / table['Invested Capital']
            return {
                'roic': table['ROIC'].tolist(),
                'net_income': table['Net Income'].tolist()
            }
        
        except KeyError as e:
            print(f"Key error during ROIC calculation: {e}")
            return {'roic': [], 'net_income': []}


    def fetch_and_add_company(self, ticker_symbol, trailing_years=4):
        company = None
        info = {}
        income_stmt = pd.DataFrame()
        mkt_cap = np.nan
        balance_sheet = pd.DataFrame()
        curr_balance_sheet = None
        liabilities = np.nan
        non_current_assets = np.nan
        current_assets = np.nan
        roic = []
        net_income = []
        
        val = Valuation()

        try:
            company = yf.Ticker(ticker_symbol)
            info = company.info
            income_stmt = company.income_stmt
            balance_sheet = company.balance_sheet
            mkt_cap = info.get('marketCap', np.nan)

            if not balance_sheet.empty and not income_stmt.empty:
                curr_balance_sheet = balance_sheet.iloc[:, 0]
                liabilities = curr_balance_sheet.get('Total Liabilities Net Minority Interest', np.nan)
                non_current_assets = curr_balance_sheet.get('Total Non Current Assets', np.nan)
                current_assets = curr_balance_sheet.get('Current Assets', np.nan)
            
            # # Initialize ROIC and net income after setting up the object
            # if not income_stmt.empty and not balance_sheet.empty:
                roic_result = self.get_income_roic(balance_sheet, income_stmt, trailing_years)
                if roic_result:
                    roic = roic_result.get('roic', [])
                    net_income = roic_result.get('net_income', [])
                    
                    if roic and net_income:
                        self.financial_data['Ticker'].append(ticker_symbol)
                        self.financial_data['Name'].append(info.get('longName', 'N/A'))
                        self.financial_data['Country'].append(info.get('country', 'N/A'))
                        self.financial_data['Financial Currency'].append(info.get('financialCurrency', 'N/A'))
                        self.financial_data['Sector Key'].append(info.get('sectorKey', 'N/A'))
                        self.financial_data['Industry Key'].append(info.get('industryKey', 'N/A'))
                        self.financial_data['Market Cap'].append(mkt_cap)
                        self.financial_data['Current Asset'].append(current_assets)
                        self.financial_data['Non Current Asset'].append(non_current_assets)
                        self.financial_data['Total Liabilities'].append(liabilities)
                        self.financial_data['Net Income'].append(net_income)
                        self.financial_data['ROIC'].append(roic)

                        print(roic)
                        roic_val = roic[0] if len(roic) == 1 else (roic[0] + roic[1]) / 2
                        val_res = val.valuate_price_2(ticker=ticker_symbol,
                                                        roic=roic_val, 
                                                        net_income=net_income[0],
                                                        current_assets=current_assets,
                                                        liabilities=liabilities,
                                                        mkt_cap=mkt_cap
                                                        )
                        self.financial_data['Final Value'].append(val_res['final_value'])
                        self.financial_data['Margin'].append(val_res['margin'])

                        return True
                    
        except Exception as e:
            print(f"Error initializing Valuation for {ticker_symbol}: {e}")

        return False


    def update_data(self, ticker_symbols):
        print(f"{len(ticker_symbols)} companies to be added in")
        count = 0
        for idx, stock in enumerate(ticker_symbols):
            print(stock)
            added_row = self.fetch_and_add_company(stock)
            if added_row:
                count += 1

            if count == self.batch_size:
                print(f"Processed {idx + 1} companies, and to be saved as .csv")
                save_to_csv(self.financial_data, self.csv_file_path, mode='a')
                # Reset financial_data dictionary
                self.financial_data = {key: [] for key in self.financial_data}
                count = 0
        
        if count > 0:
            save_to_csv(self.financial_data, self.csv_file_path, mode='a')

        print(f"Financial data has been saved to {self.csv_file_path}")
        

if __name__ == '__main__':
    loader = Loader()
    ticker_symbols_to_update = loader.load_us_stocks(others=False)
    # ticker_symbols_to_update = ['AAPL']

    updater = DataUpdater("financial_data_test.csv")
    updater.update_data(ticker_symbols_to_update) 
