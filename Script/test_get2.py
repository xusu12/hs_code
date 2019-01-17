#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

sys.path.append("../")
import time

from utils.util import Logger
from utils.util import GetRedis
from utils.util import IpQueue
from utils.util import DataQueue
from utils.util import UrlQueue
from utils.util import CookQueue
from utils.util import KeyWordQueue
from Crawler.goodsCrawler import GoodsCrawler
from Crawler.keywordCrawler import KwCrawler
from Crawler.tosellCrawler import TosellCrawler
from Crawler.reviewsCrawler import ReviewsCrawler


class Reviews(ReviewsCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        print(kwargs)
        self.args = kwargs['args']

    def run(self):
        ip, asin_or_kw, url_dict = self.args
        self.download(ip, asin_or_kw, url_dict)


class Tosell(TosellCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.args = kwargs['args']

    def run(self):
        ip, asin_or_kw, url_dict = self.args
        self.download(ip, asin_or_kw, url_dict)


class Goods(GoodsCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.args = kwargs['args']

    def run(self):
        ip, asin_or_kw, url_dict = self.args
        self.download(ip, asin_or_kw, url_dict)


class Keyword(KwCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.args = kwargs['args']

    def run(self):
        ip, asin_or_kw, url_dict = self.args
        self.download(ip, asin_or_kw, url_dict)


if __name__ == '__main__':
    log_name = sys.argv[0].split('/')[-1].split('.')[0]
    debug_log = Logger(log_name=log_name)
    info_log = Logger(log_level='info', log_name=log_name)
    myRedis = GetRedis().return_redis(debug_log)
    kwQ = KeyWordQueue(myRedis, debug_log)
    urlQ = UrlQueue(myRedis, debug_log)
    ipQ = IpQueue(myRedis, debug_log)
    dataQ = DataQueue(myRedis, debug_log)
    cookiesQ = CookQueue(myRedis, debug_log)

    with open('./keyword.csv', 'r', encoding='utf8') as f:
        lis = f.readlines()
    asin_list = []
    for li in lis:
        if li.strip() not in asin_list:
            asin_list.append(li.strip())

    while len(asin_list) > 0:
        t_lsit = []
        for i in range(5):
            if len(asin_list) > 0:
                asin = asin_list.pop(0)
                ip = ''
                url_dict = {'asin': asin, 'mtm': int(time.time()), 'utp': 'tosell'}
                args = (ip, asin, url_dict)
                t = Keyword(urlQ, ipQ, dataQ, cookiesQ, kwQ, info_log, debug_log, args=args)
                t.start()
                t_lsit.append(t)
        for t in t_lsit:
            t.join()


