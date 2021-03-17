# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@163.com>

from __future__ import print_function

import os
import sys
import re
import json
import datetime
import functools
from types import ModuleType
from collections import OrderedDict

try:
    from urllib.request import urlopen, Request as HTTPRequest
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request as HTTPRequest, HTTPError

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO


__version__ = '0.1.4'


class JQDataError(Exception):
    """错误基类"""


class InvalidTokenError(JQDataError):
    """Token 错误"""


class ParamsError(JQDataError):
    """参数错误"""


class JQDataApi(object):

    _DEFAULT_URL = "https://dataapi.joinquant.com/apis"

    def __init__(self, username=None, password=None, url=None, timeout=20):
        self._username = username
        self._password = password
        self.url = url or self._DEFAULT_URL
        self.timeout = timeout

        self.token = None
        self._encoding = "UTF-8"

        self.show_request_params = False  # 显示请求参数
        self.show_raw_result = False      # 显示原始的返回结果
        self.auto_format_result = False   # 自动格式化返回结果

    _INVALID_TOKEN_PATTERN = re.compile(
        r'(invalid\s+token)|(token\s+expired)|(token.*无效)|(token.*过期)|'
        r'(auth\s+failed.*认证失败)'
    )

    @property
    def username(self):
        return self._username or os.getenv("JQDATA_USERNAME")

    @property
    def password(self):
        return self._password or os.getenv("JQDATA_PASSWORD")

    def _request(self, data, show_request_body=False):
        req_body = json.dumps(data, default=str)
        if show_request_body:
            print("start show request body", "-" * 20)
            print(req_body)
            print("end show request body", "-" * 20)
        data = req_body.encode(self._encoding)
        req = HTTPRequest(self.url, data=data, method="POST")
        try:
            resp = urlopen(req, timeout=self.timeout)
        except HTTPError as ex:
            if ex.code == 504:
                err_msg = "请求超时，服务器繁忙，请稍后重试或减少查询条数"
                raise JQDataError(err_msg)
            elif ex.code == 500:
                err_msg = ("请求频率过高，每个账号每分钟最多允许请求 1800 次，"
                           "请稍后再试")
                raise JQDataError(err_msg)
            else:
                raise
        with resp:
            resp_body = resp.read()
            resp_data = resp_body.decode(self._encoding)
            if resp_data.startswith("error:"):
                err_msg = resp_data.replace("error:", "").strip()
                if re.search(self._INVALID_TOKEN_PATTERN, err_msg):
                    raise InvalidTokenError(err_msg)
                else:
                    raise JQDataError(err_msg)
            if resp.status != 200:
                raise JQDataError(resp_data)
        return resp_data

    def _request_data(self, method, **kwargs):
        req_data = {"method": method}
        if method not in {"get_token", "get_current_token"}:
            if not self.token:
                self.get_current_token()
            req_data["token"] = self.token
        show_request_params = kwargs.pop("show_request_params", False)
        request = functools.partial(
            self._request,
            show_request_body=(show_request_params or self.show_request_params)
        )
        req_data.update({
            key: val for key, val in kwargs.items() if val is not None
        })
        try:
            resp_data = request(req_data)
        except InvalidTokenError:
            req_data["token"] = self.get_current_token()
            resp_data = request(req_data)
        return resp_data

    def get_token(self, mob=None, pwd=None):
        if mob:
            self._username = mob
        if pwd:
            self._password = pwd
        data = self._request_data(
            "get_token", mob=self.username, pwd=self.password
        )
        self.token = data
        return data

    def get_current_token(self, mob=None, pwd=None):
        if mob:
            self._username = mob
        if pwd:
            self._password = pwd
        data = self._request_data(
            "get_current_token", mob=self.username, pwd=self.password
        )
        self.token = data
        return data

    def auth(self, username=None, password=None, url=None):
        if url:
            self.url = url
        self.get_current_token(mob=username, pwd=password)

    def logout(self):
        self._username = None
        self._password = None
        self.token = None

    def __getattr__(self, name):
        if name.startswith("get_") or name == "run_query":

            def wrapper(self, **kwargs):
                show_raw_result = kwargs.pop("show_raw_result", False)
                auto_format_result = kwargs.pop("auto_format_result", False)
                data = self._request_data(name, **kwargs)
                if show_raw_result or self.show_raw_result:
                    print("start show raw result", "-" * 20)
                    print(data)
                    print("end show raw result", "-" * 20)
                if not auto_format_result and not self.auto_format_result:
                    return data

                if name in {"get_query_count"}:
                    data = int(data)
                elif name in {"get_fund_info"}:
                    data = json.loads(data)
                elif name in {
                    "get_index_stocks",
                    "get_margincash_stocks",
                    "get_marginsec_stocks",
                    "get_industry_stocks",
                    "get_concept_stocks",
                    "get_trade_days",
                    "get_all_trade_days",
                }:
                    data = data.split()
                else:
                    data = _csv2df(data)
                return data

            cls = self.__class__
            wrapper.__name__ = name
            setattr(cls, name, wrapper)

        return object.__getattribute__(self, name)


