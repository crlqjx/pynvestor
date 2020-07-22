import datetime as dt
import json

from requests.exceptions import HTTPError
from red_rat import logger
from red_rat.app.mongo_connector import MongoConnector
from red_rat.app.data_providers import EuronextClient, ReutersClient

mongo_connector = MongoConnector()
market_data_provider = EuronextClient()

# TODO: compute financial ratios
# TODO: TOR https://www.sylvaindurand.fr/use-tor-with-python/


@logger
def update_quotes():
    filtered_stocks = (stock for stock in market_data_provider.all_stocks if stock['mic'] in ['XPAR', 'ALXP'])
    for stock in filtered_stocks:
        logger.log.info(f'updating {stock}')
        quotes = market_data_provider.get_quotes(stock['isin'], stock['mic'], 'max')
        if quotes:
            mongo_connector.insert_documents('quotes', 'equities', quotes)
    return


@logger
def update_fundamentals():
    reuters = ReutersClient()
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
        mongo_connector.insert_documents(database_name='financials',
                                         collection_name=statement,
                                         documents=data_to_insert[statement])


def get_balance_sheet_elements(ric, period, date=None):
    query_filter = {'ric': ric, 'period': period}
    if date:
        query_filter.update({'date': date})
    balance_sheet_elems = mongo_connector.find_documents(database_name='fundamentals', collection_name='balance_sheet',
                                                         **query_filter)

    return balance_sheet_elems


def get_income_statement_elements(ric, period, date=None):
    query_filter = {'ric': ric, 'period': period}
    if date:
        query_filter.update({'date': date})
    income_statement_elems = mongo_connector.find_documents(database_name='fundamentals', collection_name='income',
                                                            **query_filter)

    return income_statement_elems


def get_cash_flow_statement_elements(ric, period, date=None):
    query_filter = {'ric': ric, 'period': period}
    if date:
        query_filter.update({'date': date})
    cash_flow_statement_elems = mongo_connector.find_documents(database_name='fundamentals',
                                                               collection_name='cash_flow', **query_filter)

    return cash_flow_statement_elems


if __name__ == '__main__':
    # update_quotes()
    update_fundamentals()
    pass
