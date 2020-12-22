# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@163.com>

import jqdatahttp
from jqdatahttp import JQDataApi


def test_dataapi():
    dataapi = jqdatahttp.dataapi
    dataapi.auto_format_data = True
    print(dataapi.get_token())

    data = dataapi.get_index_stocks(code="000300.XSHG", date="2019-01-09")
    print(data)

    data = dataapi.get_security_info(code="000001.XSHE")
    print(data)
