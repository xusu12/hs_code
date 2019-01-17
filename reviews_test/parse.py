#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# from gevent import monkey
# monkey.patch_all()
import sys
sys.path.append("../")
# import os
import re
import time
# from random import randint
from random import choice
from urllib import parse
from datetime import datetime
import hashlib
from threading import Thread
from multiprocessing.pool import ThreadPool
from copy import deepcopy
from functools import wraps
from bs4 import BeautifulSoup

import demjson
import pytz
import lxml.etree
from lxml import etree
from lxml.html import tostring
import requests
from fake_useragent import UserAgent
from retrying import retry
from redis import Redis
from rediscluster import StrictRedisCluster

from flask import Flask
from flask import request
from flask import json
from flask import jsonify

# 配置
from config import BASE_TYPE
from config import PROXY_META
from config import PROXY_VERIFY
from config import UAPOND
from config import UA_FILE
from config import T_NUM
from config import CACHE_TIME
from config import SAVE_TIME
from config import REDIS_CONFIG
from config import BASE_HEADERS

#from goods_html import goods_html1


def timer(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        timenow = lambda: time.time()
        time1 = timenow()
        print('function: %s start' % (func.__name__))
        result = func(*args, **kwargs)
        print('function:%s timer:%.6f' % (func.__name__, timenow() - time1))
        return result
    return wrap


app = Flask(__name__)


@app.route('/py')
def hello_world():
    return 'Hello World!'

# redis 对象
# the_redis = lambda: StrictRedisCluster(startup_nodes=REDIS_CONFIG[BASE_TYPE], decode_responses=True) \
#     if BASE_TYPE == 'production' or BASE_TYPE == 'pre_release' else Redis(**REDIS_CONFIG[BASE_TYPE])
# R = the_redis()
# 缓存时间
cache_time = CACHE_TIME if BASE_TYPE != 'development' else 720
save_time = SAVE_TIME if BASE_TYPE != 'development' else 7200

# 数据缓存字典
PUBLIC_DATA = dict(
    data=[],
    msg=[],
    ret=0,
)

def get_porxy():
    proxyMeta = PROXY_META
    # print(proxyMeta)
    # 设置 http和https访问都是用HTTP代理
    proxies = {
        "http": proxyMeta,
        "https": proxyMeta,
    }
    return proxies

def get_user_agent():
    location = UA_FILE
    # print('location', location)
    try:
        UA = UserAgent(use_cache_server=False, path=location)
        # print(UA)
        ua = UA.random
        # print(ua)
        if ua:
            return ua
    except Exception as e:
        print('get_user_agent error [%s]' % e)
    return choice(UAPOND)


def return_PST():
    # 设置为洛杉矶时区
    time_zone = pytz.timezone('America/Los_Angeles')
    dateNow = datetime.now(time_zone)
    return dateNow


def is_RobotCheck(html_code):
    pattern = re.compile('Robot Check', re.S)
    RobotCheck = pattern.findall(html_code)
    if len(RobotCheck) > 0:
        return True
    return False


class BaseParser:
    @staticmethod
    def is_RobotCheck(html_code):
        return is_RobotCheck(html_code)

    @staticmethod
    def is_page_not_found(html_code):
        not_found_patterns = [
            re.compile('Page Not Found', re.S),
            re.compile('Sorry! We couldn', re.S),
            re.compile('Dogs of Amazon', re.S),
        ]
        not_found = BaseParser.get_new_data(pattern_list=not_found_patterns, html_code=html_code)
        if len(not_found) > 0:
            return True
        return False

    # 获取新的数据
    @staticmethod
    def get_new_data(xpath_obj=None, xpath_list=None, pattern_list=None, html_code=None, url_type='product'):
        pattern_str = html_code
        result = []
        if pattern_list and pattern_str:
            if type(pattern_str) is str:
                for pattern in pattern_list:
                    data = []
                    try:
                        # if url_type=='soldby':
                        #     print('soldy: ', pattern)
                        data = pattern.findall(pattern_str)
                    except Exception as e:
                        print('pattern, {}, extract, {} unsuccessful, error, {}'.format(pattern, url_type, e))
                    if len(data) > 0:
                        # print('pattern, {}, extract, {} successful, result, {}'.format(pattern, url_type, data))
                        result = data
                        return result

        if xpath_obj and xpath_list:
            if type(xpath_obj) is lxml.etree._Element:
                for xpath in xpath_list:
                    data = []
                    try:
                        # print('xpth, {}, extract, {}, result, {}, type, {}'.format(xpath, 'succeed', data, type(data)))
                        data = xpath_obj.xpath(xpath)
                    except Exception as e:
                        print('xpth, {}, extract, {}, error, {}'.format(xpath, url_type, e))
                    if len(data) > 0:
                        # print('xpth, {}, extract, {}, result, {}, type, {}'.format(xpath, 'succeed', data, type(data)))
                        result = data
                        return result

        return result


    @staticmethod
    def filter_str(content):
        '''清洗文本'''
        if not (isinstance(content, str) or isinstance(content, bytes)):
            return content
        sublist = ['<p.*?>', '</p.*?>', '<b.*?>', '</b.*?>', '<div.*?>', '</div.*?>',
                   '</br>', '<br />', '<ul>', '</ul>', '<li>', '</li>', '<strong>',
                   '</strong>', '<table.*?>', '<tr.*?>', '</tr>', '<td.*?>', '</td>',
                   '\r', '\n', '&.*?;', '&', '#.*?;', '<em>', '</em>']
        try:
            for substring in [re.compile(string, re.S) for string in sublist]:
                content = str(re.sub(substring, "", content)).strip()
        except:
            raise Exception('Error ' + str(substring.pattern))
        return content


class GoodsParser(BaseParser):
    def __init__(self):
        self.url = None
        self.html_code = None
        # self.xpath_obj = etree.HTML(html_code) if html_code else None
        self.quantity = -1
        self.qtydt = 0
        self.quantity_state = 0
        self.head_html = None
        self.desc_html = None
        self.buy_box_html = None
        # self.soup = BeautifulSoup(html_code, 'lxml') if html_code else None

    # 解析商品详情
    #@timer
    def parser_goods(self, html_code, the_asin, the_price, the_brand, the_rc, the_image, monitor_type=0, ip='', ua='', info_log=None,
                     debug_log=None,download_url='', cookies=None):
        '''
        品牌
        asin
        图片
        标题
        价格
        是否fba
        特点
        黄金购物车卖家
        销量排名
        评分
        评论数
        更多图片
        '''
        if not html_code:
            return
        self.asin = the_asin
        self.html_code = html_code
        self.xpath_obj = etree.HTML(html_code)
        self.head_html = self.get_head_html(self.xpath_obj)
        self.soup = BeautifulSoup(html_code, 'lxml')
        # self.desc_html = self.get_description_html(self.xpath_obj)
        self.buy_box_html = self.get_buy_box_html(self.xpath_obj)
        self.cookie = cookies
        self.ip = ip
        self.ua = ua
        self.debug_log = debug_log
        # bsr_data = {}
        if download_url:
            self.url = download_url
        if self._is_Currently_unavailable():
            asin_state = 2
        else:
            asin_state = 3
        gimage = self._get_image_group()
        title = self._get_title()  # 标题
        image = GoodsParser._get_log_image(gimage)  # 图片
        if not image:
            image = self._get_image()
        brand = self._get_brand()  # 品牌
        sname = self._get_seller_name()  # 卖家
        price = self._get_discount_price()  # 产品价格
        if price < 1:
            price = self._get_cart_price()
        bsr, bsr_dict_list = self._get_bsrRank(html_code)  # 销量排名（取大类排名包含(See Top 100)字样）
        qa_count = self._get_qa_count()  # 问答数
        rc = self._get_review_count()  # 评论数
        print(rc)
        rrg = self._get_review_rating()  # 综合评分
        feature = self._get_feature()  # 商品说明
        image_more = GoodsParser._get_image_more(gimage)  # 更多图片
        if not image_more:
            image_more = self._get_ima_more()
        if rc == 0:
            rrg = 0
        if the_price - price > the_price * 0.5 and the_price > 0:
            price = the_price
        if not brand and the_brand:
            brand = the_brand
        if rc <=0 and the_rc > 0:
            rc = the_rc
            rrg = rrg
        if not image and the_image:
            image = the_image
        fba = self._get_fba()
        goods_data = dict(
            asin=the_asin,  # asin
            # pasin=pasin,  # 父asin
            title=title,  # 标题
            image=image,  # 图片
            brand=brand,  # 品牌
            price=price,  # 产品价格
            # cart_price=cart_price,
            # quantity=quantity,  # 库存
            fba=fba,
            # sale_price=discount_price,  # 优惠价格
            sname=sname,  # 卖家
            # seller_id=seller_id,  # 商家id
            # ts_min_price=ts_min_price,  # 跟卖最低价格
            # to_sell=to_sell,  # 跟卖数
            # byb=byb,  # 是否有黄金购物车按钮, 0(为否)
            bsr=bsr,  # 销量排名  65 （取下面三个Best Sellers Rank中最小的那个）
            bsr_info=bsr_dict_list, # 销量排名详情
            rc=rc,  # 评论数
            rrg=rrg,  # 综合评分
            # r5p=r5p,  # 5星评价百分比
            # r4p=r4p,  # 4星评价百分比
            # r3p=r3p,  # 3星评价百分比
            # r2p=r2p,  # 2星评价百分比
            # r1p=r1p,  # 1星评价百分比
            feature=feature,  # 商品说明
            getinfo_tm=int(time.time() * 1000),  # 得到信息时间
            # bs1=best_seller_1,  # 分类销量是否第一, 0(为否)
            qc=qa_count,  # 问答数
            # release_date=release_date,  # 发布日期
            # asin_type=asin_type,
            image_more=image_more,  # 更多图片
            # variant=variant,  # 变体
            asin_state=asin_state,
            # dpre=dpre,  # 原价, 只有历史库要存
            # aday=return_PST().strftime("%Y%m%d"),  # 获取数据的太平洋日期
        )
        goods_datas = goods_data
        # print('goods_datas', goods_datas)
        return goods_datas

    @staticmethod
    #@timer
    def get_head_html(xpath_obj):
        result = ''
        xpath_list = [
            '//*[@id="ppd"]',
            '//*[@id="centerCol"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_obj=xpath_obj, xpath_list=xpath_list)
        if len(result_list) > 0:
            result = str(tostring(result_list[0]), encoding='utf-8')
        return result

    @staticmethod
    #@timer
    def get_buy_box_html(xpath_obj):
        result = ''
        xpath_list = [
            '//*[@id="buybox"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_obj=xpath_obj, xpath_list=xpath_list)
        if len(result_list) > 0:
            result = str(tostring(result_list[0]), encoding='utf-8')
        return result

    @staticmethod
    #@timer
    def get_description_html(xpath_obj):
        result = ''
        xpath_list = [
            '//*[@id="detail-bullets"]',
            '//*[@id="descriptionAndDetails"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_obj=xpath_obj, xpath_list=xpath_list)
        if len(result_list) > 0:
            result = str(tostring(result_list[0]), encoding='utf-8')
        return result

    def _is_Home_Business_Services(self, html_code=None):
        'Home & Business Services'
        if not html_code:
            html_code = self.html_code
        xpath_list = [
            '//*[@id="wayfinding-breadcrumbs_feature_div"]'
            '//*[@id="nav-subnav"]'
        ]
        html_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(html_list) > 0:
            html = str(tostring(html_list[0]), encoding='utf-8')
            pattern_list = [
                re.compile('Home & Business Services', re.S),
            ]

            result = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=html)
            if len(result) > 0:
                return True

        return False

    def _is_Currently_unavailable(self, html_code=None):

        if not html_code:
            html_code = self.html_code

        RobotCheck_patterns = [
            re.compile('Currently unavailable', re.S),
            re.compile('[Cc]urrently unavailable', re.S),
        ]

        unavailable = GoodsParser.get_new_data(pattern_list=RobotCheck_patterns, html_code=html_code)

        if len(unavailable) > 0:
            return True

        return False

    def _get_post_url(self, html_code=None):
        'addToCart'
        if html_code is None:
            html_code = self.html_code
        result_url = 'https://www.amazon.com/gp/product/handle-buy-box/ref=dp_start-bbf_1_glance'
        url_xpath = [
            '//*[@id="addToCart"]/@action',
        ]
        url = GoodsParser.get_new_data(xpath_list=url_xpath, xpath_obj=self.xpath_obj)
        if len(url) > 0:
            url1 = url[0].lstrip().strip()
            result_url = parse.urljoin('https://www.amazon.com', url1)
        return result_url

    def _get_fba(self):
        pattern_list = [
            re.compile('[Ff]ulfilled by [Aa]mazon'),
            re.compile('[Ff]ulfilled by [Aa]mazon', re.S),
        ]
        result_list = self.get_new_data(pattern_list=pattern_list, html_code=self.html_code)
        # print('condition1: ', result_list)
        if len(result_list) > 0:
            result = 1
        else:
            result = 0
        return result

    # 销量排名
    #@timer   # 销量排名
    def _get_bsrRank(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        # print(html_code)
        # if self.desc_html:
        #     html_code = self.desc_html
        top_pattern = re.compile('[Ss]ee [Tt]op 100')
        aday = ''#return_PST().strftime("%Y%m%d")
        tm = int(time.time() * 1000)
        bsr_pattern = re.compile('[\d,]+')
        bsrInt = 0
        bsr_tuple_list = []
        xpath_list = [
            '//*[contains(text(), "Sellers Rank")]/..//text()',   # 案例 B01G8UTA3S B000YJ2SLG 076115678x
        ]
        result_list = GoodsParser.get_new_data(xpath_obj=self.xpath_obj, xpath_list=xpath_list)
        style_xpath = ['//*[contains(text(), "Sellers Rank")]/..//style/text()', ]   # 案例 B01G8UTA3S B000YJ2SLG 076115678x
        style_list = GoodsParser.get_new_data(xpath_obj=self.xpath_obj, xpath_list=style_xpath)
        bsrRank_list = []
        if style_list:
            for i in result_list:
                for j in style_list:
                    # print('i', i, '\nj', j)
                    if i != j:
                        # print('bsrRank_list_i:', i)
                        if re.search('[Ss]ellers [Rr]ank', i):
                            i = i.split(':')[0] + ':'
                        i = i.strip().lstrip()
                        # print('bsrRank_list_i1:', i)
                        bsrRank_list.append(i)
        else:
            for i in result_list:
                i = i.strip().lstrip()

                if i:
                    if re.search('[Ss]ellers [Rr]ank', i):
                        i = i.split(':')[0] + ':'
                    bsrRank_list.append(i)

        if bsrRank_list:
            # print('bsrRank_list', bsrRank_list)
            bsr_str = ''.join(bsrRank_list)
            # print('bsr_str: ', bsr_str)
            bsr_str = bsr_str.split(':')[1]
            # print('bsr_str1: ', bsr_str)
            bsr_str_list = bsr_str.split('#')
            # print('bsr_str_list: ', bsr_str_list)
            result_list = []
            if type(bsr_str_list) is list:
                # print('bsr_str_list1', bsr_str_list)
                for item in bsr_str_list:
                    item = item.strip().lstrip()
                    # print('item: ', item)
                    item = ' '.join(item.split('\xa0'))
                    # print('item1: ', item)
                    result_list.append(item)
            bsrint_list = []
            if result_list:
                # print('result_list', result_list)
                for item in result_list:
                    # print('item', item)
                    if item:
                        bsrList = item.split('in')
                        bsrstr = bsrList[0].strip().lstrip()
                        bsrNum = bsr_pattern.search(bsrstr).group(0)
                        # print(bsrstr, 1)
                        # print(bsrNum, 1)
                        # print(bsrList, 12345)
                        bsr1 = bsrList[1:len(bsrList)]
                        # print(bsr1, 121)
                        bsrstring = 'in'.join(bsr1).strip().lstrip()
                        # print(bsrstring, 111)
                        item = bsrstr + ' in ' + bsrstring
                        # print(bsrstr, 1.1)
                        bsrNum = ''.join(bsrNum.split(','))
                        # print(bsrstr, 2)
                        if bsrNum.isdigit():
                            bsrint = int(bsrNum)
                            # print(bsrint, 2.1)
                            bsr_dict = {'bsrNum': bsrint, 'bsrStr': item, 'aday': aday, 'tm': tm}
                            bsr_tuple_list.append(bsr_dict)
                            # print(item, 2.1, 1)

                            if top_pattern.search(item):
                                # print(bsrint, 2.2)
                                bsrInt = bsrint
                            # print(bsrInt, 2.3)
                            bsrint_list.append(bsrint)
                # print(bsrInt, 3)
                if bsrInt < 1:
                    if len(bsrint_list) > 0:
                        bsrInt = min(bsrint_list)
                        # print('bsrInt', bsrInt)
                        # print('bsrTuple_list', bsrTuple_list)
        return bsrInt, bsr_tuple_list

    # 获取标题
    # @timer# 获取标题
    def _get_title(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        result_title = ''
        title_xpath = [
            '//h1[@id="title"]//text()',
        ]
        title = GoodsParser.get_new_data(xpath_list=title_xpath, xpath_obj=self.xpath_obj)
        if len(title) > 0:
            t_list = []
            for t in title:
                t = t.strip().lstrip()
                if t:
                    t_list.append(t)
            if t_list:
                result_title = ''.join(t_list)
        else:
            title_xpath = [
                '//h1[contains(@id, "title")]//span[contains(@id, "Title")]/text()'  # 图书可能存在三列标题 案例　076115678X
                '//*[@id="btAsinTitle"]/text()',
                '//h1[@data-automation-id="title"]/text()',  # 电影类别的title
                '//*[@id="mas-title"]//span[contains(@class, "a-text-bold")]/text()',  # 特殊案例 B071FW2BB6
            ]
            title = GoodsParser.get_new_data(xpath_list=title_xpath, xpath_obj=self.xpath_obj)
            if len(title) > 0:
                result_title = title[0].strip().lstrip()


        if len(result_title) > 255:
            result_title = result_title[0:247] + '...'
        return result_title

    # 获取图片组
    #@timer# 获取图片组
    def _get_image_group(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        image_patterns = [
            re.compile("colorImages'.+?{(.+)'colorToAsin", re.S),

        ]
        image_json = GoodsParser.get_new_data(html_code=html_code, pattern_list=image_patterns)
        # print('_get_image_group.image_json: ', image_json)
        if image_json is None:
            return []
        else:
            img_str = ''.join(image_json).strip()
            if 'initial' in img_str and img_str.endswith('},'):
                son_goods_list1 = img_str.rstrip('},')
                img_str = son_goods_list1.lstrip("'initial':").strip()
                image_json = demjson.decode(img_str) if img_str else None
            gimage = [{'hiRes': i['large'], 'variant': i['variant']} for i in image_json]
            # print('_get_image_group.gimage: ', gimage)
            return gimage

    # 获取urltitle(存redis拼url用)
    @staticmethod
    def get_urltitle(asin, html_code):
        urlTitle = ''
        pattern_list = [
            re.compile('<link rel="canonical.+?com/([A-Za-z0-9\-]+)/dp/.*?/>', re.S),
        ]
        urlT = GoodsParser.get_new_data(html_code=html_code, pattern_list=pattern_list)
        # print('urlT', urlT, asin)
        if len(urlT):
            urlTitle = urlT[0]
        return urlTitle

    # 获取主图
    @staticmethod
    def _get_log_image(gimage):
        log_image = ''
        if len(gimage) > 0:
            log_image = gimage[0].get('hiRes', '')
        return log_image

    def _get_image(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        result = ''
        img_xpath = [
            '//*[@id="landingImage"]/@src',
            '//*[@id="ebooksImgBlkFront"]/@src',
            '//*[@id="gc-standard-design-image"]/@src',
        ]
        imgs = GoodsParser.get_new_data(xpath_list=img_xpath, xpath_obj=self.xpath_obj)
        if len(imgs) > 0:
            img = imgs[0].strip().lstrip()
            return img
        else:
            xpath_list = [
                '//*[@id="imgBlkFront"]',
                '//*[contains(@id, "img")]'
                '//*[contains(@id, "image")]'
                '//*[contains(@id, "images")]'
            ]
            result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
            if len(result_list) > 0:
                html = str(tostring(result_list[0]), encoding='utf-8')
                pattern_lsit = [
                    re.compile('http.*?amazon.com/images.*?jpg'),
                ]
                result1 = GoodsParser.get_new_data(pattern_list=pattern_lsit, html_code=html)
                if len(result1) > 0:
                    result = result1[0].strip().lstrip()
            return result

    # 更多图片
    @staticmethod
    def _get_image_more(gimage):
        gimage_list = []
        variant_list = []
        result_gimage = ''
        # result_variant = ''
        if len(gimage) > 0:
            more_image = gimage[1:]
            # print(more_image)
            for itme in more_image:
                image = itme.get('hiRes') or ''
                # variant = itme.get('variant', '')
                # print(image)
                if image:
                    gimage_list.append(image)
                    # if variant:
                    #     variant_list.append(variant)
            if len(gimage_list) > 0:
                result_gimage = r'%s' % ('\n'.join(gimage_list))
                # if len(variant_list):
                #     result_variant = r'%s' % ('\n'.join(variant_list))
        # print('_get_image_more.result_gimage: ', result_gimage)
        return result_gimage

    def _get_ima_more(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        img_xpath = [
            '//*[@id="altImages"]//img/@src',
        ]
        result_gimage = ''
        imgs = GoodsParser.get_new_data(xpath_list=img_xpath, xpath_obj=self.xpath_obj)
        if imgs:
            result_gimage = r'%s' % ('\n'.join(imgs))
        return result_gimage

    # 获取品牌
    # @timer# 获取品牌
    def _get_brand(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        if self.head_html:
            html_code = self.head_html
        result_brand = ''
        brand_xpath = [
            '//*[@id="brand"]/text()',
            '//*[@id="gc-brand-name-link"]/text()',
            '//*[@id="bylineInfo"]//a[contains(@href, "dp_byline_sr_book_1")]/text()',
            '//*[@id="bylineInfo"]//a[contains(@href, "dp_byline_sr_ebooks_1")]/text()',
            '//*[@id="bylineInfo"]//a[contains(@href, "dp_byline_cont_book_1")]/text()',
            '//*[@id="bylineInfo"]//a[contains(@href, "dp_byline_cont_ebooks_1")]/text()',
            '//*[@id="bylineInfo"]//a[contains(@href, "dp_byline_cont_book")]/text()',
            '//*[@id="bylineInfo"]//a[contains(@href, "dp_byline_cont_ebooks")]/text()',
            '//*[@id="bylineInfo"]//a[contains(@href, "dp_byline_sr_book")]/text()',
            '//*[@id="bylineInfo"]//a[contains(@href, "dp_byline_sr_ebooks")]/text()',
            '//div[@class="a-section a-spacing-medium"]//div[@id="mbc"]/@data-brand',
            '//*[@class="a-row item-title"]/span/text()',
            '//*[@class="qpHeadline"]/b/text()',
            '//*[@id="mbc"]/@data-brand',
            '//*[@id="bylineInfo"]/text()',
        ]
        brand = GoodsParser.get_new_data(xpath_list=brand_xpath, xpath_obj=self.xpath_obj)
        # print(brand)
        if len(brand) > 0:
            result_brand = brand[0].lstrip().strip()
        else:
            brand_xpath = [
                '//img[@id="brand"]/@src',
                '//img[@id="logoByLine"]/@src'
            ]
            brand_url = GoodsParser.get_new_data(xpath_list=brand_xpath, xpath_obj=self.xpath_obj)
            if brand_url:
                result_brand = brand_url[0].strip().lstrip()


        return result_brand

    # 获取父asin
    # @timer# 获取父asin
    def _get_parent_asin(self, html_code=None):
        '''
        "currentAsin" : "B00CM220CK",
            "parentAsin" : "B017X9JIBM",
        :param html_code:
        :return:
        '''
        if html_code is None:
            html_code = self.html_code
        asin_patterns = [
            re.compile('parentAsin".*?"([A-Za-z0-9]+?)",', re.S),
            re.compile('parentAsin".*?"(.+?)",', re.S),
        ]
        asin = GoodsParser.get_new_data(pattern_list=asin_patterns, html_code=html_code)
        if len(asin) > 0:
            asin = asin[0]
            asin = GoodsParser.filter_str(asin)
            return asin
        else:
            return ''

    # 获取当前asin(用来做逻辑校验)
    def _get_current_asin(self, html_code=None):
        '''
        "currentAsin" : "B00CM220CK",
            "parentAsin" : "B017X9JIBM",
        :param html_code:
        :return:
        '''
        if html_code is None:
            html_code = self.html_code
        asin_xpath = [
            '//input[@id="ASIN"]/@value',
        ]
        asin = GoodsParser.get_new_data(xpath_list=asin_xpath, xpath_obj=self.xpath_obj)
        if len(asin) > 0:
            asin = asin[0]
            asin = GoodsParser.filter_str(asin)
            return asin
        else:
            return ''

    # 获取商家名称
    #@timer# 获取商家名称
    def _get_seller_name(self, html_code=None):
        if self._is_Currently_unavailable():
            return ''
        if html_code is None:
            html_code = self.html_code
        sold_by = ''
        xpath_list = [
            '//*[contains(text(), "Sold by")]/..',
            '//*[contains(text(), "In Stock")]/../../../..',
            '//*[@id="merchant-info"]/..',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            soldby_html = ''
            for item in result_list:
                soldby = item.xpath('//a[contains(@href, "dp_merchant_link")]/text()')
                if soldby:
                    return soldby[0]
                soldby_byte = tostring(item)
                #print(soldby_byte)# = tostring(item)
                soldby_html += str(soldby_byte, encoding='utf-8')
                #print(soldby_html)# += str(soldby_byte, encoding='utf-8')
            pattern_list = [
                re.compile('[Ss]old by.*?<a.*?dp_merchant_link.*?seller=.*?>([\w].*?)</', re.S),
            ]
            sold_by_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=soldby_html, url_type='soldby')
            if len(sold_by_list) > 0:
                sold_by = sold_by_list[0].strip().lstrip()
                return sold_by
        sold_by_pattern = [
            re.compile('[Ss]old merchants on (Amazon.com)', re.S),
            re.compile('Ships from and [Ss]old by (Amazon.com)', re.S),
            re.compile('[Ss]old by.*?<a.*?dp_merchant_link.*?seller=.*?>([\w].*?)</', re.S),
            re.compile('Ships from and [Ss]old by ([\w][A-Za-z0-9 ,\'\&\(\)\.-_]+)\..*?</', re.S),
            re.compile('[Ss]old and delivered by([[\w]A-Za-z0-9 ,\'\&\(\)\.-_]+),.*?</', re.S),
            re.compile('[Ss]old by.*?<b>([\w][A-Za-z0-9]+).*?</', re.S),
            re.compile('[Ss]old by.*?<a.*?seller=[a-zA-Z0-9]+\&.*?>([\w].*?)</', re.S),
        ]
        sold_by_list = GoodsParser.get_new_data(pattern_list=sold_by_pattern, html_code=self.buy_box_html)
        if len(sold_by_list) <= 0:
            sold_by_list = GoodsParser.get_new_data(pattern_list=sold_by_pattern, html_code=self.head_html)
        if len(sold_by_list) <= 0:
            sold_by_list = GoodsParser.get_new_data(pattern_list=sold_by_pattern, html_code=html_code)
        if len(sold_by_list) > 0:
            sold_by = sold_by_list[0].strip().lstrip()
        if len(sold_by) > 128:   # print('Sold by1: ', sold_by)
            sold_by = ''
        return sold_by

    # 获取商家ID
    #@timer# 获取商家ID
    def _get_seller_id(self, html_code=None):
        if self._is_Currently_unavailable():
            return ''
        if html_code is None:
            html_code = self.html_code
        seller_id = ''
        xpath_list = [
            '//*[contains(text(), "Sold by")]/..'
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            seller_html = str(tostring(result_list[0]), encoding='utf-8')
            pattern_list = [
                re.compile('[Ss]old by.*?<a.*?dp_merchant_link.*?seller=([a-zA-Z0-9]+)\&.*?>', re.S),
            ]
            seller_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=seller_html)
            # print('seller_id: ', seller_list)
            if len(seller_list) > 0:
                seller_id = seller_list[0].strip().lstrip()
                return seller_id

        pattern_list = [
            re.compile('<.*?sellingCustomerID.*?value="([A-Za-z0-9]+)".*?>'),
            re.compile('<.*?merchantID.*?value="([A-Za-z0-9]+)".*?>'),
        ]

        seller_id_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=html_code)
        if len(seller_id_list) > 0:
            seller_id = seller_id_list[0].strip().lstrip()
        return seller_id

    def _is_see_all_Buying(self, html_code=None):
        if not html_code:
            html_code = self.html_code
        # print('_is_see_all_Buying')
        RobotCheck_patterns = [
            re.compile('id="buybox-see-all-buying-choices-announce"', re.S),
            re.compile('See All Buying Options', re.S),

        ]
        unavailable = GoodsParser.get_new_data(pattern_list=RobotCheck_patterns, html_code=html_code)
        # print(unavailable)
        if len(unavailable) > 0:
            return True
        return False

    # 获取原价(仅历史表有用)
    #@timer# 获取原价(仅历史表有用)
    def _get_original_price(self, html_code=None):
        if self._is_Currently_unavailable():
            return 0
        if not html_code:
            html_code = self.html_code
        pattern = re.compile('\$[\d,\.]+')
        result = 0
        xpath_list = [
            '//*[contains(text(), "List Price:")]/../..//text()',
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)

        xpath_list = [
            '//*[contains(@id, "snsPrice")]//*[contains(@class, "strike")]/text()'   # 案例　B01G8UTA3S 此案例中用下面两个会抓到假价格, 所以优先级排到第一.
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)
        xpath_list = [
            '//*[contains(@id, "buyNew")]//*[contains(@class, "strike")]/text()'   # 案例　0060012781　　0060899220
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)
        xpath_list = [
            '//*[contains(@id, "price")]//*[contains(@class, "strike")]/text()'   # 案例 B008XMBWK4 B00B4YVU4G
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)
        return result

    # 获取当前价格(更新表都存此价格)
    #@timer# 获取当前价格(更新表都存此价格)
    def _get_discount_price(self, html_code=None):
        if self._is_Currently_unavailable():
            return 0
        if not html_code:
            html_code = self.html_code
        result = 0
        pattern = re.compile('\$[\d,\.]+')
        xpath_list = [
            # '//*[contains(text(), "Sale:")]/..//*[contains(@id, "priceblock")]//text()', # B00XLBELKK 特例情况价格在Sale.
            '//*[@id="priceInsideBuyBox_feature_div"]//*[@id="price_inside_buybox"]/text()',  # B00XLBELKK 优先拿购物车价格
            '//*[contains(text(), "Price:")]/..//*[contains(@class, "a-color-price")]//text()',
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)
        xpath_list = [
            '//*[contains(text(), "Price:")]/../..//*[contains(@class, "a-color-price")]//text()',
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)

        xpath_list = [
            '//*[contains(text(), "Buy New")]/../..//text()',
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)

        xpath_list = [
            '//*[contains(@id, "snsPrice")]//*[contains(@class, "price")]/text()'  # 案例 B014TF6LRC
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)
        xpath_list = [
            '//*[contains(@id, "buybox")]//*[contains(@id, "buyNew")]//*[contains(@class, "price")]/text()'  # 案例　0060012781　0060899220
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)
        xpath_list = [
            '//*[contains(@id, "addToCart")]//*[contains(@id, "price")]/text()'  # 案例　B01LYCX1GU　B016X6SEAC
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)

        xpath_list = [
            '//*[contains(@id, "newPrice")]//*[contains(@class, "priceblock")]//text()'  # 案例　B01N5OKGLH 游戏类
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        item_list = []
        if len(result_list) > 0:
            for item in result_list:
                item = item.lstrip.strip()
                if item:
                    item_list.append(item)
        result_str = ''.join(item_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)

        xpath_list = [
            '//*[contains(@id, "price")]//*[contains(@id, "priceblock")]/text()'  # 案例 B014TF6LRC
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)

        xpath_list = [
            '//*[contains(@id, "price")]//*[contains(@class, "a-color-price")]/text()'    # 案例　B016X6SEAC
        ]
        result_list = self.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        result_str = ''.join(result_list)
        serch_result = pattern.search(result_str)
        if serch_result:
            result = ''.join(''.join(''.join(serch_result.group(0).split('$')).split(',')).split('.')).strip().lstrip()
            if result.isdigit():
                return int(result)

        return result

    # 获取购物车价格(若找不到价格， 就用这个再找一遍)
    # @timer# 获取购物车价格(若找不到价格， 就用这个再找一遍)
    def _get_cart_price(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        result_price = 0
        price_xpath = [
            '//*[@id="soldByThirdParty"]/span[1]/text()',
        ]
        price = GoodsParser.get_new_data(xpath_list=price_xpath, xpath_obj=self.xpath_obj)
        if len(price) > 0:
            price = price[0]
            if '-' in price:
                price = price.split('-')[0].strip().lstrip()
            price = ''.join(''.join(''.join(price.split("$")).split('.')).split(',')).strip().lstrip()
            if price.isdigit():
                result_price = int(price)
            # print(type(price))
            else:
                return -1
            return result_price
        else:
            price_pattern = [
                re.compile('"buyboxPrice":"\$([\d,\.]+)"', re.S),
            ]

            price = GoodsParser.get_new_data(pattern_list=price_pattern, html_code=html_code)

            # print('buyboxPrice: ', price)
            if price:

                price = price[0]

                price = ''.join(''.join(price.split('.')).split(','))

                # print('buyboxPrice1: ', price)

                if price.isdigit():
                    result_price = int(price)
                else:
                    return -1
        return result_price

    # 跟卖最低价格(如无存0)
    # @timer# 跟卖最低价格(如无存0)
    def _to_price(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        result_price = 0
        xpath_list = [
            '//*[text()="Other Sellers on Amazon"]/../../../../..',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            # print(result_html)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
                re.compile('[Oo]ther [Ss]ellers.+?<a.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
                re.compile('<a.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
                re.compile('<a.*?condition.*?>.*?[\d,]+.*?new.*?from.*?<span.*?price.*>.*?\$([0-9\.,]+).*?<', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                # print('result_list: ', result_list)
                result = result_list[0].strip().lstrip()
                result = ''.join(''.join(result.split('.')).split(','))
                if result.isdigit():
                    # print('to_price1', result)
                    return int(result)
            else:
                xpath_list = [
                    '//*[@id="mbc"]//*[contains(@class, "price")]/text()'
                ]
                result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
                if len(result_list) > 0:
                    item_list = []
                    for item in result_list:
                        item = item.strip().lstrip()
                        item = ''.join(''.join(''.join(item.split('$'))).split(','))
                        if item.isdigit():
                            item_list.append(int(item))
                    if len(item_list) > 0:
                        return min(item_list)
        xpath_list = [
            '//*[@id="olpDiv"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
                re.compile('[Oo]ther [Ss]ellers.+?<a.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
                re.compile('<a.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                result = result_list[0].strip().lstrip()
                result = ''.join(''.join(result.split('.')).split(','))
                if result.isdigit():
                    # print('to_price1', result)
                    return int(result)
        xpath_list = [
            '//*[@id="olp_feature_div"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
                re.compile('[Oo]ther [Ss]ellers.+?<a.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
                re.compile('<a.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                result = result_list[0].strip().lstrip()
                result = ''.join(''.join(result.split('.')).split(','))
                if result.isdigit():
                    # print('to_price1', result)
                    return int(result)
        xpath_list = [
            '//*[@id="mbc"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
                re.compile('[Oo]ther [Ss]ellers.+?<a.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
                re.compile('<a.*?>.*?from.*?\$([0-9\.,]+).*?</', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                result = result_list[0].strip().lstrip()
                result = ''.join(''.join(result.split('.')).split(','))
                if result.isdigit():
                    # print('to_price1', result)
                    return int(result)
        xpath_list = [
            '//*[@id="toggleBuyBox"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?[\d,]+.*?new.*?from.*?<span.*?price.*>.*?\$([0-9\.,]+).*?<', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                # print('result_list: ', result_list)
                result = result_list[0].strip().lstrip()
                result = ''.join(''.join(result.split('.')).split(','))
                if result.isdigit():
                    return int(result)

        xpath_list = [
            '//*[@id="mbc"]//*[contains(@class, "price")]/text()'
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            item_list = []
            for item in result_list:
                item = item.strip().lstrip()
                item = ''.join(''.join(''.join(item.split('$'))).split(','))
                if item.isdigit():
                    item_list.append(int(item))
            if len(item_list) > 0:
                return min(item_list)

        return result_price

    # 跟卖数(如无存1)
    # @timer# 跟卖数(如无存1)
    def _to_sell(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        xpath_list = [
            '//*[text()="Other Sellers on Amazon"]/../../../../..',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?([\d,]+).*?from.*?</', re.S),
                re.compile('<a.*?condition.*?>.*?([\d,]+).*?new.*?</', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                result = result_list[0].strip().lstrip()
                if result.isdigit():
                    return int(result)
            else:
                xpath_list = [
                    '//*[@id="mbc"]//a[contains(@id, "a-autoid")]',
                ]
                result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
                if len(result_list) > 0:
                    if len(result_list) == 1:
                        result = 2
                    else:
                        result = len(result_list)
                    return result
        xpath_list = [
            '//*[@id="olp_feature_div"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?([\d,]+).*?from.*?</', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                result = result_list[0].strip().lstrip()
                if result.isdigit():
                    return int(result)
        xpath_list = [
               '//*[@id="olpDiv"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?([\d,]+).*?from.*?</', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                result = result_list[0].strip().lstrip()
                if result.isdigit():
                    return int(result)
        xpath_list = [
            '//*[@id="mbc"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?([\d,]+).*?from.*?</', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                result = result_list[0].strip().lstrip()
                if result.isdigit():
                    return int(result)
        xpath_list = [
            '//*[@id="toggleBuyBox"]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            result_xpath = result_list[0]
            result_html = tostring(result_xpath)
            pattern_list = [
                re.compile('<a.*?condition.*?>.*?([\d,]+).*?new.*?</', re.S),
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=result_html)
            if len(result_list) > 0:
                result = result_list[0].strip().lstrip()
                if result.isdigit():
                    return int(result)
        xpath_list = [
            '//*[@id="mbc"]//a[contains(@id, "a-autoid")]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            if len(result_list) == 1:
                result = 2
            else:
                result = len(result_list)
            return result
        return 0

    # 是否id="SalesRank"（某些商品销量例外）
    # @timer# 是否id="SalesRank"（某些商品销量例外）
    def is_SalesRank(self, html_code):
        SalesRank_pattern = [
            re.compile('id="SalesRank"', re.S),
        ]
        SalesRank_list = GoodsParser.get_new_data(pattern_list=SalesRank_pattern, html_code=html_code)
        if SalesRank_list:
            return True
        else:
            return False

    # 是否销量第一
    def _is_best_seller_1(self, bsrRank, html_code=None):
        if html_code is None:
            html_code = self.html_code
        if bsrRank == 1:
            return 1
        else:
            return 0

    # 是否有黄金购物车
    def _has_buy_button(self, html_code=None):
        '''有黄金购物车页面,有title="Add to Shopping Cart"的a或者input标签, 没有黄金购物车的页面,没有这个标签'''
        if html_code is None:
            html_code = self.html_code
        result = 0
        title = content = ''
        button_title_xpath = [
            '//a[@title="Add to Shopping Cart"]/text()',
        ]
        xpath_list = [
            '//input[@title="Add to Shopping Cart"]/@value',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=button_title_xpath, xpath_obj=self.xpath_obj)
        button_content = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            title = result_list[0]
            title = GoodsParser.filter_str(title)
            # print(1, 'buy_button: ', title)
        if len(button_content) > 0:
            # print(1, 'buy_button: ', button_content)
            content = button_content[0]
            content = GoodsParser.filter_str(content)
            # print(2, 'buy_button: ', content)
        if 'Add to Cart' in title or 'Add to Cart' in content:
            return 1
        else:
            xpath_list = [
                '//*[@id="add-to-cart-button"]'
            ]
            result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
            if len(result_list) > 0:
                return 1
            else:
                pattern_list = [
                    re.compile('Add to Cart'),
                    re.compile('Add to Cart', re.S),
                ]
                result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=html_code)
                if len(result_list) > 0:
                    return 1
        return result

    def _has_try_prime(self):
        'Try Prime'
        pattern_list = [
            re.compile('Try Prime'),
            re.compile('Try Prime', re.S),
        ]
        result_list = self.get_new_data(pattern_list=pattern_list, html_code=self.html_code)
        # print('condition1: ', result_list)
        if len(result_list) > 0:
            result = 1
        else:
            result = 0
        return result

    # 问答数
    # @timer# 问答数
    def _get_qa_count(self, html_code=None):
        '''
        <span id="acrCustomerReviewText" class="a-size-base">397 customer reviews</span>
        <span class="a-size-base">24 answered questions</span>
        '''
        result = 0
        if html_code is None:
            html_code = self.html_code
        if self.head_html:
            html_code = self.head_html
        qa_xpath = [
            '//a[@id="askATFLink"]/span/text()',
            '//*[@id="askATFLink"]/span/text()',
        ]
        qa_count = GoodsParser.get_new_data(xpath_list=qa_xpath, xpath_obj=self.xpath_obj)
        if len(qa_count) > 0:
            qa_count = qa_count[0]
            qa_count = GoodsParser.filter_str(qa_count)
            qa_count = qa_count.split(' ')
            if len(qa_count) > 0:
                qa_count = qa_count[0]
                if ',' in qa_count:
                    qa_count = ''.join(qa_count.split(','))
                if qa_count.isdigit():
                    result = int(qa_count)
                    # print(type(qa_count))
                    return result
        return result

    # 评论数
    # @timer# 评论数
    def _get_review_count(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        review_xpath = [
            '//div[@id="reviewSummary"]//span[@data-hook="total-review-count"]/text()',
            '//*[@id="reviewSummary"]//span[@data-hook="total-review-count"]/text()',
            '//div[@id="reviewSummary"]/div/a/div/div/div/div/span[@data-hook="total-review-count"]/text()',
            '//*[@id="reviewSummary"]/div/a/div/div/div/div/span[@data-hook="total-review-count"]/text()',
        ]
        review = GoodsParser.get_new_data(xpath_list=review_xpath, xpath_obj=self.xpath_obj)
        # 如果通过xpath解析可以拿到评论的总数  那就返回这个值
        if len(review) > 0:
            review = review[0]
            review = ''.join(review.split(','))
            if review.isdigit():
                return int(review)
            else:
                return 0
        else:
            # 如果xpath没有拿到数据  那么就使用bs4拿到页面上评论数据对应的标签  然后使用正则提取评论数据
            table = self.soup.select('span[id="acrCustomerReviewText"]')
            if len(table) > 0:
                h_code = str(table[0])
                # print(h_code)
                review = re.findall(r'<.*>(.*) customer reviews<.*>', h_code)
                print(review[0])
            if review:
                review = review[0]
                review = ''.join(review.split(','))
                if review.isdigit():
                    return int(review)
                else:
                    return 0
            else:
                return 0

    # 综合评分
    # @timer# 综合评分
    def _get_review_rating(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        if self.head_html:
            html_code = self.head_html
        result = 0
        rating_xpath = [
            '//span[@id="acrPopover"]/@title',
            '//*[@id="acrPopover"]/@title',
            '//*[@data-hook="rating-out-of-text"]/text()'
        ]
        rating = GoodsParser.get_new_data(xpath_list=rating_xpath, xpath_obj=self.xpath_obj)
        if len(rating) > 0:
            rating = rating[0].strip().lstrip()
            # print(0.0, rating)
            rating = rating.split(' ')
            if len(rating) > 0:
                rating = rating[0]
                # print(1.0, rating)
                if '.' in rating and rating.split('.')[0].isdigit():
                    # print(rating, type(rating))
                    return float(rating) * 10
        else:
            pattern_list = [
                re.compile('([\d\.]+) out of 5 stars')
            ]
            result_list = GoodsParser.get_new_data(pattern_list=pattern_list, html_code=self.html_code)
            if len(result_list) > 0:
                result1 = result_list[0]
                return float(result1) * 10
        return result

    # 5星评价百分比
    def _get_review_5_percent(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        result = 0
        percent_xpath = [
            '//div[@class="a-meter 5star"]/@aria-label',
        ]
        percent = GoodsParser.get_new_data(xpath_list=percent_xpath, xpath_obj=self.xpath_obj)
        if len(percent) > 0:
            percent = percent[0]
            percent = GoodsParser.filter_str(percent)
            percent = GoodsParser.percent_convert(percent)
            return percent

        return result

    # 4星评价百分比
    def _get_review_4_percent(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        result = 0
        percent_xpath = [
            '//div[@class="a-meter 4star"]/@aria-label',
        ]
        percent = GoodsParser.get_new_data(xpath_list=percent_xpath, xpath_obj=self.xpath_obj)
        if len(percent) > 0:
            percent = percent[0]
            percent = GoodsParser.filter_str(percent)
            percent = GoodsParser.percent_convert(percent)
            return percent

        return result

    # 3星评价百分比
    def _get_review_3_percent(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        result = 0
        percent_xpath = [
            '//div[@class="a-meter 3star"]/@aria-label',
        ]
        percent = GoodsParser.get_new_data(xpath_list=percent_xpath, xpath_obj=self.xpath_obj)
        if len(percent) > 0:
            percent = percent[0]
            percent = GoodsParser.filter_str(percent)
            percent = GoodsParser.percent_convert(percent)
            return percent
        return result

    # 2星评价百分比
    def _get_review_2_percent(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        result = 0
        percent_xpath = [
            '//div[@class="a-meter 2star"]/@aria-label',
        ]
        percent = GoodsParser.get_new_data(xpath_list=percent_xpath, xpath_obj=self.xpath_obj)
        if len(percent) > 0:
            percent = percent[0]
            percent = GoodsParser.filter_str(percent)
            percent = GoodsParser.percent_convert(percent)
            return percent
        return result

    # 1星评价百分比
    def _get_review_1_percent(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        result = 0
        percent_xpath = [
            '//div[@class="a-meter 1star"]/@aria-label',
        ]
        percent = GoodsParser.get_new_data(xpath_list=percent_xpath, xpath_obj=self.xpath_obj)
        if len(percent) > 0:
            percent = percent[0]
            percent = GoodsParser.filter_str(percent)
            percent = GoodsParser.percent_convert(percent)
            return percent
        return result

    # 商品说明
    # @timer# 商品说明
    def _get_feature(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        if self.head_html:
            html_code = self.head_html
        result = ''
        feature_xpath = [
            '//div[@id="feature-bullets"]/ul[@class="a-unordered-list a-vertical a-spacing-none"]/li/span/text()',
            '//*[@id="feature-bullets"]/ul[@class="a-unordered-list a-vertical a-spacing-none"]/li/span/text()',
            '//div[@id="feature-bullets"]/ul/li/span/text()',
            '//*[@id="feature-bullets"]/ul/li/span/text()',
            '//*[@id="fbExpandableSectionContent"]/ul//text()',
            '//*[@id="productDescription"]/p/text()',
            '//*[@id="bookDesc_iframe"]/p/b/text()',
            '//div[contains(@id, "feature")]//span[contains(@id, "shortDescription")]/text()',
            '//div[@data-automation-id="synopsis"]//text()',
            '//div[@id="mas-atf-app-permissions"]//text()',
        ]
        feature = GoodsParser.get_new_data(xpath_list=feature_xpath, xpath_obj=self.xpath_obj)
        print(feature)
        if len(feature) > 0:
            item_list = []
            for item in feature:
                # print('feature item: ', item)
                item = ' '.join(item.lstrip().strip().split('\n'))
                if item:
                    item_list.append(item)
            print('item_list: ', item_list)
            if item_list:
                result = '\n'.join(item_list).strip()
        else:
            feature_xpath = [
                '//div[@id="bookDescription_feature_div"]/noscript',
            ]
            feature = GoodsParser.get_new_data(xpath_list=feature_xpath, xpath_obj=self.xpath_obj)
            if len(feature) > 0:
                html = str(tostring(feature[0]), encoding='utf-8')
                xpath_obj = etree.HTML(html)
                # print(html)
                xpath_list = [
                    '//div/p//text()',
                    '//div//text()',
                ]
                feature = self.get_new_data(xpath_list=xpath_list, xpath_obj=xpath_obj)
                if len(feature) > 0:
                    item_list = []
                    for item in feature:
                        item = item.strip().lstrip()
                        item_list.append(item)
                    if len(item_list) > 0:
                        result = ' '.join(item_list)

        return result

    # 发布日期
    # @timer# 发布日期
    def _get_release_date(self, html_code=None):
        '''June 20, 2017 日期要进行换算，并转换成int型'''
        date_time = 0
        if html_code is None:
            html_code = self.html_code
        date_pattern = re.compile('[A-Za-z]+ \d+, \d{4}')
        xpath_list = [
            '//*[contains(text(), "Date First Available")]/..',
            '//*[contains(text(), "Date first listed on Amazon")]/..',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            for item in result_list:
                if item:
                    html = str(tostring(item), encoding='utf-8')
                    # print(html, type(html))
                    datestr = date_pattern.search(html)
                    if datestr:
                        date1 = datestr.group(0).lstrip().strip()
                        date_format = datetime.strptime(date1, "%B %d, %Y")
                        if not date_format:
                            date_format = datetime.strptime(date1, "%b %d, %Y")
                        date_time = int(date_format.strftime('%Y%m%d'))
                        return date_time

        xpath_list = [
            '//*[contains(@id, "productDetails")]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            for item in result_list:
                if item:
                    html = str(tostring(item), encoding='utf-8')
                    # print(html, type(html))
                    datestr = date_pattern.search(html)
                    if datestr:
                        date1 = datestr.group(0).lstrip().strip()
                        date_format = datetime.strptime(date1, "%B %d, %Y")
                        if not date_format:
                            date_format = datetime.strptime(date1, "%b %d, %Y")
                        date_time = int(date_format.strftime('%Y%m%d'))
                        return date_time

        xpath_list = [
            '//*[contains(@id, "detail-bullets")]',
        ]
        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            for item in result_list:
                if item:
                    html = str(tostring(item), encoding='utf-8')
                    # print(html, type(html))
                    datestr = date_pattern.search(html)
                    if datestr:
                        date1 = datestr.group(0).lstrip().strip()
                        date_format = datetime.strptime(date1, "%B %d, %Y")
                        if not date_format:
                            date_format = datetime.strptime(date1, "%b %d, %Y")
                        date_time = int(date_format.strftime('%Y%m%d'))
                        return date_time
        return date_time

    def _get_variant(self, html_code=None):
        if html_code is None:
            html_code = self.html_code
        if self.head_html:
            html_code = self.head_html
        color = ''
        size = ''
        style = ''
        xpath_list = [
            '//*[contains(@id, "color")]//*[contains(text(), "Colors:")]/..//text()',
            '//*[contains(@id, "color")]//*[contains(text(), "Color:")]/..//text()',
        ]

        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            item_list = []
            for item in result_list:
                item = item.strip().lstrip()
                if item:
                    item_list.append(item)
            if len(item_list) > 0:
                color = ''.join(item_list)
        xpath_list = [
            '//*[contains(@id, "size")]//*[contains(text(), "Sizes:")]/..//text()',
            '//*[contains(@id, "size")]//*[contains(text(), "Size:")]/..//text()',
        ]

        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            item_list = []
            for item in result_list:
                item = item.strip().lstrip()
                if item:
                    item_list.append(item)
            if len(item_list) > 0:
                size = ''.join(item_list)

        xpath_list = [
            '//*[contains(@id, "style")]//*[contains(text(), "Styles:")]/..//text()',
            '//*[contains(@id, "style")]//*[contains(text(), "style:")]/..//text()',
        ]

        result_list = GoodsParser.get_new_data(xpath_list=xpath_list, xpath_obj=self.xpath_obj)
        if len(result_list) > 0:
            item_list = []
            for item in result_list:
                item = item.strip().lstrip()
                if item:
                    item_list.append(item)
            if len(item_list) > 0:
                style = ''.join(item_list)
        result = color + " " + size + " " + style
        return result

    # 百分数换算
    @staticmethod
    def percent_convert(percent_str=''):
        float_num = 0
        if percent_str.endswith('%'):
            num = percent_str.split('%')[0]
            if num.isdigit():
                float_num = int(num)  # / 100
                # print(float_num)
        return float_num

    @staticmethod
    def has_son_goods(html_code):
        '''
        :param html_code: string
        :return: has son return son_asin_json "{'B01M13AYYA': ['10-Piece'], 'B01GBT9NJC': ['5-Piece']}"
        '''
        patterns = [
            re.compile('dimensionValuesDisplayData".*?:(.*?)"prioritizeReqPrefetch', re.S),
            # re.compile('dimensionValuesDisplayData" :(.*?)"prioritizeReqPrefetch', re.S),
        ]
        son_goods_list = GoodsParser.get_new_data(html_code=html_code, pattern_list=patterns)
        # print(1, 'son', type(son_goods_list), son_goods_list)
        if son_goods_list is None:
            return False
        else:
            son_goods_list = ''.join(son_goods_list).strip()
            # print(2, 'son', type(son_goods_list), son_goods_list)
            if son_goods_list.endswith(','):
                son_goods_list = son_goods_list.rstrip(',')
                # print(3, 'son', type(son_goods_list), son_goods_list)
            son_asin_json = demjson.decode(son_goods_list) if son_goods_list else None
            # print(4, 'son', type(son_goods_list), son_asin_json)
            return son_asin_json

@timer
@retry(stop_max_attempt_number=10)
def get_html_useRequest(asin, url=None, ua=None, ip=None, cookie=None, debug_log=None, referer=None, ipQ=None, urlQ=None, timeout=15, the_retry=1, goodsUrl='', url_type=''):
    proxies = get_porxy()
    print('%s proxies: ' % (asin), proxies)
    # print('get_html_useRequest.asin: ', asin)
    r = re.compile('^[A-Za-z0-9]{10,10}$')
    k = r.match(asin)
    url = ''
    msg = ''
    if k:
        url = "https://www.amazon.com/dp/" + asin + "?th=1&psc=1"
    print('get_html_useRequest.url: ', url)
    referer = 'https://www.amazon.com'
    headers = deepcopy(BASE_HEADERS)
    # print('headers1', headers)
    ua = get_user_agent()
    if ua:
        headers['User-Agent'] = ua
    if referer:
        headers['referer'] = referer
    html = ''
    status_code = 0
    print('\n%s headers2: ' % (asin), headers)
    is_error = False
    # get_dict = dict(
    #     headers=headers, proxies=proxies, timeout=timeout
    # )
    # verify = PROXY_VERIFY
    # if verify:
    #     get_dict['verify'] = verify
    # print(get_dict)
    if url.startswith('https://www.amazon.com') or url.startswith('http://www.amazon.com'):
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
            status_code = response.status_code
            print('%s status_code' % asin, status_code)
            if status_code == 200 or status_code == 302:
                response.encoding = 'utf-8'
                html = response.text
                if GoodsParser.is_RobotCheck(html):
                    print('%s is robot check' % (asin))
                    if the_retry > 0:
                        print('%s is robot check retrying' % (asin))
                        return get_html_useRequest(asin, the_retry=the_retry - 1)

            if status_code == 404:
                is_error = True
                msg = '%s The page not found!' % (asin)

            if status_code == 403:
                is_error = True
                msg = '%s Network error!' % (asin)

        except Exception as e:
            if status_code != 404:
                is_error = True
                msg = '%s %s' % (asin, e)
                print(msg) # = '%s %s' % (asin, e)

    return html, msg, is_error


# @timer
# def download_thread(data):
#     print(5, type(data), data)
#     if data and type(data) is dict:
#         asin = data.get('asin', '')
#         r = re.compile('^[A-Za-z0-9]{10,10}$')
#         k = r.match(asin)
#         if not k:
#             PUBLIC_DATA['msg'].append({'data': 'the asin [%s] nonlicet!' % (asin)})
#             PUBLIC_DATA['ret'] = 0
#             return
#         create_id = data.get('cid')
#         if not create_id:
#             PUBLIC_DATA['msg'].append({'data': 'Data invalid! cid'})
#             PUBLIC_DATA['ret'] = 0
#             return
#         get_id = '%s%s' % (create_id, 'parse')
#         price = data.get('price') or 0
#         asin_key = asin + 'parse'
#         if type(price) is not int:
#             if type(price) is str:
#                 if price.isdigit():
#                     price = int(price)
#                 else:
#                     price = 0
#             else:
#                 price = 0
#         brand = data.get('brand') or ''
#         rc = data.get('rc') or 0
#         image = data.get('img') or ''
#         html = ''
#         cache_data = R.get(asin_key)
#         # print('%s cache_data.cache_data: ' % (asin), cache_data)
#         try:
#             data_dict = json.loads(cache_data)
#         except:
#             data_dict = {}
#         if data_dict.get('bsr_info') or data_dict.get('feature'):
#             save_dict = json.loads(R.get(get_id) or '{}')
#             save_dict.update({asin: data_dict})
#             R.set(get_id, json.dumps(save_dict), save_time)
#             PUBLIC_DATA['data'].append(data_dict)
#             print('%s cache_data.result: ' % (asin), data_dict)
#         else:
#             try:
#                 html, msg, is_error = get_html_useRequest(asin)
#                 if is_error:
#                     PUBLIC_DATA['msg'].append({'request': {asin: msg}})
#                     PUBLIC_DATA['ret'] = 0
#                     # print(type(html), html)
#             except Exception as e:
#                 PUBLIC_DATA['msg'].append({'request': {asin: '%s' % (e)}})
#                 PUBLIC_DATA['ret'] = 0
#
#         if html:
#             if not GoodsParser.is_RobotCheck(html):
#                 try:
#                     result = GoodsParser().parser_goods(html, asin, price, brand, rc, image)
#                     PUBLIC_DATA['data'].append(result)
#                     if result['bsr_info'] or result['feature']:
#                         save_dict = json.loads(R.get(get_id) or '{}')
#                         save_dict.update({asin: result})
#                         R.set(get_id, json.dumps(save_dict), save_time)
#                         json_data = json.dumps(result)
#                         R.set(asin_key, json_data, cache_time)
#
#                 except Exception as e:
#                     PUBLIC_DATA['msg'].append({'parse': {asin: '%s' % (e)}})
#             else:
#                 PUBLIC_DATA['msg'].append({'request': {asin: 'robot check'}})
#     else:
#         PUBLIC_DATA['msg'].append({'data': 'Data invalid! Must be {"field": value}'})
#         PUBLIC_DATA['ret'] = 0


# @app.route('/py/parse', methods=['POST'])
# def parse():
#     '''
#     request.json = {'parse': [{'asin': 'asin', 'brand': 'brand', 'price': 0, 'rc': 0},]}
#     response.json = {'error': [{'methods':''}, {'parameter': ''}, {'data': ''}, {'parse': {asin: e}}], 'result': [{'asin': {'field': 'data',}},]
#     'bsrinfo': [{'bsrNum': 1, 'bsrStr': '', 'aday': 20180101, 'tm': 1528696144473},]
#
#     request_json = {
#         'parse': [
#             {'asin': 'asin', 'brand': 'brand', 'price': 0, 'rc': 0},
#         ]
#     }
#
#     '''
#
#     # time1 = time.time()
#     now = lambda : time.time()
#     time1 = now()
#     # print('PUBLIC_DATA: ', PUBLIC_DATA)
#     pool = ThreadPool(T_NUM)
#     if request.method == 'POST':
#         try:
#             a = request.get_json()
#             b = request.headers
#             if type(a) is str:
#                 # print(2, type(a), len(a))
#                 a = json.loads(a, encoding='utf-8')
#             if type(a) is not dict:
#                 print(3, type(a), len(a))
#                 raise Exception('Parameter invalid!')
#             qid = a.get('qid', '0')
#             print(qid, type(qid))
#             if not re.match('^1[0-9]{9}$', str(qid)):
#                 raise Exception('Parameter invalid! queue id format')
#             # print(now() - int(str(qid)))
#             # if now() - int(str(qid)) > 60 :
#             #     raise Exception('Parameter invalid! queue id')
#             parse_id = a.get('pid')
#             md5value = '%s%s' % (qid, b.get('user-agent', ''))
#             verfy_pid = hashlib.md5(md5value.encode('utf-8')).hexdigest()[8: -8]
#             if verfy_pid != parse_id:
#                 raise Exception('Parameter invalid! parse id')
#             parse = a.get('parse')
#             if not parse or type(parse) is not list:
#                 raise Exception('Parameter invalid! parse')
#             create_id = a.get('cid')
#             if not create_id:
#                 raise Exception('Parameter invalid! create id')
#             limit_key = '%s%s' % (create_id, 'limit')
#             get_id = '%s%s' % (create_id, 'parse')
#             delete_id = a.get('did')
#             queue_id = a.get('qid')
#             update_id = a.get('uid')
#             md5value = '%s%s%s' % (update_id, create_id, queue_id)
#             print(md5value)
#             verify_did = hashlib.md5(md5value.encode('utf-8')).hexdigest()[8: -8]
#             print(verify_did, delete_id )
#             if verify_did != delete_id:
#                 raise Exception('Parameter invalid! delete id')
#             # 清空
#             if update_id == 4:
#                 R.set(get_id, json.dumps({}), 1)
#             # 删除
#             if update_id == 3:
#                 result_data = json.loads(R.get(get_id) or '{}')
#                 for pr in parse:
#                     if result_data.get(pr.get('asin')):
#                         result_data.pop(pr.get('asin'))
#                 R.set(get_id, json.dumps(result_data), SAVE_TIME)
#             # 获取旧数据
#             if update_id == 0:
#                 data_dict = json.loads(R.get(get_id) or '{}')
#                 print('date_dict', data_dict)
#                 t_list = []
#                 if not data_dict:
#                     pool.map(download_thread, parse)
#                 else:
#                     for pr in parse:
#                         result = data_dict.get(pr.get('asin'))
#                         print(pr.get('asin'), 'result', result)
#                         if result:
#                             PUBLIC_DATA['data'].append(result)
#                         else:
#                             t_list.append(Thread(target=download_thread, args=(pr,)))
#                     if len(t_list) > 0:
#                         for t in t_list:
#                             t.start()
#                         for t in t_list:
#                             t.join()
#             # 获取新数据
#             if update_id == 1:
#                 if R.get(limit_key):
#                     raise Exception('Please operate after 3 seconds')
#                 R.set(limit_key, 'True', 3)
#                 pool.map(download_thread, parse)
#
#         except Exception as e:
#             PUBLIC_DATA['msg'].append({'main': '%s' % (e)})
#             PUBLIC_DATA['ret'] = 1
#     else:
#         PUBLIC_DATA['msg'].append({'methods': 'The request methods must be post!'})
#         PUBLIC_DATA['ret'] = 1
#     # print(4, type(PUBLIC_DATA), PUBLIC_DATA)
#     result_data = deepcopy(PUBLIC_DATA)
#     print('result_data: ', result_data)
#     try:
#         result = jsonify(result_data)
#         PUBLIC_DATA['data'] = []
#         PUBLIC_DATA['msg'] = []
#         PUBLIC_DATA['ret'] = 0
#         # print('PUBLIC_DATA', PUBLIC_DATA)
#         print('result: ', result)
#         print(now() - time1)
#         return result
#     except Exception as e:
#         print(e)
#         result = jsonify(dict(data=[],msg=['data type error'],ret=1,))
#     PUBLIC_DATA['data'] = []
#     PUBLIC_DATA['msg'] = []
#     PUBLIC_DATA['ret'] = 0
#     # print('PUBLIC_DATA', PUBLIC_DATA)
#     result.headers['Server'] = 'HTTP/1.1'
#     print('result: ', result)
#     print(now() - time1)
#     return result


if __name__ == '__main__':

    headers = deepcopy(BASE_HEADERS)
    get_dict = dict(
        headers=headers, proxies=get_porxy(), timeout=15
    )
    verify = PROXY_VERIFY
    if verify:
        get_dict['verify'] = verify
    print(get_dict)
    print(get_porxy())
    print(get_user_agent())
    # print(R)
    # print(BASE_TYPE)
    # print(cache_time)
    # print(R.set('1', '11', 1))
    # print(R.get('1'))
    # '''192.168.13.24:8001/py/parse'''
    # app.run(host='0.0.0.0', port=8001, debug=True)
    # app.run()
    #print(GoodsParser().parser_goods(goods_html1, '', 0, '', 0, ''))
