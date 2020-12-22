#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@163.com>

import re
import json
from urllib2 import urlopen


class JQDataError(Exception):

    pass


class InvalidTokenError(JQDataError):

    pass


class JQDataApi(object):

    _DEFAULT_URL = "https://dataapi.joinquant.com/apis"

    def __init__(self, user, password, url=None):
        self.user = user
        self.password = password
        self.url = url or self._DEFAULT_URL

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
        if not mob:
            self.user = mob
        if not pwd:
            self.password = pwd
        data = self._request_data(
            "get_token", mob=self.user, pwd=self.password
        )
        self.token = data
        return data

    def get_current_token(self, mob=None, pwd=None):
        if not mob:
            self.user = mob
        if not pwd:
            self.password = pwd
        data = self._request_data(
            "get_current_token", mob=self.user, pwd=self.password
        )
        self.token = data
        return data

    def __getattr__(self, name):
        if name.startswith("get_") or name == "run_query":
            pass
