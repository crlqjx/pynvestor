from ..source import euronext, reuters, yahoo

isin = 'FR0010397232'


def test_euronext():
    actual_get_instrument_details_result = euronext.get_instrument_details(isin)
    actual_all_stocks = euronext.all_stocks
    actual_all_indices = euronext.all_indices
    actual_get_mic_from_isin_result = euronext.get_mic_from_isin(isin)
    actual_get_exch_code_from_mic_result = euronext.get_exch_code_from_mic(actual_get_mic_from_isin_result)
    actual_get_quotes_multiple_stocks_result = euronext.get_quotes_multiple_stocks([('FR0010397232', 'ALXP', 'max'),
                                                                                    ('FR0005691656', 'XPAR', 'max')])
    assert actual_get_instrument_details_result is not None
    assert 'instr' in actual_get_instrument_details_result.keys()
    assert actual_get_instrument_details_result['instr']['longNm'].upper() == 'NOVACYT'
    assert type(actual_all_stocks) is list
    assert type(actual_all_indices) is list
    assert actual_get_mic_from_isin_result == 'ALXP'
    assert actual_get_exch_code_from_mic_result == 'XPAR'
    assert len(actual_get_quotes_multiple_stocks_result) == 2
    for elem in actual_get_quotes_multiple_stocks_result:
        assert type(elem) is list


def test_reuters():
    actual_get_financial_data_result = reuters.get_financial_data('PLVP.PA')
    actual_get_company_profile_result = reuters.get_company_profile('PLVP.PA')
    actual_get_companies_profile_result = reuters.get_companies_profile(['PLVP.PA', 'TRIA.PA'])
    assert actual_get_financial_data_result['ric'] == 'PLVP.PA'
    assert 'market_data' in actual_get_financial_data_result.keys()
    assert actual_get_company_profile_result['ric'] == 'PLVP.PA'
    assert 'market_data' in actual_get_company_profile_result.keys()
    assert actual_get_companies_profile_result[0]['ric'] == 'PLVP.PA'
    assert actual_get_companies_profile_result[1]['ric'] == 'TRIA.PA'
    assert 'market_data' in actual_get_companies_profile_result[0].keys()
    assert 'market_data' in actual_get_companies_profile_result[1].keys()


def test_yahoo():
    actual_get_info_from_isin_result = yahoo.get_info_from_isin(isin)
    actual_get_quotes_result = yahoo.get_quotes('PVL.PA')
    assert type(actual_get_info_from_isin_result) is dict
    assert actual_get_info_from_isin_result['symbol'] == 'ALNOV.PA'
    assert 'chart' in actual_get_quotes_result.keys()
