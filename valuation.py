import numpy as np
import pandas as pd



class Valuation:
    def __init__(self):
        pass

    def valuate_price_2(self, ticker, roic, net_income, current_assets, liabilities, mkt_cap, years=10, base_multiplier=10):
        roic = float(roic)
        if abs(mkt_cap) < 1e-6:
            return {}
        try:
            final_value = ((1 + roic) ** years / (1 + base_multiplier / 100) ** years) * net_income * 100 / base_multiplier + current_assets - liabilities
            margin = final_value / mkt_cap if final_value >= 0 else mkt_cap / final_value
        except Exception as e:
            print(f"Error in valuation for {ticker}: {e}")
            final_value = np.nan
            margin = np.nan
        return {
            'final_value': final_value,
            'margin': margin
        }
    
    def valuate_row_2(self, row, n=0):
        # row can be a row in pandas df, or a dictionary
        assert(n >= 0 and n < 3)

        required_keys = ['Ticker', 'Market Cap History', 'Net Income', 'ROIC', 'Current Asset', 'Total Liabilities']
        for key in required_keys:
            if key not in row or len(row[key]) <= n:
                return pd.Series([np.nan, np.nan])
        
        values_to_check = ['Market Cap History', 'Net Income', 'ROIC', 'Current Asset', 'Total Liabilities']
        for key in values_to_check:
            if isinstance(row[key], list) and (not isinstance(row[key][n], (int, float)) or np.isnan(row[key][n])):
                print
                return pd.Series([np.nan, np.nan])
            
        ticker = row['Ticker']
        mkt_cap = row['Market Cap History'][n]
        net_income = row['Net Income'][n]
        roic_val = (row['ROIC'][0 + n] + row['ROIC'][1 + n]) / 2
        current_assets = row['Current Asset'][n]
        liabilities = row['Total Liabilities'][n]
        val_res = self.valuate_price_2(ticker, roic_val, net_income, current_assets, liabilities, mkt_cap)

        return pd.Series([val_res['final_value'], val_res['margin']])