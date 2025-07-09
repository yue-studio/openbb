from openbb import obb
import pandas as pd
import argparse

def get_options_chain(symbol: str, dte: int, next_3_dte: bool = False):
    """
    Gets and processes options chain data for a given symbol.
    """
    obb.user.preferences.output_type = "dataframe"
    options = obb.derivatives.options.chains(symbol, provider="cboe")

    dtes_to_fetch = []
    if next_3_dte:
        all_dtes = sorted(options['dte'].unique())
        dtes_to_fetch = [d for d in all_dtes if d >= dte][:3]
        if not dtes_to_fetch:
            print(f"No DTEs found for {symbol} at or after {dte} DTE.")
            return
    else:
        # Filter for days to expiration (DTE)
        filtered_options = options[options['dte'] == dte]

        if filtered_options.empty:
            min_dte = options['dte'].min()
            print(f"No {dte} DTE options found for {symbol}, getting lowest dte: {min_dte}")
            dtes_to_fetch = [min_dte]
        else:
            dtes_to_fetch = [dte]

    for dte_to_fetch in dtes_to_fetch:
        options_for_dte = options[options['dte'] == dte_to_fetch]
        expiration_date = options_for_dte['expiration'].iloc[0]
        print()
        print(f"Options chain for {symbol} on {expiration_date} (DTE: {dte_to_fetch})")
        print()

        if options_for_dte.empty:
            print(f"No options found for {symbol} with DTE {dte_to_fetch}")
            continue

        underlying_price = options_for_dte['underlying_price'].iloc[0]

        # Filter for puts below the underlying price
        puts_below = options_for_dte[(options_for_dte['strike'] < underlying_price) & (options_for_dte['option_type'] == 'put')]
        puts_below_selected = puts_below.sort_values(by='strike', ascending=False).head(10)

        # Filter for calls above the underlying price
        calls_above = options_for_dte[(options_for_dte['strike'] > underlying_price) & (options_for_dte['option_type'] == 'call')]
        calls_above_selected = calls_above.sort_values(by='strike', ascending=True).head(10)

        # Filter for at-the-money options
        at_the_money = options_for_dte[options_for_dte['strike'] == underlying_price]

        # Combine the filtered options
        final_options = pd.concat([puts_below_selected, at_the_money, calls_above_selected]).sort_values(by='strike')

        # Remove unnecessary columns
        columns_to_remove = [
            'underlying_symbol', 'contract_symbol', 'expiration', 'dte', 'gamma', 'theta',
            'vega', 'rho', 'prev_close', 'change_percent', 'last_trade_time',
            'bid_size', 'ask_size', 'open', 'high', 'low', 'change', 'implied_volatility'
        ]
        final_options = final_options.drop(columns=columns_to_remove, errors='ignore')

        print(final_options.to_string(index=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get options chain data for a ticker.")
    parser.add_argument("-t", "--ticker", dest="ticker", help="Ticker symbol", default="SPX")
    parser.add_argument("-d", "--dte", dest="dte", help="Days to expiration", default=0, type=int)
    parser.add_argument("-n", "--next-3-dte", dest="next_3_dte", help="Show next 3 DTE option chains", action="store_true")
    args = parser.parse_args()
    get_options_chain(args.ticker, args.dte, args.next_3_dte)