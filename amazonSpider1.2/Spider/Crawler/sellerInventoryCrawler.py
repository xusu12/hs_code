#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import sys
sys.path.append("../")

import re

from lxml.html import etree

from Crawler.productUtils import InventoryParser
from Crawler.Downloader import post_inventory, get_product
from conf.setting import PROXY_HTTP_POST, PROXY_HTTPS_POST


'''
卖家库存获取
    url = 'https://www.amazon.com'
    html_code, resp, param = get_product(url=url)
    session = resp.cookies.get('session-id')
    print(resp.cookies)
    print(session)
    print(param)
    post_datas = {
        "session-id": session,
        "quantity": 999,
        "offerListingID": pams.get('offering'),
        "submit.addToCart": "Add+to+cart"
    }
    post_url = 'https://www.amazon.com/gp/product/handle-buy-box/ref=dp_start-bbf_1_glance'
'''
def is_continue(**kwargs):
    pattern = re.compile('<form.*?action="/gp/verify-action/templates/add-to-cart/ordering".*?>', re.S)
    if pattern.findall(kwargs.get('post_html', '')):
        return True
    return False


def get_quantity(**kwargs):
    '''
    解析库存主要逻辑
    :param dict parms: 必须参数, 一个字典, 含有html_code, xpath_obj 两个必备字段
    :return:
    '''
    return InventoryParser.get_qty(kwargs)


# 公共爬虫接口
def scrape_inventory(parms: dict, retry=3) -> dict:
    '''
    爬取库存主要逻辑(可以对接定时器, 进行任务重试)
    :param dict parms: 必须参数, 一个字典, 含有asin, sname, seller_id, offering, fba, price几个必备字段
    :return:
    '''
    # 访问亚马逊首页, 获得cookie
    url = 'https://www.amazon.com'
    # 使用post代理, 速度更快.
    proxy = {'https': PROXY_HTTPS_POST, 'http': PROXY_HTTP_POST}
    amazon_html_code, resp, param = get_product(url=url, proxies=proxy)
    session_id = resp.cookies.get('session-id')
    print(resp.cookies)
    print(session_id)
    print(param)
    # 获取购物车post参数
    post_datas = {
        "ASIN": parms.get('asin'),
        "session-id": session_id,
        "quantity": 999,
        "offerListingID": parms.get('offering_id'),
        "submit.addToCart": "Add+to+cart"
    }
    # 添加购物车接口
    post_url = 'https://www.amazon.com/gp/product/handle-buy-box/ref=dp_start-bbf_1_glance'
    # 获取购物车页面
    html_code, resp, param = post_inventory(url=post_url, data=post_datas, cookies=resp.cookies, user_anget=param['headers'].get('User-Agent'))
    print(len(html_code), resp.cookies, parms)
    # 如果需要二次提交(说明参数缺失)
    if is_continue(post_html=html_code):
        print('%s_next_post_continue.html' % (parms.get('asin')))
        from conf.setting import develop_e_name, BASE_TYPE
        if BASE_TYPE == develop_e_name:
            with open('%s_next_post_continue.html' % (parms.get('asin')), 'w', encoding='utf-8') as f:
                f.write(html_code)

    else:
        from conf.setting import develop_e_name, BASE_TYPE
        if BASE_TYPE == develop_e_name:
            with open('%s_inv_post.html' % (parms.get('asin')), 'w', encoding='utf-8') as f:
                f.write(html_code)

        # 解析库存
        qty, qtydt = get_quantity(html_code=html_code, xpath_obj=etree.HTML(html_code))
        if qty <= 0 and retry > 0:
            return scrape_inventory(parms, retry=retry - 1)
        # 打包数据
        parms['qty'] = qty
        parms['qtydt'] = qtydt
        if qty <= 0:
            crawler_state = 2
        else:
            crawler_state = 1
        parms['crawler_state'] = crawler_state
        return parms