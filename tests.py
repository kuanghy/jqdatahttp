# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@163.com>

import datetime
import functools
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

        data = api.get_price(code="300073.XSHE", unit='1m', count=100,
                             end_date='2020-09-01')
        print(data)

        data = api.get_price_period(code="300073.XSHE", unit='1m',
                                    date='2020-09-01',
                                    end_date='2020-09-01 15:00:00')
        print(data)


def test_get_trade_days():
    today = datetime.date.today()
    Date = datetime.date
    get_trade_days = jqdatahttp.get_trade_days
    assert len(get_trade_days()) > 250 * (today.year - 2015)
    assert len(get_trade_days(Date(2018, 4, 16), Date(2018, 4, 18))) == 3
    date = Date(2018, 4, 19)
    assert get_trade_days(start_date=date)[0] == date
    assert get_trade_days(end_date=date)[-1] == date
    assert get_trade_days(start_date=date, count=1) == [date]
    assert get_trade_days(start_date=date, count=3)[-1] == Date(2018, 4, 23)
    assert get_trade_days(end_date=date, count=5)[0] == Date(2018, 4, 13)


def test_is_trade_date():
    assert jqdatahttp.is_trading_day(datetime.date(2017, 12, 1))
    assert not jqdatahttp.is_trading_day(datetime.date(2017, 11, 25))
    assert jqdatahttp.is_trading_day('2022-04-01')
    assert not jqdatahttp.is_trading_day('2022-04-02')


def test_get_security_info():
    security_info1 = jqdatahttp.get_security_info("600519.XSHG")
    assert security_info1.display_name == "贵州茅台"
    assert security_info1.start_date == datetime.date(2001, 8, 27)

    security_info2 = jqdatahttp.get_security_info("000300.XSHG")
    assert security_info2.start_date == datetime.date(2005, 4, 8)
    assert security_info2.type == "index"


def test_get_all_securities():
    data = jqdatahttp.get_all_securities(['index'])
    assert len(data)

    data2 = jqdatahttp.get_all_securities(['fja', 'fjb'])
    assert len(data2)


def test_get_ticks():
    data = jqdatahttp.get_ticks('600519.XSHG', count=10,
                                end_dt='2021-07-07 10:21:00')
    assert allclose(data.iloc[0, 1:4], [2020.01, 2028.88, 2003.84])
    data = jqdatahttp.get_ticks('399998.XSHE', count=5,
                                end_dt='2021-07-07 10:23:00')
    assert allclose(data.iloc[0, 1:4], [1617.3189, 1639.7735, 1615.5138])


def test_convert_security():
    security_info1 = jqdatahttp.get_security_info('000001.XSHE')
    security_info2 = jqdatahttp.get_security_info('000018.XSHE')
    data = jqdatahttp.get_extras(
        'is_st',
        [security_info1, security_info2],
        start_date='2013-12-01',
        end_date='2013-12-03'
    )
    print(data)
    data2 = jqdatahttp.get_industry(security_info2)
    print(data2)
    assert len(data), len(data2)


def test_get_bars():
    data = jqdatahttp.get_bars('MA2105.XZCE', end_dt='2021-03-24',
                               count=10, unit='1d')
    dbar_fields = [
        'date', 'open', 'close', 'high', 'low', 'volume', 'money', 'paused',
        'high_limit', 'low_limit', 'open_interest', 'avg', 'pre_close',
    ]
    data = data.reindex(columns=dbar_fields)
    print(data)
    print(data.iloc[0, 1:])
    assert allclose(data.iloc[0, 1:], [
        2486.0, 2460.0, 2491.0, 2420.0, 1295422.0, 31763747440.0, 0, 2663.0,
        2361.0, 855268.0, 2451.7385, 2512.0
    ])

    mbar_fields = [
        'date', 'open', 'close', 'high', 'low', 'volume', 'money',
        'open_interest'
    ]
    data = jqdatahttp.get_bars('MA2105.XZCE', end_dt='2021-03-24',
                               count=20, unit='1m')
    data = data.reindex(columns=mbar_fields)
    print(data)
    assert allclose(data.iloc[-2, 1:], [
        2352.0, 2351.0, 2353.0, 2351.0, 2604.0, 61272120.0, 691364.0
    ])
    data = jqdatahttp.get_bars('MA2105.XZCE', end_dt='2021-03-24',
                               count=30, unit='1M')
    data = data.reindex(columns=mbar_fields[:-1])
    print(data)
    assert allclose(data.iloc[-1, 1:], [
        2466.0, 2356.0, 2682.0, 2288.0, 24901720.0, 617942268640.0
    ])

    securities = ["ZN2112P24400.XSGE", "10003205.XSHG"]
    data = jqdatahttp.get_bars(securities, unit='1d',
                               end_dt="2021-09-10 10:18:00", count=1, df=False)
    print(data)
    assert set(securities) == set(data)


