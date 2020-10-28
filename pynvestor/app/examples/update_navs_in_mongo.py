import pandas as pd
import datetime as dt
from pynvestor.app import mongo
from pynvestor.app.portfolio import Portfolio

navs = list(mongo.find_documents('net_asset_values', 'net_asset_values', {'_id': 0}, sort=[("date", -1)]))

last_date = navs[0]['date']
today = dt.datetime.today()

# dates to update
dates_to_update = pd.date_range(last_date, today, freq='7D')

portfolios = [Portfolio(date).save_portfolio_nav() for date in dates_to_update]
