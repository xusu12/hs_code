#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")

import re
import time
from datetime import datetime

import lxml.etree
from lxml.html import etree
from lxml.html import tostring

from utils.util import return_PST


def get_the_time():
    # 日期格式
    date_str = '%Y%m%d'
    # 时间格式
    time_str = '%Y%m%d%H%M%S'

    # 当天的日期对象
    the_day = datetime.now()
    the_hour = the_day.hour
    pstNow = return_PST()
    pstHour = pstNow.hour
    # print(1.1, the_day)
    # 当天日期字符串
    date_str = the_day.strftime(date_str)
    # 当天15点整字符串
    the_day_str = '%s150000' % (date_str)
    # 当天15点的时间对象
    time_day = time.strptime(the_day_str, time_str)
    # print(1, time_day)

    the_time = time.mktime(time_day)
    # 当天15点时间戳
    the_date_time = the_time
    # 昨天15点时间戳
    old_date_time = the_date_time - 86400

    # 如果过了太平洋时间0点了, 需要另外计算.
    if 10 >= pstHour >= 0 and 15 <= the_hour <= 23:
        the_date_time = the_time + 86400
        old_date_time = the_time

    return the_date_time, old_date_time


# 解析函数
# @timer
def get_data(xpath_obj=None, xpath_list=None, pattern_list=None, pattern_str=None, url_type=None):
    result = []
    if pattern_list is not None and pattern_str is not None :
        if type(pattern_str) is str:
            for pattern in pattern_list:
                data = []
                try:
                    data = pattern.findall(pattern_str)
                except Exception as e:
                    print('pattern, {}, extract, {} unsuccessful, error, {}'.format(pattern, url_type, e))
                if len(data) > 0:
                    # print('pattern, {}, extract, {} successful, result, {}'.format(pattern, url_type, data))
                    result = data
                    return result

    if xpath_obj is not None and xpath_list is not None:
        if type(xpath_obj) is lxml.etree._Element:
            for xpath in xpath_list:
                data = []
                try:
                    data = xpath_obj.xpath(xpath)
                except Exception as e:
                    print('xpth, {}, extract, {}, error, {}'.format(xpath, url_type, e))
                if len(data) > 0:
                    # print('xpth, {}, extract, {}, result, {}, type, {}'.format(xpath, 'succeed', data, type(data)))
                    result = data
                    return result

    return result


# 解析基类
class Parse:
    @staticmethod
    # @timer
    def get_new_data(xpath_obj=None, xpath_list=None, pattern_list=None, pattern_str=None, url_type=None):
        parameter = dict(
            xpath_obj=xpath_obj,
            xpath_list=xpath_list,
            pattern_list=pattern_list,
            pattern_str=pattern_str,
            url_type=url_type,
        )
        data = get_data(**parameter)
        return data