api = JQDataApi()


def auth(username, password, url=None):
    """账号认证"""
    api.auth(username=username, password=password, url=url)


def logout():
    """退出账号"""
    api.logout()


def get_token(username=None, password=None):
    """获取 Token，如果指定账号密码则获取新的 Token，否则获取当前 Token"""
    if username and password:
        return api.get_token(mob=username, pwd=password)
    else:
        return api.token


def reset_token():
    """重置 Token，主要用于 Token 失效的情况"""
    return api.get_token()


def get_query_count(field=None):
    """查询当日可请求条数/剩余请求条数"""
    assert field in ["total", "spare", None], "field 参数必须为 total, spare, None 中的一个"
    return int(api.get_query_count())


def settimeout(value):
    """设置请求超时时间"""
    api.timeout = value


class _LazyModuleType(ModuleType):

    @property
    def _mod(self):
        name = super(_LazyModuleType, self).__getattribute__("__name__")
        if name not in sys.modules:
            __import__(name)
        return sys.modules[name]

    def __getattribute__(self, name):
        if name == "_mod":
            return super(_LazyModuleType, self).__getattribute__(name)

        try:
            return self._mod.__getattribute__(name)
        except AttributeError:
            return super(_LazyModuleType, self).__getattribute__(name)

    def __setattr__(self, name, value):
        self._mod.__setattr__(name, value)


np = _LazyModuleType("numpy")
pd = _LazyModuleType("pandas")


def is_string_types(obj):
    if sys.version_info[0] < 3:
        string_types = basestring
    else:
        string_types = str
    return isinstance(obj, string_types)


def is_text_type(obj):
    if sys.version_info[0] < 3:
        text_type = unicode
    else:
        text_type = str
    return isinstance(obj, text_type)


def _csv2list(data):
    """转化为 list 类型"""
    data = data.strip().split()
    if "," in data[0]:
        data = [line.split(",") for line in data]
    return data


def _csv2array(data, dtype=None, skip_header=0):
    """转换为 numpy 数组"""
    if not data:
        return np.empty((0, 0))
    if dtype and not isinstance(dtype, np.dtype):
        dtype = np.dtype(dtype)
    return np.genfromtxt(
        StringIO(data), dtype=dtype, delimiter=",", skip_header=skip_header
    )


def _csv2df(data, dtype=None):
    """转化为 pandas.DataFrame 类型"""
    if not data:
        return np.DataFrame()
    if dtype and not isinstance(dtype, np.dtype):
        dtype = np.dtype(dtype)
    try:
        return pd.read_csv(StringIO(data), dtype=dtype)
    except Exception:
        return pd.read_csv(StringIO(data))


def _date2dt(date):
    """转化 datetime.date 到 datetime.datetime 类型"""
    return datetime.datetime.combine(date, datetime.time.min)


def to_date(date):
    """转化为 datetime.date 类型"""
    if not date:
        return date
    elif is_string_types(date):
        if ':' in date:
            date = date[:10]
        try:
            return datetime.date(*map(int, date.split('-')))
        except Exception:
            pass
    elif isinstance(date, datetime.datetime):
        return date.date()
    elif isinstance(date, datetime.date):
        return date
    raise ValueError("date must be datetime.date, datetime.datetime, "
                     "pandas.Timestamp or like '2015-01-05'")


def to_datetime(dt):
    """转化为 datetime.datetime 类型"""
    if not dt:
        return dt
    elif is_string_types(dt):
        try:
            return datetime.datetime(*map(int, re.split(r"\W+", dt)))
        except Exception:
            pass
    elif isinstance(dt, datetime.datetime):
        return dt
    elif isinstance(dt, datetime.date):
        return _date2dt(dt)
    raise ValueError("dt must be datetime.date, datetime.datetime or like "
                     "'2015-01-05 12:00:00'")


