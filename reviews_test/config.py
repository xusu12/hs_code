#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
import os
import re


# 项目根目录
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_DIR = '/data1/www/'

BASE_TYPE_LIST = [
    'development',
    'testing',
    'pre_release',
    'production',
]


## 运行环境(db or redis)
def get_environment():
    env_file = os.path.join(BASE_DIR, 'environment.txt') \
        if re.search('[Ww]in', sys.platform) else os.path.join(ENV_DIR, 'environment.txt')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            env_str = f.readline().lstrip().strip()
            return env_str if env_str in BASE_TYPE_LIST else ''

BASE_TYPE = get_environment() if get_environment() else 'production'

# 代理服务器
PROXY_HOST = "n10.t.16yun.cn"
PROXY_POPT = "6442"

# 代理隧道验证信息
PROXY_USER = "16WRMGEL"
PROXY_PASS = "070128"

PROXY_META = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
    "host": PROXY_HOST,
    "port": PROXY_POPT,
    "user": PROXY_USER,
    "pass": PROXY_PASS,
}

PROXY_VERIFY = None

# 缓存时间(s)
CACHE_TIME = 72000

# 存储时间
SAVE_TIME = 3600 * 24 * 30

# 线程数
T_NUM = 10

# UA池文件
UA_FILE = os.path.join(BASE_DIR, 'UAPOND.json')

# redis配置
REDIS_CONFIG = {
    "development": dict(
        host='192.168.13.8',
        port=6379,
        db=3,
        max_connections=100,
        decode_responses=True,
    ),
    "testing": dict(
        host='192.168.13.8',
        port=6379,
        db=5,
        max_connections=100,
        decode_responses=True,
    ),
    # 集群版
    'pre_release': [
        # {'host': '172.19.55.201', 'port': 7001},
        #{'host': '172.19.55.201', 'port': 9001},
        #{'host': '172.19.55.200', 'port': 7002},
        #{'host': '172.19.55.200', 'port': 9002},
        #{'host': '172.19.55.199', 'port': 7003},
        {'host': '172.19.55.199', 'port': 9003},
    ],
    # 集群版
    'production': [
        {'host': '172.19.55.201', 'port': 7001},
        {'host': '172.19.55.201', 'port': 9001},
        {'host': '172.19.55.200', 'port': 7002},
        {'host': '172.19.55.200', 'port': 9002},
        {'host': '172.19.55.199', 'port': 7003},
        {'host': '172.19.55.199', 'port': 9003},
    ],
}

# 兜底ua池
UAPOND = [
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.5 Safari/534.55.3',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; TencentTraveler 4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1))',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; Maxthon/3.0)',
    'Mozilla/5.0 (Windows; U; Windows NT 5.2) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13',
    'Mozilla/5.0 (Windows; U; Windows NT 5.2) AppleWebKit/525.13 (KHTML, like Gecko) Version/3.1 Safari/525.13',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1) Gecko/20070309 Firefox/2.0.0.3',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:16.0) Gecko/20121026 Firefox/16.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)',
]

# 兜底headers
BASE_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; TencentTraveler 4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1))',
    'Upgrade-Insecure-Requests': '1',
}

if __name__ == '__main__':
    pass
    # print(get_environment())
    print(BASE_TYPE)