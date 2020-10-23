import datetime as dt
from red_rat.app.screener import Screener

screener = Screener({'eps': (0, 100),
                     'per': (0, 15),
                     'roe': (0.10, 1),
                     'gearing': (0, 1),
                     'operating_margin': (0.05, 10)},
                    period='annual', as_of_date=dt.datetime(2020, 9, 1))
result = screener.run()
