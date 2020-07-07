## PYNVESTOR

Tool to monitor a stock portfolio.
Prices are from Euronext

Data are stored in a MongoDB
notes about mongoDB collections:
    - net_asset_values.historical_navs: field "Date" must be set as a unique key
    - quotes.equities: fields "isin" and "time" must be set as unique keys