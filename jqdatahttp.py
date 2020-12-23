# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@163.com>

import re
import json
from importlib import import_module

try:
    from urllib.request import urlopen, Request as HTTPRequest
except ImportError:
    from urllib2 import urlopen, Request as HTTPRequest

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO


__version__ = '0.1.0'


class JQDataError(Exception):

    pass


class InvalidTokenError(JQDataError):

    pass


class JQDataApi(object):

    _DEFAULT_URL = "https://dataapi.joinquant.com/apis"

    def __init__(self, username=None, password=None, url=None,
                 auto_format_data=False):
        self.username = username
        self.password = password
        self.url = url or self._DEFAULT_URL
        self.auto_format_data = auto_format_data

        self.token = None
        self.timeout = 10
        self._encoding = "UTF-8"

    _INVALID_TOKEN_PATTERN = re.compile(
        r'(invalid\s+token)|(token\s+expired)|(token.*无效)|(token.*过期)'
    )

    def _request(self, data):
        req_body = json.dumps(data).encode(self._encoding)
        req = HTTPRequest(self.url, data=req_body, method="POST")
        with urlopen(req, timeout=self.timeout) as resp:
            resp_body = resp.read()
            resp_data = resp_body.decode(self._encoding)
            if resp.status != 200:
                raise JQDataError(resp_data)
        if re.search(self._INVALID_TOKEN_PATTERN, resp_data):
            raise InvalidTokenError(resp_data)
        return resp_data

    def _request_data(self, method, **kwargs):
        req_data = {"method": method}
        if method not in {"get_token", "get_current_token"}:
            if not self.token:
                self.get_token()
            req_data["token"] = self.token
        req_data.update(kwargs)
        try:
            resp_data = self._request(req_data)
        except InvalidTokenError:
            req_data["token"] = self.get_token()
            resp_data = self._request(req_data)
        return resp_data

    def get_token(self, mob=None, pwd=None):
        if mob:
            self.username = mob
        if pwd:
            self.password = pwd
        data = self._request_data(
            "get_token", mob=self.username, pwd=self.password
        )
        self.token = data
        return data

    def get_current_token(self, mob=None, pwd=None):
        if mob:
            self.username = mob
        if pwd:
            self.password = pwd
        data = self._request_data(
            "get_current_token", mob=self.username, pwd=self.password
        )
        self.token = data
        return data

    def auth(self, username=None, password=None, url=None):
        if url:
            self.url = url
        self.get_token(mob=username, pwd=password)

    def __getattr__(self, name):
        if name.startswith("get_") or name == "run_query":

            def wrapper(self, **kwargs):
                data = self._request_data(name, **kwargs)
                if not self.auto_format_data:
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


def _csv2array(data):
    pass


def _csv2df(data):
    pd = import_module("pandas")
    return pd.read_csv(StringIO(data))


def auth(username, password, url=None):
    api.auth(username=username, password=password, url=url)
