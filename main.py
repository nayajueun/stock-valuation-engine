from utils import *


if __name__ == '__main__':
    filepath = 'financial_data.csv'
    print("Press Enter if you would want to go with the default.")
    country = input("Which country's stock would you like to investigate? ")
    if not country:
        country = "United States"
    sector = input("What sector are you interested in? ")
    min_cap = input("Enter minimum market cap (mil USD): ")
    if not min_cap:
        min_cap = 1000000000
    max_cap = input("Enter maximum market cap (mil USD): ")
    n = input("How many stocks do you want to see")
    if not n: n = 10
    else: n = int(n)
    # base_multiplier = float(input("Enter your required rate of return (percentage): "))

    data = load_and_filter_data(filepath, country, sector, min_cap, max_cap)
    data = data.sort_values(by=['Margin'], ascending=False)
    print(data.head(n)[['Ticker', 'Name', 'Margin']])

    median = data['Margin'].median()
    print(f"Median Margin (Filtered): {median}")

    data_all = load_csv("financial_data.csv")
    median_all = data_all['Margin'].median()
    print(f"Median Margin (All): {median_all}")

