#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@163.com>

from __future__ import print_function

import re
from setuptools import setup
from os.path import join as path_join, dirname as path_dirname


CURRDIR = path_dirname(__file__)

setup_args = dict(
    name='jqdatahttp',
    version='0.0.1',
    py_modules=["jqdatahttp"],
    author='Huoty',
    author_email='sudohuoty@163.com',
    maintainer="Huoty",
    maintainer_email="sudohuoty@163.com",
    description="JQData HTTP API encapsulation",
    url='https://github.com/kuanghy/jqdatahttp',
    keywords=["jqdata", "jqdatahttp", "jq", "joinquant"],
    zip_safe=False,
    license='Apache License v2',
    python_requires='>=3.6',
    platforms=["any"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
    ],
)


def get_version():
    with open(path_join(CURRDIR, 'jqdatahttp.py'), "rb") as fp:
        content = fp.read().decode("utf-8")
        pattern = r'.*__version__\s+=\s+["\'](.*?)["\']'
        version = re.match(pattern, content, re.S).group(1)
    return version


def get_long_description():
    with open(path_join(CURRDIR, 'README.md'), 'rb') as fp:
        long_description = fp.read().decode('utf-8')
    return long_description


def main():
    setup_args["version"] = get_version()
    setup_args["long_description"] = get_long_description()
    setup_args["long_description_content_type"] = "text/markdown"
    setup_args["extras_require"] = {
        "whole": ["numpy", "pandas"],
    }
    setup(**setup_args)


if __name__ == "__main__":
    main()
