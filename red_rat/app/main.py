import datetime as dt
import json

from requests.exceptions import HTTPError
from red_rat import logger
from red_rat.app import mongo, euronext, reuters


@logger
def update_stocks_quotes():
    filtered_stocks = [(stock['isin'], stock['mic'], 'max')
                       for stock in euronext.all_stocks if stock['mic'] in ['XPAR', 'ALXP']]
    all_quotes = euronext.get_quotes_multiple_stocks(filtered_stocks)
    quotes = [quote for quotes in all_quotes for quote in quotes]  # List flatten
    mongo.insert_documents('quotes', 'equities', quotes)
    return True


@logger
def update_indices_quotes():
    filtered_indices = [(stock_index['isin'], stock_index['mic'], 'max')
                        for stock_index in euronext.all_indices if stock_index['mic'] in ['XPAR', 'ALXP']]
    all_quotes = euronext.get_quotes_multiple_stocks(filtered_indices)
    quotes = [quote for quotes in all_quotes for quote in quotes]  # List flatten
    mongo.insert_documents('quotes', 'equities', quotes)
    return True


@logger
def update_fundamentals():
    with open(r"D:\Python Projects\red_rat\red_rat\static\rics.json", "r") as f:
        ric_codes = json.load(f)

    data_to_insert = {'income': [], 'balance_sheet': [], 'cash_flow': []}

    for symbol in ric_codes.values():
        if symbol is None:
            continue

        logger.log.info(f'{symbol}: Getting financials')

        try:
            financials = reuters.get_financial_data(symbol)
        except HTTPError as http_error:
            logger.log.warning(f'{symbol}: {http_error}')
            continue

        try:
            financial_statements = financials['market_data'].get('financial_statements')
            assert financial_statements is not None, 'could not find financials from reuters'
        except KeyError as key_error:
            logger.log.warning(f'{symbol}: {key_error}')
            continue
        except AssertionError as assertion_error:
            logger.log.warning(f'{symbol}: {assertion_error}')
            continue

        for statement, statement_data in financial_statements.items():
            for period, income_statements in statement_data.items():
                for report_elem, reports in income_statements.items():
                    assert isinstance(reports, list)
                    for report in reports:
                        data = {'ric': financials['ric'],
                                'period': period,
                                'date': dt.datetime.fromisoformat(report['date']),
                                'report_elem': report_elem,
                                'value': float(report['value'])}

                        data_to_insert[statement].append(data)
    for statement in data_to_insert:
        mongo.insert_documents(database_name='financials',
                               collection_name=statement,
                               documents=data_to_insert[statement])

    return True


def get_balance_sheet_elements(ric, period, date=None):
    query_filter = {'ric': ric, 'period': period}
    if date:
        query_filter.update({'date': date})
    balance_sheet_elems = mongo.find_documents(database_name='fundamentals', collection_name='balance_sheet',
                                               **query_filter)

    return balance_sheet_elems


def get_income_statement_elements(ric, period, date=None):
    query_filter = {'ric': ric, 'period': period}
    if date:
        query_filter.update({'date': date})
    income_statement_elems = mongo.find_documents(database_name='fundamentals', collection_name='income',
                                                  **query_filter)

    return income_statement_elems


def get_cash_flow_statement_elements(ric, period, date=None):
    query_filter = {'ric': ric, 'period': period}
    if date:
        query_filter.update({'date': date})
    cash_flow_statement_elems = mongo.find_documents(database_name='fundamentals',
                                                     collection_name='cash_flow', **query_filter)

    return cash_flow_statement_elems


if __name__ == '__main__':
    update_stocks_quotes()
    update_indices_quotes()
    update_fundamentals()
