#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import time
import pytz
import hashlib
import hmac
import base64
from datetime import datetime, timedelta

# date = t + timedelta(hours=-16)
# print(t)

# 生成Timestamp参数
t = (datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
date = t.split(' ')[0]
t = t.split(' ')[1]
t = date + 'T' + t + 'Z'
print(t)

parameters = {
    'AWSAccessKeyId': 'AKIAJTOJNBBBYA6MQJCA',
    'Action': 'GetMatchingProductForId',
    'MWSAuthToken': 'amzn.mws.1caeb4e8-438d-72b4-67f2-464039da966c',
    'SellerId': 'A1XEMYOCVN4TN8',
    'SignatureMethod': 'HmacSHA256',
    'SignatureVersion': '2',
    'SubmittedFromDate': '2018-11-07T12:00:00Z',
    'Timestamp': t,
    'Version': '2011-10-01',
}

# 将参数排序
keys = list(parameters.keys())

keys.sort()
array = []
# 拼接参数：
for k in keys:
    array.append(k + '=' + parameters.get(k))
url_string = '&'.join(array)
# 生成签名
string_to_sign = "POST\n" + "mws.amazonservices.com\n" + "/Products/2011-10-01\n%s" % url_string
message = (string_to_sign).encode('utf-8')
secret = ("awIhm0SRruyoMeWoPpSFpTPVq3tcHQJ15o6kwY4Q").encode('utf-8')

signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())

FormData = {
    'AWSAccessKeyId': 'AKIAJTOJNBBBYA6MQJCA',
    'Action': 'GetMatchingProductForId',
    'MWSAuthToken': 'amzn.mws.1caeb4e8-438d-72b4-67f2-464039da966c',
    'SellerId': 'A1XEMYOCVN4TN8',
    'SignatureVersion': 2,
    'Timestamp': t,
    'Version': '2011-10-01',
    'Signature': signature,
    'SignatureMethod': 'HmacSHA256',
    'MarketplaceId': 'ATVPDKIKX0DER',
    'IdType': 'ISBN',
    'IdList.Id.1': '9781933988665',
}

url = 'https://mws.amazonservices.com/Products/2011-10-01'

res = requests.post(url, data=FormData, verify=False)
print(res.text)