def _array2date(data):
    vectorize = np.vectorize(to_date, otypes=[datetime.date])
    return vectorize(data)


def _array2datetime(data):
    vectorize = np.vectorize(to_datetime, otypes=[datetime.datetime])
    return vectorize(data)


class Security(object):
    """证券标的信息"""

    __slots__ = ('_code', '_type', '_start_date', '_end_date', '_name',
                 '_display_name', '_parent', '_sid', '_exchange',
                 '_exchange_name', '_extra')

    _EXCHANGE_MAPPING = {
        'XSHG': '上海证券交易所',
        'XSHE': '深圳证券交易所',
        'CCFX': '中国金融期货交易所',
        'XSGE': '上海期货交易所',
        'XDCE': '郑州商品交易所',
        'XZCE': '大连商品交易所',
        'XINE': '上海国际能源期货交易所',
        'OF': '场外基金',
    }

    def __init__(self, code=None, type=None, start_date=None, **kwargs):
        self._code = code or kwargs.pop("code", None)
        self._type = type or kwargs.pop("type", None)
        if start_date:
            self._start_date = to_date(start_date)
        else:
            if "start_date" in kwargs:
                self._start_date = to_date(kwargs.pop("start_date"))
            else:
                self._start_date = None

        if not (self._code and self._type and self._start_date):
            raise JQDataError(
                '实例化 Security 对象时必须提供 code, start_date, type 参数'
            )
        assert '.' in code, 'invalid security code'

        end_date = kwargs.pop("end_date", None)
        self._end_date = to_date(end_date) if end_date else None

        self._name = kwargs.pop("name", None)
        self._display_name = kwargs.pop("display_name", None)
        self._parent = kwargs.pop("parent", None)

        self._sid, self._exchange = self._code.rsplit('.', 1)
        self._exchange_name = self._EXCHANGE_MAPPING.get(self._exchange)

        self._extra = kwargs

    def __repr__(self):
        return (
            "{}(code='{}', type='{}', start_date='{}', end_date='{}', "
            "display_name='{}')"
        ).format(
            self.__class__.__name__, self._code, self._type,
            self._start_date, self._end_date,
            self._display_name
        )

    def __str__(self):
        return self._code

    @property
    def code(self):
        """证券代码，带交易所后缀，如 000001.XSHE"""
        return self._code

    @property
    def symbol(self):
        """证券代码，同 code 字段"""
        return self._code

    @property
    def sid(self):
        """证券 ID，不带交易所后缀的证券代码"""
        return self._sid

    @property
    def start_date(self):
        """上市日期"""
        return self._start_date

    @property
    def end_date(self):
        """最后一个上市日期"""
        return self._end_date

    @property
    def type(self):
        """类型"""
        return self._type

    @property
    def name(self):
        """缩写简称"""
        return self._name

    @property
    def display_name(self):
        """中文名称"""
        return self._display_name

    @property
    def parent(self):
        """分级基金的母基

        其他类型返回 None
        """
        return self._parent

    @property
    def exchange(self):
        """交易所英文简称"""
        return self._exchange

    @property
    def exchange_name(self):
        """交易所中文全称"""
        return self._exchange_name

    @property
    def extra(self):
        """其他信息"""
        self._extra

    def to_dict(self):
        info = {
            "code": self._code,
            "start_date": self._start_date,
            "end_date": self._end_date,
            "type": self._type,
            "name": self._name,
            "display_name": self._display_name,
            "security_id": self._sid,
            "exchange": self._exchange,
            "exchange_name": self._exchange_name,
            "parent": self._parent,
        }
        if self._extra:
            info["extra"] = self._extra
        return info


def get_security_info(code, date=None):
    """获取股票/基金/指数的信息"""
    assert code, "code is required"
    date = to_date(date) if date else datetime.date.today()
    data = api.get_security_info(code=code)
    data = data.strip().split()
    if len(data) < 2:
        return None
    info = dict(zip(data[0].split(","), data[1].split(",")))
    return Security(**info)


