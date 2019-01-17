#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import sys
sys.path.append("../")

import json
import time

from lxml import etree
from functools import wraps

import requests

from Crawler.BaseCrawler import BaseCrawler
from Crawler.goodsParser import GoodsParser
from utils.util import Logger, UaPond, GetRedis, UrlQueue
from Crawler.Downloader import get_product



# 获取商品数据的api
GET_ASIN_DATA_API = 'https://192.168.13.8:5120/indexCrawler.php?r=PyApi/Product/getProduct&asin={}'
# 获取分类数据的api
GET_CATEGORY_API = 'https://192.168.13.8:5120/indexCrawler.php?r=PyApi/Product/getCategory&asin={}'

# 以当前文件的名称作为日志文件的名称　sys.argv[0]是获取当前模块的名字
log_name = sys.argv[0].split('/')[-1].split('.')[0]
debug_log = Logger(log_name=log_name)


def get_data_from_db(sql, redisQ, asin=None, data=None):
    urlQ = UrlQueue(redisQ, debug_log)
    if type(data) is dict:
        result = urlQ.retrieve_asin(sql, data)
    else:
        result = urlQ.retrieve_asin(sql)
    return result


def get_data_from_api(api_url):
    time.sleep(2)
    data = requests.get(api_url, verify=False)
    print(data)
    print(data.text)
    try:
        data_dict = json.loads(data.text)
    except Exception as e:
        print(e)
        data_dict = {}
    return data_dict


def get_data_from_requests(url):
    html_code, cookie, is_error = get_product(url=url)
    return html_code


# 通过查询数据库获取品牌信息
def get_brand_from_db(asin):
    pass
    # # 获取品牌信息  先从redis缓存中获取数据  如果没有  再查postgresql数据库
    # # 先从redis的product_info_asin中获取品牌数据
    # redisQ = GetRedis().return_redis(debug_log)
    # print(asin)
    # brand = redisQ.hget('product_info_asin', 'product_info_{}'.format(asin))
    # print(brand)
    # if brand:
    #     return brand
    # print(2222)
    # str_brand = lambda lst: [x[0] for x in lst if type(x) is tuple and len(x) > 0]
    # # 查询数据库的sql语句
    # # sql = "select brand from public.amazon_product_info where asin='%s'" % (asin)
    # sql = "select brand from public.amazon_product_data where asin='%s'" % (asin)
    # print(sql)
    # brand = str_brand(get_data_from_db(sql, redisQ, asin=asin))
    # return brand


# 就通过api接口获取品牌信息
def get_brand_from_api(asin):
    brand = ''
    api_url = GET_ASIN_DATA_API.format(asin)
    data_dict = get_data_from_api(api_url)
    print(get_brand_from_api.__name__, data_dict, type(data_dict))
    if type(data_dict) is dict:
        data = data_dict.get('data', {})
        # # TODO 将数据保存到redis中  以product_info_asin为键  hash格式
        # myRedis = GetRedis().return_redis(debug_log)
        # myRedis.hset('product_info_asin', 'product_info_{}'.format(asin), data)
        print(get_brand_from_api.__name__, data, type(data))
        if type(data) is dict:
            brand = data.get('brand', '')
    return brand


# 通过商品解析类中的方法获取商品的品牌信息
def get_brand_from_parser(html_code):
    # 调用商品解析的方法获取页面的品牌信息
    brand = GoodsParser(html_code)._get_brand()
    return brand


def get_brand(asin):
    # 1. 通过查询数据库获取品牌信息
    # TODO 查询数据库
    brand = get_brand_from_db(asin)

    # 2. 如果数据库中未能获取品牌信息　就通过api接口获取品牌信息
    if not brand:
        brand = get_brand_from_api(asin)
        #
        # # 3. 如果通过API未能获取品牌信息 就通过商品解析类中的方法获取商品的品牌信息
        if not brand:
            brand = get_brand_from_parser(asin)
    return brand


