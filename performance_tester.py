from valuation import Valuation
from utils import *
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

class PerformanceTester():
    def __init__(self) -> None:
        self.valuation = Valuation()
        self.last_refresh_date = get_last_refresh_date()

    
    
    def test_performance(self, amount_per_share, include_dividends=True):
        df = load_csv('financial_data.csv')
        benchmark_stock_history = df.iloc[-1]['Stock Price']
        this_time = self.last_refresh_date - timedelta(days=365 * 2)

        with open('simulation_results.csv', 'a') as file:
            file.write("Simulation Run, Initial Amount, Final Amount, Initial Benchmark, Final Benchmark, Return on Stocks, Return on Benchmark, Beat Market By\n")

            for i in range(2, 0, -1):

                df[['Final Value', 'Margin']] = df.apply(lambda row, i=i: self.valuation.valuate_row_2(row, n=i), axis=1)
                df = df[df['Country'] == 'United States'] 
                df = df[df['Market Cap'] >= 1000000000]
                df = df.sort_values(by=['Margin'], ascending=False)
                print(f"simulation run at: {this_time}")
                print(df.head(10))

                shortlisted_stokcs = df.head(10)
                total_initial_amount = 0
                total_final_amount = 0
                
                for _, row in shortlisted_stokcs.iterrows():
                    initial_stock_price = row['Stock Price'][i]
                    end_stock_price = row['Stock Price'][i - 1]
                    nb_shares = amount_per_share // initial_stock_price

                    inital_amount = nb_shares * initial_stock_price
                    final_amount = nb_shares * end_stock_price

                    if include_dividends:
                        if not np.isnan(row['Dividends'][i]):
                            final_amount += row['Dividends'][i]

                    total_initial_amount += inital_amount
                    total_final_amount += final_amount
                
                initial_benchmark_price = benchmark_stock_history[i]
                final_benchmark_price = benchmark_stock_history[i - 1]

                print(benchmark_stock_history)
                
                return_on_stock = (total_final_amount - total_initial_amount) * 100 / total_initial_amount
                return_benchmark = (final_benchmark_price - initial_benchmark_price) * 100 / initial_benchmark_price
                this_time += timedelta(days=365)
                print(f"Results after one year on {this_time.strftime('%Y-%m-%d')}:")
                print(f"  - Return on Stocks: {return_on_stock:.2f}%")
                print(f"  - Benchmark Return: {return_benchmark:.2f}%")
                print(f"  - Beat the Market By: {return_on_stock - return_benchmark:.2f}%\n")

                file.write(f"{this_time.strftime('%Y-%m-%d %H:%M:%S')}, {total_initial_amount}, {total_final_amount}, {initial_benchmark_price}, {final_benchmark_price}, {return_on_stock:.2f}, {return_benchmark:.2f}, {return_on_stock - return_benchmark:.2f}\n")


            
if __name__ == '__main__':
    tester = PerformanceTester()
    tester.test_performance(amount_per_share=10000)