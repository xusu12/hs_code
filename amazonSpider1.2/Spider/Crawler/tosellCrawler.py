#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import sys

sys.path.append("../")
# from os import cpu_count
import re
import time
import pickle
from threading import Thread
from math import ceil

from Crawler.BaseCrawler import BaseCrawler
from Crawler.tosellParser import TosellParser
from Crawler.tosellParser import TosellNotFoundParser
from Crawler.DataOutput import DataOutput
from utils.util import return_PST
from conf.setting import BASE_TYPE
from conf.setting import TOSELL_T_NUM

from utils.util import Logger
from utils.util import GetRedis
from utils.util import DataQueue
from utils.util import UrlQueue
from utils.util import KeyWordQueue
from utils.decorator import timer


class TosellCrawler(BaseCrawler, Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Thread.__init__(self)
        self.url_type = 'tosell'

    # 根据asin与页数, 生成翻页url
    def make_page_url(self, asin, page):
        url = TosellParser.make_tosell_page_url(asin, page)
        return url

    # 获取要翻的页数
    def get_page_urls(self, asin, tosellSum):
        page_urls = []
        if type(tosellSum) is int:
            page_num = ceil(tosellSum / 10)
            print(page_num, type(page_num))
            one_page_url = TosellParser.make_tosell_url(asin)
            page_urls.append(one_page_url)
            if page_num > 0:
                for i in range(1, page_num):
                    url = self.make_page_url(asin, i + 1)
                    page_urls.append(url)
            return page_urls

    # 下载跟卖页面
    def get_page_html(self, page_url, referer, **kwargs):
        page_html, cookies, page_is_error = self.get_html(page_url, referer=referer)
        self.url_list.append(page_url)
        self.html_list.append(page_html)
        self.is_error_list.append(page_is_error)
        if cookies:
            self.cookies = cookies

    # 翻页下载跟卖
    def get_tosell_html_lsit(self, asin, goods_url, referer, **kwargs):
        self.html_list = []
        self.url_list = []
        self.is_error_list = []
        self.not_found = False
        self.cookies = None
        goods_html = kwargs.get('goods_html')
        # 如果没有传goods_html, 或者 goods_html 为空字符串
        if type(goods_html) is not str or not goods_html:
            # 抓取商品的页面
            goods_html, cookiesObj, is_error = self.get_html(goods_url, referer=referer, url_type=self.url_type,
                                                             asin=asin)
        self.goods_html = goods_html
        # 通过解析类的方法获取跟卖的总数
        tosellSum = TosellParser.get_to_sell_sum(goods_html)
        print('tosellSum1', tosellSum)
        if tosellSum < 1 and not self.is_page_not_found(goods_html):
            tosellSum = 1
        print('tosellSum2', tosellSum)
        print('tosellSum: ', tosellSum)
        page_url_list = self.get_page_urls(asin, tosellSum)
        # tList = []
        # tStart = 0
        # 遍历下载跟卖
        if page_url_list:
            i = 0
            referer = goods_url
            for page_url in page_url_list:
                i += 1
                print('tosell page%s: [%s]' % (i, page_url))
                print('tosell referer %s: [%s]' % (i, referer))
                self.get_page_html(page_url, referer)
                if re.search('There are currently no listings for this search', self.html_list[i - 1]):
                    print('There are currently no listings for this search')
                    break
                referer = page_url
        else:
            # 做没有跟卖处理.
            pass

        return self.html_list, self.url_list, self.cookies, self.is_error_list, tosellSum

    @timer
    def download(self, asin_or_kw, url_dict, **kwargs):
        url_type = self.url_type
        asin = asin_or_kw
        monitor_type = url_dict.get('mtp') or 5
        print('url type: ', url_type)
        startTime = return_PST().strftime("%Y-%m-%d %H:%M:%S")
        time_now = lambda: time.time()
        time1 = time_now()
        url_md5key = url_dict.get('md5') or ''
        if not url_md5key:
            url_md5key = self.get_md5_key(asin + url_type)
        goodsUrl_tuple = self.make_url(asin, url_type='goods')
        goodsUrl, referer = goodsUrl_tuple
        if goodsUrl:
            html_list, url_list, cookiesObj, is_error_lsit, tosellSum = \
                self.get_tosell_html_lsit(asin, goodsUrl, referer, **kwargs)
            old_dnum = url_dict.get('dnum') or 0
            durl = url_dict.get('durl') or []
            url_dict['durl'] = list(set(durl + url_list))
            url_dict['dnum'] = old_dnum + 1
            # 如果判定为没有跟卖, 结束程序
            if self.not_found:
                self.urlQ.record_tosell_notFound_times()
                msgInt = 0
                proxyInfo = 'the asin not tosell'
                self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)
                return self.debug_log.war('%s没有跟卖' % (asin))
            i = -1
            tosell_html_list = []
            if len(html_list) > 0:
                for html in html_list:
                    i += 1
                    is_error = is_error_lsit[i]
                    print(is_error_lsit, is_error_lsit[i])
                    url = url_list[i]
                    if is_error:
                        self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
                        msgInt = 6
                        proxyInfo = 'get Html error'
                        self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)

                    else:
                        analyze = self.analyze_html(html, asin, url_dict, time1,
                                                    startTime, html_type=url_type)
                        if analyze and analyze != 404:
                            tosell_html_list.append(html)
                print('html num: ', len(html_list), 'tosell_html num: ', len(tosell_html_list))
                if len(tosell_html_list) == len(html_list):
                    result, is_error = self.parser(tosell_html_list, html_type=url_type, asin=asin,
                                                   monitor_type=monitor_type, tosellSum=tosellSum,
                                                   goods_html_code=self.goods_html)
                    # from pprint import pprint
                    # pprint('tosell_result', result)
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
                            self.save_success_asin_keyword(asin, url_type=url_type)
                            msgInt = 1
                            proxyInfo = 'get data success'
                            self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)
                            tosell_datas = result[0]
                            # from pprint import pprint
                            # pprint(tosell_datas)
                            data_bytes = pickle.dumps(tosell_datas)
                            self.dataQ.add_tosell_to_queue(data_bytes)
                            self.dataQ.record_data_ok_times()
                            self.dataQ.record_tosell_ok_times()
                else:
                    self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
            else:
                if tosellSum == -1:
                    self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
                if tosellSum > 0:
                    self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
        else:
            print(url_type, '没有url')
            self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
            time.sleep(1)


def tosell_start(urlQ, dataQ, kwQ, info_log, debug_log, i):
    debug_log.debug('\ntosell_start%s 启动成功' % (i))
    t_num = TOSELL_T_NUM
    from conf.setting import develop_e_name
    if BASE_TYPE == develop_e_name:
        t_num = 1
    while True:
        urllen1 = urlQ.retrieve_tosellUrl_len()
        urllen2 = urlQ._get_queue_len('monitorTosell')
        urllen = urllen1 + urllen2
        if urllen < 1:
            sys.exit()
        crawlers = [TosellCrawler(urlQ, dataQ, kwQ, info_log, debug_log) for i in range(t_num)]
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
    tosell_start(urlQ, dataQ, kwQ, info_log, debug_log, 1)