def get_all_securities(types=[], date=None):
    """获取平台支持的所有股票、基金、指数、期货信息"""
    if not types:
        types = ["stock"]
    elif is_string_types(types):
        types = [types]
    if date:
        date = to_date(date)
    securities = []
    for code in types:
        params = {"code": code}
        if date:
            params["date"] = date
        data = api.get_all_securities(**params)
        data = _csv2list(data)
        if not securities:
            securities.extend(data)
        else:
            securities.extend(data[1:])
    securities = pd.DataFrame(securities[1:], columns=securities[0])
    return securities.set_index('code')


def get_all_trade_days():
    """获取所有交易日"""
    data = _csv2array(api.get_all_trade_days(), dtype="<U16")
    return _array2date(data)


def get_trade_days(start_date=None, end_date=None, count=None):
    """获取指定日期范围内的所有交易日"""
    start_date = to_date(start_date)
    end_date = to_date(end_date)

    dates = get_all_trade_days()

    if not any([start_date, end_date, count]):
        return dates

    start_idx = dates.searchsorted(start_date) if start_date else 0
    end_idx = dates.searchsorted(end_date, side='right') if end_date else -1

    if not count and all([start_date, end_date]):
        return dates[start_idx:end_idx]
    if not end_date and all([start_date, count]):
        return dates[start_idx:(start_idx + count)]
    if not start_date and all([end_date, count]):
        return dates[(end_idx - count if end_idx > count else 0):end_idx]
    if start_date and not any([end_date, count]):
        return dates[start_idx:]
    if end_date and not any([start_date, count]):
        return dates[:end_idx]
    raise ParamsError("start_date 参数与 count 参数必须输入一个")


def normalize_code(code):
    """归一化证券代码

    如将证券代码 000001 转化为全称 000001.XSHE
    """


def _convert_security(security):
    if is_string_types(security):
        if "," in security:
            return security.split(",")
        else:
            return [security]
    elif isinstance(security, Security):
        return [security.code]
    elif isinstance(security, (list, tuple)):
        return [
            item.code if isinstance(item, Security) else item
            for item in security
        ]
    else:
        raise ParamsError("security type should be Security or list")


_bar_data_dtypes = OrderedDict([
    ('date', '<U26'), ('open', '<f8'), ('close', '<f8'),
    ('high', '<f8'), ('low', '<f8'), ('volume', '<f8'), ('money', '<f8'),
    ('paused', '<i1'), ('high_limit', '<f8'), ('low_limit', '<f8'),
    ('avg', '<f8'), ('pre_close', '<f8'), ('open_interest', '<f8'),
])

_tick_data_dtypes = OrderedDict([
    ('time', '<U26'), ('current', '<f8'), ('high', '<f8'), ('low', '<f8'),
    ('volume', '<f8'), ('money', '<f8'), ('position', '<f8'),
    ('a1_v', '<f8'), ('a2_v', '<f8'), ('a3_v', '<f8'), ('a4_v', '<f8'), ('a5_v', '<f8'),
    ('a1_p', '<f8'), ('a2_p', '<f8'), ('a3_p', '<f8'), ('a4_p', '<f8'), ('a5_p', '<f8'),
    ('b1_v', '<f8'), ('b2_v', '<f8'), ('b3_v', '<f8'), ('b4_v', '<f8'), ('b5_v', '<f8'),
    ('b1_p', '<f8'), ('b2_p', '<f8'), ('b3_p', '<f8'), ('b4_p', '<f8'), ('b5_p', '<f8'),
])


def get_price(security, start_date=None, end_date=None, frequency='1d',
              fields=None, skip_paused=False, fq='pre', count=None,
              panel=False, fill_paused=True):
    """获取一支或者多只证券的行情数据"""
    if panel:
        raise ParamsError("'panel' param is discarded")
    start_date = to_date(start_date) if start_date else None
    end_date = to_date(end_date) if end_date else None
    if (not count) and (not start_date):
        start_date = "2015-01-01"
    if count and start_date:
        raise ParamsError("(start_date, count) only one param is required")
    if frequency == "daily":
        frequency = "1d"
    elif frequency == "minute":
        frequency = "1m"
    if not fields:
        fields = ['open', 'close', 'high', 'low', 'volume', 'money']
    fields.insert(0, "date")

    data = api.get_price(
        code=security,
        end_date=end_date,
        count=10,
        unit=frequency,
        fq_ref_date=None
    )
    data = _csv2df(data)
    return data[fields].set_index("date")


