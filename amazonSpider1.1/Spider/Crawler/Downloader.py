#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import sys
sys.path.append("../")
import time
import re
# import pickle
from random import randint
from urllib.parse import unquote
from urllib.parse import urlparse
from lxml import etree
import json
# import hashlib

import requests
from retrying import retry
# from selenium import webdriver

# 破解验证码
from captcha_crack import amazon_captcha_crack
from utils.util import UaPond
from utils.util import Sleep
from conf.setting import BASE_TYPE
from conf.setting import PROXY_HTTP, PROXY_HTTPS
from conf.setting import PROXY_VERIFY
from Crawler.BaseParser import BaseParser
from Crawler.DataOutput import DataOutput
# from Crawler.reviewsParser import ReviewsParser
from utils.decorator import timer


class BaseDownload:
    def __init__(self):
        pass


def is_RobotCheck(html_code):
    pattern = re.compile('Robot Check', re.S)
    RobotCheck = pattern.findall(html_code)
    if len(RobotCheck) > 0:
        return True
    return False


# @timer
@retry(stop_max_attempt_number=15)
def get_html_useRequest(url, ua, ip, cookie, debug_log, referer, ipQ, urlQ=None, timeout=90, retry=1, goodsUrl='', url_type='', asin=''):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'close',
        'User-Agent': ua,
        'Host': 'www.amazon.com',
        'Referer': referer,
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    proxy = {'https': PROXY_HTTPS, 'http': PROXY_HTTP}
    print(proxy)
    html = ''
    cookies = {}
    status_code = 0
    session = requests
    print('\nheaders: ', headers)
    is_error = False
    if url.startswith('https://www.amazon.com') or url.startswith('http://www.amazon.com'):
        try:
            get_parmas = dict(url=url, headers=headers, proxies=proxy, timeout=timeout)
            if 'proxy.crawlera.com' in proxy.get('https', ''):
                get_parmas['verify'] = PROXY_VERIFY
            response = session.get(**get_parmas)
            status_code = response.status_code
            print('status_code', status_code)
            if status_code == 200 or status_code == 302 or status_code == 404:
                response.encoding = 'utf-8'
                responseCookies = response.cookies
                if not cookie:
                    cookies = responseCookies
                if status_code == 404:
                    if url_type == 'goods' and asin:
                        DataOutput.record_not_found_goods(asin)
                    if url_type == 'tosell' and asin:
                        DataOutput.record_not_found_tosell(asin)
                    html = response.text
                else:
                    html = response.text
                    if "Enter the characters you see below" in html:
                        raise Exception("Exception: Captcha")
                    if "Enter the characters you see below" in html:
                        raise Exception("Exception: block")
                if 'proxy.crawlera.com' not in proxy.get('https', ''):
                    time.sleep(3)
                return html, cookies, is_error
        except Exception as e:
            if status_code != 404:
                is_error = True
                debug_log.error('[%s] get_html_useRequest下载 [%s] 时 [%s]' % (ip, url, e))
                if "NotFound" in str(e):
                    raise Exception("NOT_FOUND")
    else:
        debug_log.error('[%s] get_html_useRequest下载 [%s] url不合法' % (ip, url))
    return html, cookies, is_error


if __name__ == '__main__':
    time1 = time.time()
    # from pprint import pprint
    #
    ip = '192.126.168.2:3128'
    proxy = dict(
        https='https://%s' % (ip),
    )
    print(proxy)
    # html = get_html('https://www.amazon.com/dp/B01C4N6IBA', ip, proxy=proxy)
    # print(type(html))
    # print(len(html))
    # parser = HtmlParser()
    # pprint(parser.parser_goods(html, 'B01C4N6IBA'))
    time2 = time.time()
    print(time2 - time1)
    # from conf.setting import DB_CONFIG, REDIS_CONFIG, BASE_DIR
    #
    UA = UaPond.get_new_ua()
    # print(DB_CONFIG)
    # print(REDIS_CONFIG)
    # print(BASE_DIR)
    print(UA)

