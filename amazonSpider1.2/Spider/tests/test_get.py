#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

sys.path.append("../")
import time

from Crawler.tosellCrawler import TosellCrawler
from Crawler.goodsCrawler import GoodsCrawler
from Crawler.reviewsCrawler import ReviewsCrawler
from Crawler.keywordCrawler import KwCrawler
from utils.util import Logger
from utils.util import GetRedis
from utils.util import DataQueue
from utils.util import UrlQueue
from utils.util import KeyWordQueue


class Reviews(ReviewsCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.args = kwargs['args']

    def run(self):
        asin_or_kw, url_dict = self.args
        self.download(asin_or_kw, url_dict)


class Tosell(TosellCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.args = kwargs['args']

    def run(self):
        asin_or_kw, url_dict = self.args
        self.download(asin_or_kw, url_dict)


class Keyword(KwCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.args = kwargs['args']

    def run(self):
        asin_or_kw, url_dict = self.args
        self.download(asin_or_kw, url_dict)


class Goods(GoodsCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.args = kwargs['args']

    def run(self):
        asin_or_kw, url_dict = self.args
        self.download(asin_or_kw, url_dict)


if __name__ == '__main__':
    log_name = sys.argv[0].split('/')[-1].split('.')[0]
    debug_log = Logger(log_name=log_name)
    info_log = Logger(log_level='info', log_name=log_name)
    myRedis = GetRedis().return_redis(debug_log)
    kwQ = KeyWordQueue(myRedis, debug_log)
    urlQ = UrlQueue(myRedis, debug_log)
    dataQ = DataQueue(myRedis, debug_log)

    asin_list = [
        # 'B01LZ6XKS6',
        # 'B004L5JCZ4',
        # 'B006UET808',
        # 'B07CHYKCQ7',
        # 'B07F847NZW'
        #
        # 'B01F0QQN8Q',
        'B07FCDW81J'
        # 'B01FF0E7QC'
        # 'B07FCFFMJV'

    ]
    t_lsit = []
    for asin in asin_list:
        url_dict = {'asin': asin, 'mtm': int(time.time()), 'utp': 'tosell'}
        args = (asin, url_dict)
        # t_lsit.append(Tosell(urlQ, dataQ, kwQ, info_log, debug_log, args=args))
        # t_lsit.append(Reviews(urlQ, dataQ, kwQ, info_log, debug_log, args=args))
        t_lsit.append(Goods(urlQ,dataQ, kwQ, info_log, debug_log, args=args))
        # t_lsit.append(Keyword(urlQ,dataQ, kwQ, info_log, debug_log, args=args))
    for t in t_lsit:
        t.start()
    for t in t_lsit:
        t.join()
