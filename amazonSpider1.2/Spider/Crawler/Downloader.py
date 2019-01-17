#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import sys
sys.path.append("../")

import os
import time
from copy import deepcopy

import requests
from retrying import retry
from fake_useragent import UserAgent

from utils.decorator import timer
from conf.setting import BASE_DIR
from conf.setting import PROXY_VERIFY
from conf.setting import PROXY_HTTP_GET, PROXY_HTTPS_GET
from conf.setting import PROXY_HTTP_POST, PROXY_HTTPS_POST


# user agent
get_ua = lambda location: UserAgent(use_cache_server=False, path=location).random


# 缺省请求头
default_headers = {
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8,tr;q=0.7,ru;q=0.6',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/65.0.3325.181 Chrome/65.0.3325.181 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'close',
}


# 验证码检测
def check_errors(ret):
    if "Enter the characters you see below" in ret:
        if "--debug" in sys.argv or True: print("captcha")
        raise Exception("Exception: Captcha")
    if "Sorry! Something went wrong!" in ret:
        if "--debug" in sys.argv or True: print("block")
        raise Exception("Exception: block")


# requests.get
@retry(stop_max_attempt_number=10)
def get_use_requests(params):
    '''
    :param params: need the dict
    :return:
    '''
    try:
        # 必要参数
        url = params['url']
    except KeyError:
        # 模拟位置参数, 缺则报错
        raise Exception('Required parameter missing: url')

    # 用于动态调整参数
    need_param = dict(
        headers=None,
        cookies=None,
        proxies=None,
        verify=None,
        timeout=180,
    )
    # 过滤参数
    need_param = filter_params(need_param=need_param, params=params)
    the_headers = deepcopy(default_headers)
    try:
        # 设置'User-Agent'
        location = os.path.join(BASE_DIR, 'config/UAPOND.json')
        the_headers['User-Agent'] = get_ua(location)
        # 检查headers, 设置缺省值
        need_param.setdefault('headers', the_headers)
        need_param['url'] = url
        print(get_use_requests.__name__, params.get('num'), need_param)
        resp = requests.get(**need_param)
        print(resp)
        check_errors(resp.text)
        time.sleep(3)
        return resp.text, resp, need_param
    except Exception as e:
        if "NotFound" in str(e):
            raise Exception("NOT_FOUND")
        raise e


# requests.post
@retry(stop_max_attempt_number=10)
def post_use_requests(params):
    '''
    :param params: need the dict
    :return:
    '''
    try:
        # 必要参数
        url = params['url']
        data = params['data']
        user_anget = params['user_anget']
    except KeyError:
        # 模拟位置参数, 缺则报错
        raise Exception('Required parameter missing: url, user_anget')
    # 用于动态调整参数
    need_param = dict(
        headers=None,
        cookies=None,
        proxies=None,
        verify=None,
        timeout=180,
    )
    # 过滤参数
    need_param = filter_params(need_param=need_param, params=params)
    the_headers = deepcopy(default_headers)
    try:
        # 设置'User-Agent'
        the_headers['User-Agent'] = user_anget
        # 检查headers, 设置缺省值
        need_param.setdefault('headers', the_headers)
        need_param['url'] = url
        need_param['data'] = data
        print(post_use_requests.__name__, params.get('num'), need_param)
        time.sleep(3)
        resp = requests.post(**need_param)
        check_errors(resp.text)
        return resp.text, resp, need_param
    except Exception as e:
        if "NotFound" in str(e):
            raise Exception("NOT_FOUND")
        raise e


# 参数过滤
def filter_params(need_param=None, params=None):
    if type(need_param) is not dict or type(params) is not dict:
        return
    give_up_params = []
    for param in need_param:
        need_param[param] = params.get(param, None)
    for param in need_param:
        if need_param[param] is None:
            give_up_params.append(param)
    # print(give_up_params)
    for param in give_up_params:
        need_param.pop(param)
    return need_param


# get下载器
def download_get(**kwargs):
    return get_use_requests(kwargs)


# post下载器
def download_post(**kwargs):
    return post_use_requests(kwargs)


# 库存下载器
@timer
def post_inventory(**kwargs):
    proxy = {'https': PROXY_HTTPS_POST, 'http': PROXY_HTTP_POST}
    kwargs.setdefault('proxies', proxy)
    if 'proxy.crawlera.com' in kwargs.get('proxies').get('https', ''):
        kwargs['verify'] = PROXY_VERIFY
    return download_post(**kwargs)


# 产品下载器
@timer
def get_product(**kwargs):
    '''
    :param
        必要参数: url=string
        headers=dict,
        cookies=cookiesjar,
        proxies=dict,
        verify=string,
        timeout=int,
    :return: resp.text, resp, need_param
    '''
    proxy = {'https': PROXY_HTTPS_GET, 'http': PROXY_HTTP_GET}
    kwargs.setdefault('proxies', proxy)
    if 'proxy.crawlera.com' in kwargs.get('proxies').get('https', ''):
        kwargs['verify'] = PROXY_VERIFY
    return download_get(**kwargs)


if __name__ == '__main__':
    pass