def test_get_bars_period():
    data = jqdatahttp.get_bars_period(
        'SN2109.XSGE', '2021-07-06', '2021-07-06 15:30', unit='1m'
    )
    print(data)
    data = data.drop(columns='date')
    assert not (data < 0).any().any()


def test_get_fq_factor():
    params = dict(
        security='000001.XSHE', start_date='2023-06-10', end_date='2023-06-15'
    )
    data = jqdatahttp.get_fq_factor(**params)
    print(data)
    params['fq'] = "pre"
    data = jqdatahttp.get_fq_factor(**params)
    print(data)


def test_get_current_tick():
    data = jqdatahttp.get_current_tick("600519.XSHG")
    print(data)
    if jqdatahttp.is_trading_day(datetime.date.today()):
        assert len(data)


def test_get_current_ticks():
    data = jqdatahttp.get_current_ticks(["600519.XSHG", "000002.XSHE"])
    assert len(data)


def test_get_last_price():
    data = jqdatahttp.get_last_price(['000001.XSHE', '600000.XSHG'])
    print(data)
    assert sum(data.values())


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


def test_get_extras2():
    code = '000403.XSHE'
    df = jqdatahttp.get_extras(
        'is_st', code,
        end_date='2018-11-23', count=5
    )
    assert df[code].tolist() == [True, True, True, False, False]


def test_get_fundamentals():
    data = jqdatahttp.get_fundamentals(
        code='000651.XSHE', date='2019q1', table='income', count=100
    )
    print(data)


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
    assert len(data) >= len(data2)


def test_get_concept_stocks():
    print(jqdatahttp.get_concept_stocks('SC0001'))
    data = jqdatahttp.get_concept_stocks('SC0084', date='2019-04-16')
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
    data = jqdatahttp.get_index_weights("000001.XSHG", date="2018-05-09")
    print(data)
    assert allclose(
        data.loc[
            ['600000.XSHG', '600128.XSHG', '600933.XSHG', '603888.XSHG'],
            'weight'
        ],
        [1.074, 0.007, 0.035, 0.035]
    )


def test_get_industry():
    data = jqdatahttp.get_industry(['000001.XSHE', '000002.XSHE'])
    print(data)
    assert isinstance(data, dict)


def test_get_fund_info():
    data = jqdatahttp.get_fund_info('519223.OF', date='2018-12-01')
    print(data)
    assert isinstance(data, dict)


def test_get_call_auction():
    start_date = '2022-01-10'
    end_date = '2022-01-12'
    get_call_auction = functools.partial(
        jqdatahttp.get_call_auction,
        start_date=start_date,
        end_date=end_date,
        fields=['code', 'time', 'current', 'volume', 'money']
    )

    data = get_call_auction("000001.XSHE")
    print(data)
    assert len(data) > 1
    assert "a1_v" not in data.columns

    securities = jqdatahttp.get_all_securities("stock", start_date)
    securities = securities.index.tolist()
    data = get_call_auction(securities[:18])
    assert len(set(data.code)) == 18

    data = get_call_auction(securities[:118])
    assert len(set(data.code)) == 118

    data = get_call_auction(securities[:234])
    print(data)
    assert len(data) > 500
