# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@163.com>

import jqdatahttp
from jqdatahttp import JQDataApi


def test_dataapi():
    api = jqdatahttp.api
    api.auto_format_data = True
    print(api.get_token())

    data = api.get_index_stocks(code="000300.XSHG", date="2019-01-09")
    print(data)

    data = api.get_security_info(code="000001.XSHE")
    print(data)
