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

    asin_list = [
        # 'B01G49UOW4',
        # 'B07H3CYD62',

        # 'sports equip ment',
        'iphone Xth'
    ]

    t_lsit = []
    for asin in asin_list:
        ip = ''
        url_dict = {'asin': asin, 'mtm': int(time.time()), 'utp': 'tosell'}
        args = (ip, asin, url_dict)
        # t_lsit.append(Tosell(urlQ, ipQ, dataQ, cookiesQ, kwQ, info_log, debug_log, args=args))
        # t_lsit.append(Reviews(urlQ, ipQ, dataQ, cookiesQ, kwQ, info_log, debug_log, args=args))
        # t_lsit.append(Goods(urlQ, ipQ, dataQ, cookiesQ, kwQ, info_log, debug_log, args=args))
        t_lsit.append(Keyword(urlQ, ipQ, dataQ, cookiesQ, kwQ, info_log, debug_log, args=args))
    for t in t_lsit:
        t.start()
        t.join()
    for t in t_lsit:
        t.join()
