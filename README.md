JQDataHTTP
==========

[JQData HTTP](https://dataapi.joinquant.com/docs) 版接口封装。提供兼容 [JQDataSDK](https://github.com/JoinQuant/jqdatasdk) 的接口，同时也支持返回接口原生的 csv 格式数据。自动缓存 token，token 过期后自动重新获取。

```python
>>> import jqdatahttp
>>> jqdatahttp.settimeout(10)
>>> jqdatahttp.auth('xxxxxxxxxxx', 'xxxxxx')
>>> jqdatahttp.get_security_info('000001.XSHE')
Security(code='000001.XSHE', type='stock', start_date='1991-04-03', end_date='2200-01-01', display_name='平安银行')
>>> jqdatahttp.get_current_tick('000001.XSHE')
...
```

## 安装方式

```
pip install -U git+https://github.com/kuanghy/jqdatahttp
```

（由于功能还没完善，暂时为提交到 PyPI）

## 账号接口

- **账号登录**

```python
auth(username, password)
```

指定账号和密码，登录成功后会自动缓存 token，无需重新获取（仅在单个进程中缓存，如果进程退出后重新启动，仍然会重新获取）

- **账号退出**

```python
logout()
```

退出时会丢弃掉账号信息与 token 的缓存，接口不再可用

- **Token 处理**

```python
# 获取 Token，如果指定账号密码则获取新的 Token，否则获取当前 Token
get_token(username=None, password=None)

# 重置 Token，即请求新的 Token，旧的 Token 会失效
reset_token()
```

- **查询当日剩余请求条数**

```python
get_query_count()
```

- **设置请求超时时间**

```python
settimeout(value)
```

默认超时时间为 20 秒

## 原生接口

原生接口是对 HTTP 做的封装，提供原生的接口数据获取方式。可使用 `jqdattahttp.api.xxx` 的方式调用，如 get_security_info 接口对应 jqdattahttp.api.get_security_info，使用示例：

```python
>>> print(jqdatahttp.api.get_security_info(code='000001.XSHE'))
code,display_name,name,start_date,end_date,type,parent
000001.XSHE,平安银行,PAYH,1991-04-03,2200-01-01,stock,
```

接口函数的参数为，HTTP 请求时提供的 json 参数中去掉 method 和 token 后剩下的字段。如 get_security_info 接口的 HTTP 请求需要提供如下的参数：

```json
{
    "method": "get_security_info",
    "token": "5b6a9ba7b0f572bb6c287e280ed",
    "code": "502050.XSHG"
}
```

则 jqdattahttp.api.get_security_info 则只需提供 code 关键参数。

此外，还支持提供两个额外的参数：

- `show_request_params`: 参数为 True 会将请求时的详细参数打印出来
- `show_raw_result`: 该参数为 True 会将原始数据打印
- `auto_format_result`: 该参数为 True 时，会更新接口返回内容将结果格式化为 pandas.DataFrame 或者 list 等结构

这些额外参数也支持在全局设置：

```
jqdatahttp.api.show_request_params = True  # 显示请求参数
jqdatahttp.api.show_raw_result = True      # 显示原始的返回结果
jqdatahttp.api.auto_format_result = True   # 自动格式化返回结果
```

示例：

```python
>>> jqdatahttp.api.get_security_info(code='000001.XSHE', auto_format_result=True, show_raw_result=True)
start show raw result --------------------
code,display_name,name,start_date,end_date,type,parent
000001.XSHE,平安银行,PAYH,1991-04-03,2200-01-01,stock,
end show raw result --------------------
          code display_name  name  start_date    end_date   type  parent
0  000001.XSHE         平安银行  PAYH  1991-04-03  2200-01-01  stock     NaN

>>> jqdatahttp.api.show_request_params = True
>>> jqdatahttp.get_security_info('000001.XSHE')
start show request body --------------------
{"method": "get_security_info", "token": "586a9ba7b0f572bb6c2b782802c408", "code": "000001.XSHE"}
end show request body --------------------
Security(code='000001.XSHE', type='stock', start_date='1991-04-03', end_date='2200-01-01', display_name='平安银行')
```

## JQDataSDK 兼容接口

此外还提供了兼容 JQDataSDK 版的接口，函数名、参数以及返回值基本与其相同。示例：

```python
>>> jqdatahttp.get_security_info(code='000001.XSHE')
Security(code='000001.XSHE', type='stock', start_date='1991-04-03', end_date='2200-01-01', display_name='平安银行')

>>> jqdatahttp.get_all_securities('stock')
            display_name  name  start_date    end_date   type
code
000001.XSHE         平安银行  PAYH  1991-04-03  2200-01-01  stock
000002.XSHE          万科A   WKA  1991-01-29  2200-01-01  stock
000004.XSHE         国华网安  GHWA  1990-12-01  2200-01-01  stock
000005.XSHE         世纪星源  SJXY  1990-12-10  2200-01-01  stock
000006.XSHE         深振业A  SZYA  1992-04-27  2200-01-01  stock
...                  ...   ...         ...         ...    ...
688777.XSHG         中控技术  ZKJS  2020-11-24  2200-01-01  stock
688788.XSHG         科思科技  KSKJ  2020-10-22  2200-01-01  stock
688819.XSHG         天能股份  TNGF  2021-01-18  2200-01-01  stock
688981.XSHG         中芯国际  ZXGJ  2020-07-16  2200-01-01  stock
689009.XSHG         九号公司  JHGS  2020-10-29  2200-01-01  stock

[4311 rows x 5 columns]

>>> jqdatahttp.get_trade_days(end_date='2021-03-05')
array([datetime.date(2005, 1, 4), datetime.date(2005, 1, 5),
       datetime.date(2005, 1, 6), ..., datetime.date(2021, 3, 3),
       datetime.date(2021, 3, 4), datetime.date(2021, 3, 5)], dtype=object)

>>> jqdatahttp.get_bars('FG8888.XZCE', end_dt='2021-03-04 15:00:00', count=5, unit='1m')
                              date      open     close      high       low   volume         money  open_interest
FG8888.XZCE 0  2021-03-04 22:56:00  2068.144  2070.734  2072.408  2067.217   7860.0  3.295467e+08       700662.0
            1  2021-03-04 22:57:00  2070.927  2071.875  2072.781  2070.002   5400.0  2.263327e+08       700766.0
            2  2021-03-04 22:58:00  2072.688  2072.565  2074.386  2071.749   5629.0  2.360677e+08       699888.0
            3  2021-03-04 22:59:00  2072.543  2063.416  2072.785  2062.492  25076.0  1.031859e+09       692303.0
            4  2021-03-04 23:00:00  2070.089  2063.416  2070.129  2062.492  18243.0  7.451906e+08       692303.0
```
