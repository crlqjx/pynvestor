import datetime as dt
from pynvestor.source.screener import Screener

screener_date = dt.datetime(2020, 11, 5)

screener = Screener({'eps': (0, 100),
                     'per': (0, 15),
                     'roe': (0.10, 1),
                     'gearing': (0, 1),
                     'operating_margin': (0.05, 10)},
                    period='annual', as_of_date=dt.datetime(screener_date.year,
                                                            screener_date.month,
                                                            screener_date.day))
result = screener.run()
