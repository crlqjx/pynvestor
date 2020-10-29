import datetime as dt
from pynvestor.source.screener import Screener

today = dt.date.today()

screener = Screener({'eps': (0, 100),
                     'per': (0, 15),
                     'roe': (0.10, 1),
                     'gearing': (0, 1),
                     'operating_margin': (0.05, 10)},
                    period='annual', as_of_date=dt.datetime(today.year, today.month, today.day))
result = screener.run()
