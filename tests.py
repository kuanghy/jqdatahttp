# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@163.com>

from math import isclose
from itertools import zip_longest

import jqdatahttp
from jqdatahttp import JQDataApi


def allclose(la, lb, *, rel_tol=1e-09, abs_tol=0.0):
    for a, b in zip_longest(la, lb):
        assert isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
    return True


class TestJQDataApi(object):

    def setup_class(cls):
        api = JQDataApi()
        api.auth()
        api.auto_format_data = True
        cls.api = api

    def teardown_class(cls):
        cls.api.logout()

    def test_base(self):
        api = self.api
        print(api.get_token())

        data = api.get_security_info(code="000001.XSHE")
        print(data)

        data = api.get_index_stocks(code="000300.XSHG", date="2019-01-09")
        print(data)

        data = api.get_fundamentals(code='605388.XSHG', date='2020-08-18',
                                    count=10, table='valuation')
        print(data)


def test_get_bars():
    data = jqdatahttp.get_bars('MA2105.XZCE', end_dt='2021-03-24',
                               count=10, unit='1d')
    print(data)
    print(data.iloc[0, 1:])
    assert allclose(data.iloc[0, 1:], [
        2486.0, 2460.0, 2491.0, 2420.0, 1295422.0, 31763747440.0, 0, 2663.0,
        2361.0, 855268.0, 2451.7385, 2512.0
    ])
    data = jqdatahttp.get_bars('MA2105.XZCE', end_dt='2021-03-24',
                               count=20, unit='1m')
    print(data)
    assert allclose(data.iloc[-2, 1:], [
        2352.0, 2351.0, 2353.0, 2351.0, 2604.0, 61272120.0, 691364.0
    ])
    data = jqdatahttp.get_bars('MA2105.XZCE', end_dt='2021-03-24',
                               count=30, unit='1M')
    print(data)
    assert allclose(data.iloc[-1, 1:], [
        2466.0, 2356.0, 2682.0, 2288.0, 24901720.0, 617942268640.0
    ])


def test_get_factor_values():
    data = jqdatahttp.get_factor_values(
        '000001.XSHE,600519.XSHG',
        'net_profit_ratio,cfo_to_ev,size,EMA5,EMAC10',
        '2021-02-01',
        '2021-03-03'
    )
    print(data)

    df = data["net_profit_ratio"]
    assert df.iloc[0, 0] > 0


def test_get_last_price():
    data = jqdatahttp.get_last_price(['000001.XSHE', '600000.XSHG'])
    print(data)
    assert sum(data.values())


def test_get_extras():
    data = jqdatahttp.get_extras(
        'acc_net_value', ['510300.XSHG', '510050.XSHG'],
        start_date='2015-12-01', end_date='2015-12-03'
    )
    print(data)
    assert sum(data['510300.XSHG']) > 3

    data = jqdatahttp.get_extras(
        'is_st', ['000001.XSHE', '000018.XSHE'],
        start_date='2013-12-01', end_date='2013-12-03'
    )
    print(data)
    assert not any(data['000001.XSHE']) and all(data['000018.XSHE'])

    data = jqdatahttp.get_extras(
        'acc_net_value', ['510300.XSHG', '510050.XSHG'],
        start_date='2015-12-01', end_date='2015-12-03', df=False
    )
    print(data)
    assert isinstance(data, dict) and sum(data['510050.XSHG']) > 9


def test_get_billboard_list():
    data = jqdatahttp.get_billboard_list(
        stock_list='000009.XSHE', end_date="2021-06-10", count=1
    )
    print(data)
    assert len(data) > 1


def test_get_index_stocks():
    data = jqdatahttp.get_index_stocks('000300.XSHG')
    print(data)
    assert len(data)

    # 测试在成分股切换时逻辑是否正常
    stocks = jqdatahttp.get_index_stocks("000300.XSHG", date="2011-01-04")
    stocks2 = jqdatahttp.get_index_stocks("000300.XSHG", date="2011-01-05")
    assert len(stocks) == len(stocks2)


def test_get_industry_stocks():
    data = jqdatahttp.get_industry_stocks('I64')
    print(data)
    assert len(data)


def test_get_industries():
    data = jqdatahttp.get_industries('zjw')
    print(data)
    assert len(data) > 0

    data2 = jqdatahttp.get_industries('zjw', date="2021-06-10")
    assert len(data) > len(data2)


def test_get_concept_stocks():
    print(jqdatahttp.get_concept_stocks('GN086'))
    data = jqdatahttp.get_concept_stocks('GN036', date='2019-04-16')
    print(data)
    assert len(data) > 5


def test_get_concepts():
    data = jqdatahttp.get_concepts()
    print(data)
    assert len(data)


def test_get_money_flow():
    data = jqdatahttp.get_money_flow('000001.XSHE', '2016-02-01', '2016-03-01')
    print(data)
    assert len(data) > 10

    data = jqdatahttp.get_money_flow(
        ['000001.XSHE', '600000.XSHG'], '2010-01-01', '2010-01-30',
        ["date", "sec_code", "change_pct", "net_amount_main", "net_pct_l", "net_amount_m"]
    )
    print(data)
    assert "net_pct_m" not in data.columns


def test_get_mtss():
    data = jqdatahttp.get_mtss('000001.XSHE', '2016-01-01', '2016-04-01')
    print(data)
    assert len(data) > 0

    data = jqdatahttp.get_mtss(
        ['000001.XSHE', '600000.XSHG'], '2016-01-01', '2016-04-01',
        fields="sec_sell_value"
    )
    print(data)
    assert "date" not in data.columns


def test_get_margincash_marginsec_stocks():
    assert len(jqdatahttp.get_margincash_stocks()) > 0
    assert len(jqdatahttp.get_marginsec_stocks()) > 0


def test_get_future_contracts():
    data = sorted(jqdatahttp.get_future_contracts('IF', date="2021-06-10"))
    print(data)
    assert data == ['IF2106.CCFX', 'IF2107.CCFX', 'IF2109.CCFX', 'IF2112.CCFX']


def test_get_dominant_future():
    assert jqdatahttp.get_dominant_future('IF', date="2021-06-10") == 'IF2106.CCFX'


def test_get_index_weights():
    # get_index_weights(index_id="000001.XSHG", date="2018-05-09")
    pass