def get_category_from_db(asin):
    pass


def get_category_from_api(asin):
    category = ''
    api_url = GET_CATEGORY_API.format(asin)
    data_dict = get_data_from_api(api_url)
    if type(data_dict) is dict:
        category_list = data_dict.get('data', [])
        # # TODO 将数据保存到redis中  以product_info_asin为键  hash格式
        # myRedis = GetRedis().return_redis(debug_log)
        # myRedis.hset('product_info_asin', 'product_info_{}'.format(asin), data)
        # print(data)
        if len(category_list) > 0:
            category = json.dumps(category_list)
    return category


def get_category_from_parser(html_code):
    # 通过解析 html 获得品牌
    category = GoodsParser(html_code)._get_category()
    return category


def get_category(asin):
    # 1. 通过查询数据库获取分类信息
    # TODO 查询数据库
    category = get_category_from_db(asin)

    # 2. 如果数据库中未能获取品牌信息　就通过api接口获取品牌信息
    if not category:
        category = get_category_from_api(asin)
    return category


def get_product_info(data):
    asin = data['asin']
    # data['category'] = get_category(asin)
    # if not data['brand']:
    #     data['brand'] = get_brand(asin)
    url, _ = BaseCrawler.make_url(asin, url_type='goods')
    html_code = get_data_from_requests(url)
    data['category'] = get_category_from_parser(html_code)
    if not data['brand']:
        data['brand'] = get_brand_from_parser(html_code)
    return data