def get_bars(security, count, unit="1d", fields=None, include_now=False,
             end_dt=None, fq_ref_date=None, df=True):
    """获取历史数据(包含快照数据), 可查询单个标的多个数据字段"""
    security = _convert_security(security)
    assert count > 0
    if end_dt:
        # end_dt = to_datetime(end_dt)
        end_dt = to_date(end_dt)  # HTTP 版只支持 date 参数
    if fq_ref_date:
        fq_ref_date = to_date(fq_ref_date)

    bars_mapping = {}
    for code in security:
        data = api.get_bars(
            code=code,
            count=int(count),
            unit=unit,
            end_date=end_dt,
            fq_ref_date=fq_ref_date,
        )
        header = [
            item.strip() for item in data.split('\n', 1)[0].split(',') if item
        ]
        dtype = [(col, _bar_data_dtypes[col]) for col in header]
        bars = _csv2array(data, dtype=dtype, skip_header=1)
        bars["date"] = _array2datetime(bars["date"])
        bars_mapping[code] = bars[fields] if fields else bars

    if df:
        dfs = []
        for code, arr in bars_mapping.items():
            index = [[code] * arr.size, list(range(arr.size))]
            dfs.append(pd.DataFrame(data=arr, index=index))
        return pd.concat(dfs, copy=False)
    else:
        return bars_mapping


def get_last_price(codes):
    """获取标的的最新价格"""
    codes = convert_security(codes)


def get_current_tick(security):
    """获取最新的 tick 数据"""
    if isinstance(security, Security):
        security = security.code
    dtype = list(_tick_data_dtypes.items())
    return _csv2df(api.get_current_tick(code=security), dtype=dtype)


def get_current_ticks(security):
    """获取多标的最新的 tick 数据"""
    security = _convert_security(security)
    dtype = [("code", "U30")] + list(_tick_data_dtypes.items())
    return _csv2df(api.get_current_ticks(code=",".join(security)), dtype=dtype)


def get_ticks(security, start_dt=None, end_dt=None, count=None, fields=None, skip=True, df=False):
    """获取 Tick 数据"""
    is_list_security = isinstance(security, (tuple, list, set))
    security = _convert_security(security)
    end_dt = to_datetime(end_dt) if end_dt else datetime.datetime.now()
    if start_dt and count:
        raise ParamsError("start_dt 与 count 参数只能二选一")
    if count:
        assert count > 0
        get_data = functools.partial(api.get_ticks, count=count, end_date=end_dt)
    else:
        start_dt = to_datetime(start_dt if start_dt else end_dt.date())
        get_data = functools.partial(api.get_ticks_period, date=start_dt, end_date=end_dt)

    ticks_mapping = {}
    for code in security:
        data = get_data(code=code)
        header = [
            item.strip() for item in data.split('\n', 1)[0].split(',') if item
        ]
        dtype = [(col, _tick_data_dtypes[col]) for col in header]
        ticks = _csv2array(data, dtype=dtype, skip_header=1)
        ticks_mapping[code] = ticks[fields] if fields else ticks

    if df:
        dfs = []
        for code, arr in ticks_mapping.items():
            index = [[code] * arr.size, list(range(arr.size))]
            dfs.append(pd.DataFrame(data=arr, index=index))
        return pd.concat(dfs, copy=False)
    else:
        if is_list_security or len(ticks_mapping) > 1:
            return ticks_mapping
        else:
            _, ticks = ticks_mapping.popitem()
            return ticks


def get_extras(info, security_list, start_date=None, end_date=None, df=True, count=None):
    """获取多只标的在一段时间的如下额外的数据"""
    assert security_list, "security_list is required"
    start_date = to_date(start_date)
    end_date = to_date(end_date)
    security_list = convert_security(security_list)


def get_fundamentals(query_object, date=None, statDate=None):
    """查询财务数据"""
    pass


def get_billboard_list(stock_list=None, start_date=None, end_date=None, count=None):
    """获取指定日期区间内的龙虎榜数据"""
    pass


def get_locked_shares(stock_list=None, start_date=None, end_date=None, forward_count=None):
    """ 获取指定日期区间内的限售解禁数据"""
    pass


def get_index_stocks(index_symbol, date=None):
    """获取一个指数给定日期在平台可交易的成分股列表"""
    pass


def get_industry_stocks(industry_code, date=None):
    """获取在给定日期一个行业的所有股票"""
    pass