# 解析库存
class InventoryParser(Parse):


    @staticmethod
    def get_post_data(params):
        try:
            # 必要参数
            asin = params['asin']
            xpath_obj = params['xpath_obj']
        except KeyError:
            # 模拟位置参数, 缺则报错
            raise Exception('Required parameter missing: asin, xpath_obj')
        # html = str(tostring(xpath_obj), encoding='utf-8')
        # print(html)
        # with open('%s_post_data.html' % (asin), 'w') as f: f.write(html)
        offerListingID = xpath_obj.xpath('//*[@id="offerListingID"]/@value')[0] if xpath_obj.xpath(
            '//*[@id="offerListingID"]/@value') else ''
        if not offerListingID:
            offerListingID = xpath_obj.xpath('//*[@name="offeringID.1"]/@value')[0] if xpath_obj.xpath(
                '//*[@name="offeringID.1"]/@value') else ''
        if not offerListingID:
            return None
        sessionID = xpath_obj.xpath('//*[@id="session-id"]/@value')[0] if xpath_obj.xpath('//*[@id="session-id"]/@value') else ''
        if not sessionID:
            sessionID = xpath_obj.xpath('//*[@name="session-id"]/@value')[0] if xpath_obj.xpath('//*[@name="session-id"]/@value') else ''

        post_datas = {
            "session-id": sessionID,
            "sr": "8-11",
            "signInToHUC": 0,
            "metric-asin." + asin: 1,
            "registryItemID.1": "",
            "registryID.1": "",
            "quantity.1": 999,
            "offeringID.1": offerListingID,
            "isAddon": 0,
            "submit.addToCart": "Add+to+cart"
        }
        return post_datas


    @staticmethod
    def get_qty(params):
        try:
            # 必要参数
            html_code = params['html_code']
            xpath_obj = params['xpath_obj']
        except KeyError:
            # 模拟位置参数, 缺则报错
            raise Exception('Required parameter missing: html_code, xpath_obj')
        qtydt = 0
        xpath_list = [
            '//*[text()="Cart subtotal"]/../..//text()',  # 案例 B01G8UTA3S B000YJ2SLG 076115678x
        ]
        result_lsit = Parse.get_new_data(xpath_list=xpath_list, xpath_obj=xpath_obj)
        if len(result_lsit) > 0:
            item_list = []
            for item in result_lsit:
                item = item.lstrip().strip()
                item_list.append(item)
            item_str = ''.join(item_list)
            result_list = re.findall("Cart subtotal.*?\((\d+) item[s]*\):.*?\$[\d\.,]+", item_str)
            if len(result_list) > 0:
                result = result_list[0].lstrip().strip()
                if result.isdigit():
                    xpath_list = [
                        '//div[@id="huc-v2-box-warning"]//p/text()',
                    ]
                    limit_list = Parse.get_new_data(xpath_list=xpath_list, xpath_obj=xpath_obj)
                    if len(limit_list) > 0:
                        if re.search("from this seller has a limit of %s per customer" % (result), " ".join(limit_list)):
                            qtydt = 2
                    return int(result), qtydt

        return -1, 1

# 是否二手
def is_buy_used(**kwargs):
    if kwargs.get('html_code', ''):
        pattern_list = [
            re.compile('Buy used:'),
        ]
        need_param = dict(
            pattern_list=pattern_list,
            pattern_str=kwargs.get('html_code'),
            url_type=kwargs.get('url_type'),
        )
        if len(get_data(**need_param)) > 0:
            return True
    return False


# 是否prime
def is_try_prime(**kwargs):
    if kwargs.get('html_code', ''):
        pattern_list = [
            re.compile('Try Prime free for 30 days'),
            re.compile('<a id="pe-bb-signup-button-announce".*?Try Prime.*?</', re.S),
        ]
        need_param = dict(
            pattern_list=pattern_list,
            pattern_str=kwargs.get('html_code'),
            url_type=kwargs.get('url_type'),
        )
        if len(get_data(**need_param)) > 0:
            return True
    return False


# 是否404
def is_not_found(**kwargs):
    if kwargs.get('status_code', None) == 404:
        return True
    elif kwargs.get('html_code', ''):
        pattern_list = [
            re.compile('Page Not Found', re.S),
            re.compile('Sorry! We couldn', re.S),
            re.compile('Dogs of Amazon', re.S),
        ]
        need_param = dict(
            pattern_list=pattern_list,
            pattern_str=kwargs.get('html_code'),
            url_type=kwargs.get('url_type'),
        )
        if len(get_data(**need_param)) > 0:
            return True
    return False


# 是否验证码
def is_robot_check(**kwargs):
    if kwargs.get('html_code', ''):
        pattern_list = [
            re.compile('Robot Check', re.S),
            re.compile('Bot Check', re.S),
            re.compile('Amazon CAPTCHA', re.S),
        ]
        need_param = dict(
            pattern_list=pattern_list,
            pattern_str=kwargs.get('html_code'),
            url_type=kwargs.get('url_type'),
        )
        if len(get_data(**need_param)) > 0:
            return True
    return False


