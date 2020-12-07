import datetime as dt
from pynvestor.source import euronext
from dataclasses import dataclass
from marshmallow import Schema, fields
from marshmallow_enum import EnumField
from enum import Enum


class TransactionType(Enum):
    BUY = 'BUY'
    SELL = 'SELL'
    INFLOW = 'INFLOW'
    OUTFLOW = 'OUTFLOW'
    STOCK_DIVIDEND = 'STOCK DIVIDEND'
    STOCK_SPLIT = 'STOCK SPLIT'


@dataclass
class Transaction:
    transaction_date: dt.datetime = None
    transaction_type: TransactionType = None
    isin: str = None
    mic: str = None
    name: str = None
    quantity: float = None
    price: float = None
    gross_amount: float = None
    fee: float = None
    transaction_tax: float = None
    net_cashflow: float = None
    notes: str = None

    def _get_name(self):
        return euronext.get_instrument_details(self.isin, self.mic)['instr']['longNm']

    def _get_gross_value(self):
        return round(self.price * self.quantity, 4)

    def to_mongo_format(self):
        result = TransactionSchema().dump(self)
        return result


class Buy(Transaction):
    def __init__(self, transaction_date: dt.datetime, isin: str, mic: str, quantity: float, price: float, fee: float,
                 notes: str = None, has_transaction_tax: bool = True):
        self.transaction_type = TransactionType.BUY
        self.transaction_date = transaction_date
        self.isin = isin.strip()
        self.quantity = quantity
        self.mic = mic
        self.price = price
        self.fee = fee
        self.name = self._get_name()
        self.gross_amount = self._get_gross_value()
        self._has_transaction_tax = has_transaction_tax
        self.transaction_tax = self._get_transaction_tax()
        self.net_cashflow = self._get_net_cashflow()
        self.notes = notes

    def _get_transaction_tax(self):
        if self._has_transaction_tax is True:
            transaction_tax = 0.003 * self.gross_amount
        else:
            transaction_tax = 0.0

        return round(transaction_tax, 4)

    def _get_net_cashflow(self):
        net_cashflow = -(self.gross_amount + self.transaction_tax + self.fee)
        return round(net_cashflow, 4)


class Sell(Transaction):
    def __init__(self, transaction_date: dt.datetime, isin: str, mic: str, quantity: float, price: float, fee: float,
                 notes: str = None):
        assert quantity < 0, "quantity must be negative"
        self.transaction_type = TransactionType.SELL
        self.transaction_date = transaction_date
        self.isin = isin.strip()
        self.quantity = quantity
        self.mic = mic.strip()
        self.price = price
        self.fee = fee
        self.name = self._get_name()
        self.gross_amount = self._get_gross_value()
        self.net_cashflow = self._get_net_cashflow()
        self.notes = notes

    def _get_net_cashflow(self):
        net_cashflow = -self.gross_amount - self.fee
        return round(net_cashflow, 4)


class Inflow(Transaction):
    def __init__(self, transaction_date: dt.datetime, amount: float):
        self.transaction_date = transaction_date
        self.transaction_type = TransactionType.INFLOW
        self.name = 'Bank'
        self.net_cashflow = amount


class StockDividend(Transaction):
    def __init__(self, transaction_date: dt.datetime, isin: str, mic: str, net_amount, notes: str = None):
        self.transaction_type = TransactionType.STOCK_DIVIDEND
        self.transaction_date = transaction_date
        self.isin = isin.strip()
        self.mic = mic.strip()
        self.net_cashflow = net_amount
        self.notes = notes


class StockSplit(Transaction):
    def __init__(self, transaction_date: dt.datetime, isin: str, mic: str, new_quantity, notes: str = None):
        self.transaction_type = TransactionType.STOCK_DIVIDEND
        self.transaction_date = transaction_date
        self.isin = isin.strip()
        self.mic = mic.strip()
        self.quantity = new_quantity
        self.notes = notes


class TransactionSchema(Schema):
    transaction_date = fields.Function(lambda obj: obj.transaction_date)  # Keep datetime format
    transaction_type = EnumField(TransactionType, dump_by=EnumField.VALUE)
    order = fields.Str()
    isin = fields.Str()
    mic = fields.Str()
    name = fields.Str()
    quantity = fields.Float()
    price = fields.Float()
    gross_amount = fields.Float()
    fee = fields.Float()
    transaction_tax = fields.Float()
    net_cashflow = fields.Float()
    notes = fields.Str()