def get_industries(name='zjw', date=None):
    """按照行业分类获取行业列表"""
    pass


def get_concept_stocks(concept_code, date=None):
    """获取在给定日期一个概念板块的所有股票"""
    assert concept_code, "concept_code is required"
    date = to_date(date)


def get_concepts():
    """获取概念板块"""
    pass


def get_concept(security, date):
    """获取股票所属概念板块"""
    date = to_date(date)


def get_money_flow(security_list, start_date=None, end_date=None, fields=None, count=None):
    """获取一只或者多只股票在一个时间段内的资金流向数据"""
    assert security_list, "security_list is required"
    security_list = convert_security(security_list)
    start_date = to_date(start_date)
    end_date = to_date(end_date)


def get_mtss(security_list, start_date=None, end_date=None, fields=None, count=None):
    """获取一只或者多只股票在一个时间段内的融资融券信息"""
    assert (not start_date) ^ (not count), "(start_date, count) only one param is required"
    start_date = to_date(start_date)
    end_date = to_date(end_date)
    security_list = convert_security(security_list)


def get_margincash_stocks(date=None):
    """返回上交所、深交所最近一次披露的的可融资标的列表"""
    date = to_date(date)


def get_marginsec_stocks(date=None):
    """返回上交所、深交所最近一次披露的的可融券标的列表"""
    date = to_date(date)


def get_future_contracts(underlying_symbol, date=None):
    """获取某期货品种在策略当前日期的可交易合约标的列表"""
    assert underlying_symbol, "underlying_symbol is required"
    dt = to_date(date)


def get_dominant_future(underlying_symbol, date=None):
    """获取主力合约对应的标的"""
    dt = to_date(date)


def get_baidu_factor(category=None, day=None, stock=None, province=None):
    """获取百度因子搜索量数据"""
    day = to_date(day)
    stock = normal_security_code(stock)


def get_all_factors():
    """获取聚宽因子库中所有的因子信息"""
    return _csv2df(api.get_all_factors())


def get_factor_values(securities, factors=None, start_date=None, end_date=None, count=None):
    """获取因子数据"""
    securities = _convert_security(securities)

    if factors is None:
        factors = ['VEMA5']
    elif is_string_types(factors):
        factors = factors.strip().split(',') if ',' in factors else [factors]
    if not isinstance(factors, (tuple, list, set)):
        raise Exception("Parameter 'factors' type error")

    start_date = to_date(start_date)
    end_date = to_date(end_date)

    if count:
        dates = get_trade_days(start_date, end_date, count)
        start_date, end_date = dates[0], dates[-1]
    elif start_date and not end_date:
        end_date = datetime.date.today()
    elif not start_date and end_date:
        start_date = datetime.date(2005, 1, 1)

    factors_str = ','.join(factors)
    dfs = []
    for code in securities:
        data = api.get_factor_values(
            code=code,
            date=start_date,
            end_date=end_date,
            columns=factors_str,
        )
        df = _csv2df(data)
        df["code"] = code
        dfs.append(df)

    all_data = pd.concat(dfs)
    data_dict = {}
    for factor in factors:
        pretty_data = all_data.pivot(
            index='date', columns='code', values=factor
        )
        data_dict[factor] = pretty_data.astype("float64").fillna(np.nan)
    return data_dict


def get_index_weights(index_id, date=None):
    """获取指数成分股权重"""
    assert index_id, "index_id is required"
    date = to_date(date)


def get_industry(security, date=None):
    """查询股票所属行业"""
    assert security, "security is required"
    security = convert_security(security)
    date = to_date(date)


def get_fund_info(security, date=None):
    """基金基础信息数据接口"""
    assert security, "security is required"
    security = convert_security(security)
    date = to_date(date)


def get_factor_effect(security, start_date, end_date, period, factor, group_num=5):
    """获取因子分层回测效果"""
    security = convert_security(security)
    start_date = to_date(start_date)
    end_date = to_date(end_date)
    assert group_num > 0, "group_num must be a positive numbe"
    assert isinstance(security, six.string_types), "security must be a inde code"
    assert period[-1] in ["D", "W", "M"], "period must be end with one of (\"D\", \"W\", \"M\")"


def get_call_auction(security, start_date=None, end_date=None, fields=None):
    """获取指定时间区间内集合竞价时的 Tick 数据"""