# 是否不可售
def is_currently_unavailable(**kwargs):
    if kwargs.get('xpath_obj') is not None:
        xpath_list = [
            '//*[contains(@id, "uybox")]//*[contains(text(), "urrently unavailable")]//text()',
            '//*[contains(@id, "uyBox")]//*[contains(text(), "urrently unavailable")]//text()',
        ]
        need_param = dict(
            xpath_list=xpath_list,
            xpath_obj=kwargs.get('xpath_obj'),
            url_type=kwargs.get('url_type'),
        )
        result_list = get_data(**need_param)
        if len(result_list) > 0:
            the_html = ''.join(result_list)
            if re.search('[Cc]urrently unavailable', the_html):
                return True
        return False
    return False


# 是否buying options
def is_see_all_buying_options(**kwargs):
    if kwargs.get('html_code', ''):
        pattern_list = [
            re.compile('id="buybox-see-all-buying-choices-announce"', re.S),
            re.compile('See All Buying Options', re.S),
        ]
        need_param = dict(
            pattern_list=pattern_list,
            pattern_str=kwargs.get('html_code'),
            url_type=kwargs.get('url_type'),
        )
        if len(get_data(**need_param)) > 0:
            return True
    return False


# 是否没有库存
def is_not_qty(**kwargs):
    if kwargs.get('xpath_obj') is not None:
        xpath_list = [
            '//*[@id="wayfinding-breadcrumbs_feature_div"]//text()|//*[@id="nav-subnav"]//text()',
        ]
        need_param = dict(
            xpath_list=xpath_list,
            xpath_obj=kwargs.get('xpath_obj'),
            url_type=kwargs.get('url_type'),
        )
        result_list = get_data(**need_param)
        if len(result_list) > 0:
            html = ''.join(result_list)
            pattern_list = [
                            # not_qty 不拿库存的类别
                re.compile('Home & Business Services'),   # 家庭服务
                re.compile('Prime Video'),                # 电影类
                re.compile('Apps & Games'),               # app类
                re.compile('Kindle Store'),               # kindle 电子书
                re.compile('Gift Card'),                  # Gift Cards 定制卡片
                re.compile('Handmade Products'),          # 手工制品
                re.compile('Books'),                      # 书籍类(业务不拿)
                re.compile('Movies & TV'),                # 视频类
                re.compile('Digital Music'),              # 数字音乐
                re.compile('Alexa Skill'),                # Alexa Skill 类
                re.compile('Download Store'),             # 下载类音乐等(一个小类.)
                # re.compile('Home & Kitchen'),             # Home & Kitchen (要继续拿库存了)
            ]
            need_param = dict(
                pattern_list=pattern_list,
                pattern_str=html,
                url_type=kwargs.get('url_type'),
            )
            if len(get_data(**need_param)) > 0:
                return True
    return False


# 是否需要定制
def if_customize(**kwargs):
    if kwargs.get('xpath_obj') is not None:
        xpath_list = [
            '//*[@id="buybox"]//*[contains(text(), "Customize Now")]',
            '//*[@id="buybox"]//*[contains(text(), "This product needs to be customized before adding to cart")]',
        ]
        need_param = dict(
            xpath_list=xpath_list,
            xpath_obj=kwargs.get('xpath_obj'),
            url_type=kwargs.get('url_type'),
        )
        result_list = get_data(**need_param)
        if len(result_list) > 0:
                return True
    return False


# 产品分析
def product_analyze(**kwargs):
    result = dict(
        not_qty=is_not_qty,
        buy_used=is_buy_used,
        try_prime=is_try_prime,
        not_found=is_not_found,
        robot_check=is_robot_check,
        unavailable=is_currently_unavailable,
        buying_options=is_see_all_buying_options,
        customize=if_customize
    )
    kwargs.setdefault('pattern_str', kwargs.get('html_code', ''))
    kwargs.setdefault('xpath_obj', etree.HTML(kwargs.get('html_code', '')))
    for item in result:
        result[item] = result[item](**kwargs)
    result.setdefault('asin', kwargs.get('asin'))
    return result