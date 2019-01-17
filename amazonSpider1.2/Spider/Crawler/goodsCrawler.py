#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import sys
sys.path.append("../")

import time
import pickle
from threading import Thread

from Crawler.BaseCrawler import BaseCrawler
from Crawler.goodsParser import GoodsParser
from utils.util import return_PST
from conf.setting import BASE_TYPE
from conf.setting import GOODS_T_NUM

from utils.util import Logger
from utils.util import GetRedis
from utils.util import DataQueue
from utils.util import UrlQueue
from utils.util import KeyWordQueue
from utils.decorator import timer
from Crawler.productTosellCrawler import start


class GoodsCrawler(BaseCrawler, Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Thread.__init__(self)
        self.url_type = 'goods'

    def save_url_title(self, asin, html):
        urlTitle = GoodsParser.get_urltitle(asin, html)
        if urlTitle and len(urlTitle) <= 72:
            urlQ.add_urlTitle_to_string(asin, urlTitle)

    @timer
    def download(self, asin_or_kw, url_dict):
        print(asin_or_kw, url_dict)
        url_type = self.url_type
        print(url_type)
        asin = asin_or_kw
        monitor_type = url_dict.get('mtp') or 1
        print('url type: ', url_type)
        url_md5key = url_dict.get('md5') or ''
        if not url_md5key:
            url_md5key = self.get_md5_key(asin + url_type)
        startTime = return_PST().strftime("%Y-%m-%d %H:%M:%S")
        time_now = lambda: time.time()
        time1 = time_now()
        retry = False
        old_dnum = url_dict.get('dnum') or 0
        if old_dnum > 3:
            retry = True
        url, referer = GoodsParser.make_goods_url(asin, retry=retry)
        if url:
            print('goods_url: ', url)
            html, cookiesObj, is_error = self.get_html(url, referer=referer, url_type=url_type, asin=asin)
            print('is_error:', is_error)
            durl = url_dict.get('durl') or []
            durl.append(url)
            url_dict['durl'] = list(set(durl))
            url_dict['dnum'] = old_dnum + 1
            if is_error:
                self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
                msgInt = 6
                proxyInfo = 'get Html error'
                self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)

            else:
                analyze = self.analyze_html(html, asin_or_kw, url_dict,
                          time1, startTime, html_type=url_type)
                if analyze and analyze != 404:
                    result, is_error = self.parser(html, html_type=url_type, asin=asin,
                                                   debug_log=self.debug_log, monitor_type=monitor_type, url=url)
                    if is_error:
                        self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
                        msgInt = 3
                        proxyInfo = 'get data error'
                        self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)
                    else:
                        if not result:
                            self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
                            msgInt = 2
                            proxyInfo = 'get data defeated'
                            self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)
                        else:
                            goods_datas = result[0]
                            if goods_datas:
                                cookies, headers = cookiesObj
                                user_anget = headers.get('User-Agent')
                                print(user_anget)
                                from pprint import pprint
                                pprint(cookies)
                                pprint(goods_datas)
                                msgInt = 1
                                proxyInfo = 'get data success'
                                log_param = (asin, time1, msgInt, url_type, startTime, proxyInfo)
                                start(asin=asin, goods_datas=goods_datas, user_anget=user_anget, url_dict=url_dict, goods_html=html, cookies=cookies, log_param=log_param, crawler_obj=self)
                else:
                    self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
                    time.sleep(1)
        else:
            print(url_type, '没有url')
            self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
            time.sleep(1)


def goods_start(urlQ, dataQ, kwQ, info_log, debug_log, i):
    debug_log.debug('\ngoods_start%s 启动成功' % (i))
    t_num = GOODS_T_NUM
    from conf.setting import develop_e_name
    if BASE_TYPE == develop_e_name:
        t_num = 1
    while True:
        urllen1 = urlQ.retrieve_goodsUrl_len()
        urllen2 = urlQ._get_queue_len('monitorGoods')
        urllen = urllen1 + urllen2
        # print(urllen)
        if urllen < 1:
            sys.exit()
        crawlers = [GoodsCrawler(urlQ, dataQ, kwQ, info_log, debug_log) for i in range(t_num)]
        for craw in crawlers:
            craw.start()
        for craw in crawlers:
            craw.join()


if __name__ == '__main__':
    log_name = sys.argv[0].split('/')[-1].split('.')[0]
    debug_log = Logger(log_name=log_name)
    info_log = Logger(log_level='info', log_name=log_name)
    myRedis = GetRedis().return_redis(debug_log)
    kwQ = KeyWordQueue(myRedis, debug_log)
    urlQ = UrlQueue(myRedis, debug_log)
    dataQ = DataQueue(myRedis, debug_log)
    goods_start(urlQ, dataQ, kwQ, info_log, debug_log, 1)