def field_patch(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        # 运行被装饰方法　　获取返回数据
        data_dict = func(*args, **kwargs)

        # 如果数据为空　直接返回
        if not data_dict:
            return data_dict

        # 返回数据的字典
        result_dict = {}
        data_list = []

        # result_dict拆包
        for key, value in data_dict.items():
            kw = key
            keyword_data_dict = value[0]
            keyword_druid_data_list = value[1]
            # 遍历获取列表中的每一条数据　判断brand是否为空　如果是　就重新获取brand数据写入列表

            for data in keyword_druid_data_list:
                if not data['category']:
                    data = get_product_info(data)
                # 将更新后的每条数据添加进新的列表
                data_list.append(data)
            result_dict[kw] = (keyword_data_dict, data_list)
        from pprint import pprint
        pprint(result_dict)
        return result_dict

    return wrap

@field_patch
def func():
    data = {'silver jeans men': ({'cid': 0,
                       'date': 20181020,
                       'getinfo_tm': 1540032508846,
                       'kw': 'silver jeans men',
                       'mon_search': 0,
                       'mon_search_state': 0,
                       'other_state': 1,
                       'price_ave': 5817,
                       'price_max': 11899,
                       'price_min': 99,
                       'rc_ave': 197,
                       'rc_max': 5846,
                       'rc_min': 0,
                       'rrg_ave': 43,
                       'rrg_max': 50,
                       'rrg_min': 36,
                       'search_num': 228},
                      [{'aday': '20181020',
                        'asin': 'B00FMO4IJS',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41ZwMZC14zL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 1,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 1,
                        'price': 6999,
                        'rc': 429,
                        'rrg': 44,
                        'special': 1,
                        'srn': 228,
                        'title': 'Zac Relaxed Fit Straight Leg Jeans, , Blue',
                        'tm': 1540032508551},
                       {'aday': '20181020',
                        'asin': 'B00EE288PY',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51Ob058wsGL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 1,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 2,
                        'price': 7864,
                        'rc': 222,
                        'rrg': 44,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Gordie Loose Fit "
                                 'Straight Leg Jeans',
                        'tm': 1540032508566},
                       {'aday': '20181020',
                        'asin': 'B071LBMSPF',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41hghsIJfXL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 1,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 3,
                        'price': 9900,
                        'rc': 30,
                        'rrg': 46,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Craig Bootcut Jeans",
                        'tm': 1540032508578},
                       {'aday': '20181020',
                        'asin': 'B07FYP2VP3',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 0,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41tZTEaTXCL._AC_US200_.jpg',
                        'is_prime': 0,
                        'issp': 1,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 4,
                        'price': 9900,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Women's Plus Size Sam "
                                 'Medium Wash Boyfriend Jean',
                        'tm': 1540032508585},
                       {'aday': '20181020',
                        'asin': 'B00FMO4IJS',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41ZwMZC14zL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 5,
                        'price': 5475,
                        'rc': 429,
                        'rrg': 44,
                        'special': 1,
                        'srn': 228,
                        'title': 'Zac Relaxed Fit Straight Leg Jeans, , Blue',
                        'tm': 1540032508588},
                       {'aday': '20181020',
                        'asin': 'B0714F2MMG',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41NHJ3WsFrL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 6,
                        'price': 4197,
                        'rc': 222,
                        'rrg': 44,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Gordie Loose Fit "
                                 'Straight Leg Jeans',
                        'tm': 1540032508592},
                       {'aday': '20181020',
                        'asin': 'B00N49FECS',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51dTzrxJdHL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 7,
                        'price': 5939,
                        'rc': 81,
                        'rrg': 41,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Men's Zac Relaxed Fit Straight Leg "
                                 'Jeans - M42408ld191',
                        'tm': 1540032508595},
                       {'aday': '20181020',
                        'asin': 'B006W5ITMS',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/413bUbxtgTL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 8,
                        'price': 6348,
                        'rc': 21,
                        'rrg': 47,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Men's Zac Dark Wash Jeans Relaxed Fit "
                                 '- M4408sda495',
                        'tm': 1540032508598},
                       {'aday': '20181020',
                        'asin': 'B076Y2H5HD',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/413ZLqzHdTL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 9,
                        'price': 5957,
                        'rc': 18,
                        'rrg': 39,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Grayson Easy Fit "
                                 'Straight Leg Jeans',
                        'tm': 1540032508601},
                       {'aday': '20181020',
                        'asin': 'B079V95FKV',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41mSrVcZUxL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 10,
                        'price': 5340,
                        'rc': 7,
                        'rrg': 45,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co... Men's Konrad Fit Slim Leg "
                                 'Jeans',
                        'tm': 1540032508605},
                       {'aday': '20181020',
                        'asin': 'B071X48FSH',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41GK4BMg+8L._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 11,
                        'price': 4149,
                        'rc': 6,
                        'rrg': 46,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Allan Slim Leg Jeans",
                        'tm': 1540032508608},
                       {'aday': '20181020',
                        'asin': 'B00UILLATG',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41+WyFINjnL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 12,
                        'price': 9000,
                        'rc': 7,
                        'rrg': 43,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Nash Classic Fit "
                                 'Straight Leg',
                        'tm': 1540032508610},
                       {'aday': '20181020',
                        'asin': 'B071LBMXP2',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41UntzdTwKL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 13,
                        'price': 3471,
                        'rc': 8,
                        'rrg': 38,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Konrad Slim Fit Slim "
                                 'Leg Black Jeans',
                        'tm': 1540032508613},
                       {'aday': '20181020',
                        'asin': 'B016U44Y4W',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41mvAeDgxaL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 14,
                        'price': 8900,
                        'rc': 35,
                        'rrg': 43,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Zac Relaxed Fit "
                                 'Straight Leg Flap Pockets',
                        'tm': 1540032508615},
                       {'aday': '20181020',
                        'asin': 'B07147W1F9',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51sTEC0uFRL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 15,
                        'price': 11899,
                        'rc': 12,
                        'rrg': 43,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Big and Tall Grayson "
                                 'Straight Leg Jeans',
                        'tm': 1540032508618},
                       {'aday': '20181020',
                        'asin': 'B073TYWCJ5',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41T4wN3W5iL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 16,
                        'price': 6317,
                        'rc': 4,
                        'rrg': 47,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Grayson Straight Leg "
                                 'Knit Denim',
                        'tm': 1540032508622},
                       {'aday': '20181020',
                        'asin': 'B076Y2XQKS',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41-u4IpKkEL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 17,
                        'price': 5499,
                        'rc': 37,
                        'rrg': 46,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Eddie Relaxed Fit "
                                 'Tapered Leg',
                        'tm': 1540032508625},
                       {'aday': '20181020',
                        'asin': 'B072QXVTLK',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41g11SxDjfL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 18,
                        'price': 4381,
                        'rc': 1,
                        'rrg': 50,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Eddie Relaxed Fit "
                                 'Tapered Leg Colored Jeans',
                        'tm': 1540032508627},
                       {'aday': '20181020',
                        'asin': 'B07DDDYTM9',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41YkQNx9EtL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 19,
                        'price': 5523,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Hunter Athletic Fit",
                        'tm': 1540032508630},
                       {'aday': '20181020',
                        'asin': 'B076Y27PRY',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41xHVm-hQhL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 20,
                        'price': 6970,
                        'rc': 30,
                        'rrg': 46,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Craig Bootcut Jeans",
                        'tm': 1540032508633},
                       {'aday': '20181020',
                        'asin': 'B079VPWYKY',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41v9q44cDhL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 21,
                        'price': 4812,
                        'rc': 9,
                        'rrg': 42,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co Men's Eddie Relaxed Fit "
                                 'Tapered Leg Jeans',
                        'tm': 1540032508637},
                       {'aday': '20181020',
                        'asin': 'B07DDC65SL',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41V2+4rowpL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 22,
                        'price': 7900,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Grayson Easy Fit "
                                 'Straight Leg',
                        'tm': 1540032508639},
                       {'aday': '20181020',
                        'asin': 'B0725LJQ7P',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51XBr8QGh+L._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 23,
                        'price': 6950,
                        'rc': 10,
                        'rrg': 45,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Big and Tall Eddie "
                                 'Relaxed Fit Tapered Leg',
                        'tm': 1540032508642},
                       {'aday': '20181020',
                        'asin': 'B071K65BZV',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41gbfFL9SuL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 24,
                        'price': 3869,
                        'rc': 4,
                        'rrg': 47,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Taavi Slim Fit Skinny "
                                 'Leg Jeans',
                        'tm': 1540032508644},
                       {'aday': '20181020',
                        'asin': 'B0716HD9FJ',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/414jbuw5iRL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 25,
                        'price': 10900,
                        'rc': 1,
                        'rrg': 50,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Hunter Loose Fit "
                                 'Tapered Leg Jeans',
                        'tm': 1540032508647},
                       {'aday': '20181020',
                        'asin': 'B076Y6SGW9',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41rIfmDxniL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 26,
                        'price': 8900,
                        'rc': 1,
                        'rrg': 50,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Men's Gordie Loose Fit Straight "
                                 'Leg',
                        'tm': 1540032508650},
                       {'aday': '20181020',
                        'asin': 'B07DDDN2XH',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41s1bRMgmtL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 27,
                        'price': 7175,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Grayson Easy Fit "
                                 'Straight Leg Jeans',
                        'tm': 1540032508652},
                       {'aday': '20181020',
                        'asin': 'B071Z4FR23',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41bePV3qqCL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 28,
                        'price': 3576,
                        'rc': 4,
                        'rrg': 36,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Fowler Joggers",
                        'tm': 1540032508656},
                       {'aday': '20181020',
                        'asin': 'B005GSYPR0',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41HUK459d7L._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 1,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 29,
                        'price': 2990,
                        'rc': 1578,
                        'rrg': 42,
                        'special': 1,
                        'srn': 228,
                        'title': "LEE Men's Relaxed Fit Straight Leg Jean",
                        'tm': 1540032508663},
                       {'aday': '20181020',
                        'asin': 'B071WBX3JX',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41Sf0FMu-SL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 1,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 30,
                        'price': 3699,
                        'rc': 640,
                        'rrg': 41,
                        'special': 1,
                        'srn': 228,
                        'title': "Levi's Men's 502 Regular Taper Jean",
                        'tm': 1540032508700},
                       {'aday': '20181020',
                        'asin': 'B00GA7VVQY',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41Hu1Tk2qLL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 1,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 31,
                        'price': 4494,
                        'rc': 5846,
                        'rrg': 40,
                        'special': 1,
                        'srn': 228,
                        'title': "Levi's Men's 514 Straight Fit Jean",
                        'tm': 1540032508706},
                       {'aday': '20181020',
                        'asin': 'B072MRRBFP',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41izKmWwh4L._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 1,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 32,
                        'price': 5499,
                        'rc': 117,
                        'rrg': 42,
                        'special': 1,
                        'srn': 228,
                        'title': "Levi's Men's 512 Slim Taper Fit Jean",
                        'tm': 1540032508712},
                       {'aday': '20181020',
                        'asin': 'B013VP6TLE',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51kJIqk-7OL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 33,
                        'price': 992,
                        'rc': 3,
                        'rrg': 44,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Flannel Button Up "
                                 'Plaid Shirt',
                        'tm': 1540032508714},
                       {'aday': '20181020',
                        'asin': 'B016U3A6D6',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51HfIKKd5lL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 34,
                        'price': 4399,
                        'rc': 2,
                        'rrg': 45,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Plaid Shirt",
                        'tm': 1540032508716},
                       {'aday': '20181020',
                        'asin': 'B01MYGHMQE',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41PlYHRjZlL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 35,
                        'price': 6299,
                        'rc': 3,
                        'rrg': 45,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Gordie Loose-fit "
                                 'Short',
                        'tm': 1540032508719},
                       {'aday': '20181020',
                        'asin': 'B07HW1L6CJ',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 0,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51VghtmVQVL._AC_US200_.jpg',
                        'is_prime': 0,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 36,
                        'price': 99,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': 'Life After Men: A short story (The Silver '
                                 'Sex Kittens Book 1)',
                        'tm': 1540032508727},
                       {'aday': '20181020',
                        'asin': 'B076Y1P98K',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41xOg5ZdGeL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 37,
                        'price': 3398,
                        'rc': 1,
                        'rrg': 50,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Zac Relaxed Fit Jean "
                                 'Shorts',
                        'tm': 1540032508731},
                       {'aday': '20181020',
                        'asin': 'B071K64RT3',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/414OpXOHzeL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 38,
                        'price': 6999,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Konrad Jeans",
                        'tm': 1540032508734},
                       {'aday': '20181020',
                        'asin': 'B07H4197YY',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 0,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/418B97zH-BL._AC_US200_.jpg',
                        'is_prime': 0,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 39,
                        'price': 2400,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': 'Turkish Style Handmade Jewelry Double Jean '
                                 'Eagle Baguette Cut Sapphire and Round Cut '
                                 "Turquoise 925 Sterling Silver Men's Ring "
                                 'Size Option',
                        'tm': 1540032508740},
                       {'aday': '20181020',
                        'asin': 'B07DD9XQ6Y',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41l-XEPlFpL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 40,
                        'price': 8900,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Konrad Fit Slim Leg",
                        'tm': 1540032508743},
                       {'aday': '20181020',
                        'asin': 'B00DRA7NP0',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 0,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41Ly-AA3k5L._AC_US200_.jpg',
                        'is_prime': 0,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 41,
                        'price': 9900,
                        'rc': 1,
                        'rrg': 40,
                        'special': 1,
                        'srn': 228,
                        'title': 'Silver Jeans Men Zac Flap Relaxed Fit '
                                 'Straight Leg Distressed Hem in Medium Blue',
                        'tm': 1540032508745},
                       {'aday': '20181020',
                        'asin': 'B01N3Z3F2V',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51aFpR9o4wL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 42,
                        'price': 1799,
                        'rc': 3,
                        'rrg': 40,
                        'special': 1,
                        'srn': 228,
                        'title': 'ROUGH ENOUGH Heavy Duty Elastic Nylon '
                                 'Reinforced Military Style Tactical Web Belt '
                                 'Strap with Flip Top Antique Silver Metal '
                                 'Buckle for Teens Men Casual Set',
                        'tm': 1540032508747},
                       {'aday': '20181020',
                        'asin': 'B076XYSL4S',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/410bJRCy8KL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 43,
                        'price': 5215,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Gordie Loose Fit Jean "
                                 'Shorts',
                        'tm': 1540032508753},
                       {'aday': '20181020',
                        'asin': 'B071GCMZTY',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/414kiwCPMmL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 44,
                        'price': 6776,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Men's Konrad Fit Slim Leg, Dark "
                                 'Rinse Wash, 34x30',
                        'tm': 1540032508756},
                       {'aday': '20181020',
                        'asin': 'B008X5LOP4',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41bxg8DRNvL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 45,
                        'price': 7040,
                        'rc': 47,
                        'rrg': 43,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Nash Classic Fit "
                                 'Straight Leg Jeans',
                        'tm': 1540032508761},
                       {'aday': '20181020',
                        'asin': 'B07CFX17NL',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 0,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51Iunb8RutL._AC_US200_.jpg',
                        'is_prime': 0,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 46,
                        'price': 2499,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': 'The Outside Man Original Lobby Card '
                                 'Ann-Margret Jean Louis Trintignant On Run',
                        'tm': 1540032508763},
                       {'aday': '20181020',
                        'asin': 'B01CM6BOQ8',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41oZksH2FFL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 47,
                        'price': 10900,
                        'rc': 4,
                        'rrg': 39,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Zac Relaxed Fit Knit "
                                 'Denim Jeans with Flap Pockets',
                        'tm': 1540032508765},
                       {'aday': '20181020',
                        'asin': 'B013VP715C',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/51XVesJ-QBL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 48,
                        'price': 2499,
                        'rc': 6,
                        'rrg': 42,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Flannel Button Up "
                                 'Plaid Shirt',
                        'tm': 1540032508771},
                       {'aday': '20181020',
                        'asin': 'B016W48DJC',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/41KhvAbE2qL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 49,
                        'price': 1409,
                        'rc': 2,
                        'rrg': 50,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Gray Spade T-shirt",
                        'tm': 1540032508775},
                       {'aday': '20181020',
                        'asin': 'B01N06LOWP',
                        'brand': '',
                        'bsr': None,
                        'category': None,
                        'cid': 0,
                        'fba': 1,
                        'img': 'https://images-na.ssl-images-amazon.com/images/I/418eg0N7zDL._AC_US200_.jpg',
                        'is_prime': 1,
                        'issp': 0,
                        'kw': 'silver jeans men',
                        'msn': 0,
                        'pr': 50,
                        'price': 4561,
                        'rc': 0,
                        'rrg': 0,
                        'special': 1,
                        'srn': 228,
                        'title': "Silver Jeans Co. Men's Grayson Straight Leg "
                                 'Black Jeans',
                        'tm': 1540032508777}])}
    return data


if __name__ == '__main__':
    # asins = [
    #     # 'B00001YVH0',  # 接口中有
    #     # 'B018TDACOS',  # 接口中有
    #     'B0757MWSKK'  # 数据库中有
    # ]
    # for asin in asins:
    #     category = get_category(asin)
    #     # print('分类信息是：', category)
    #     brand = get_brand(asin)
    #     print('品牌信息是：', brand)
    func()
