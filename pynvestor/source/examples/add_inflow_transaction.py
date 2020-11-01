import datetime as dt

from pynvestor.source.portfolio import Portfolio
from pynvestor.models.transaction import Inflow

ptf = Portfolio()

transaction_date = dt.datetime(2020, 10, 29)
amount = 1000.0

transaction = [Inflow(transaction_date, amount).to_mongo_format()]

ptf.add_transaction(transaction)
