# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@163.com>

import math
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


def test_get_last_price():
    jqdatahttp.get_last_price(['000001.XSHE', '600000.XSHG'])
