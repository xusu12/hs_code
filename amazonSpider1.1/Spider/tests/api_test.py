#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib

import requests
import time
import pytz
from datetime import datetime, timedelta
import hashlib
import hmac
import base64

def run():
    secretKey = "AKIAJTOJNBBBYA6MQJCA"
    serviceUrl = "https://mws.amazonservices.com/"

    t = (datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    print(t)
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
        'SubmittedFromDate': '',
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
    string_to_sign = "POST\n" + "mws.amazonservices.com\n" + "/\n%s" % url_string
    message = (string_to_sign).encode('utf-8')
    secret = ("AKIAJTOJNBBBYA6MQJCA").encode('utf-8')

    signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
    print(signature)


if __name__ == '__main__':
    run()