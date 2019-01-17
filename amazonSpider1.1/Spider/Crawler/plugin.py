#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''↓↓↓ author: 陈欣群 ↓↓↓'''
import sys

sys.path.append("../")
import os
import time
from functools import wraps
from utils.util import return_PST

save_asin_list = [
    # first
    'B011QTP8HI',
    'B00I08JAYG',
    'B00WY9AS5M',
    'B077ZWCNPP',
    'B01J8UKRH8',
    'B019JS96GC',
    'B00SX72AE6',
    'B071GXRRGR',
    'B00K2MYQ7E',
    'B00JU8HYF2',
    'B01N0GOU4G',
    'B00U4PD6UC',
    'B073PCQH1J',
    'B00MA7AF74',
    'B01F2PA7WS',
    'B01JRY04PK',
    'B00F5UCP30',
    'B077BXPM1W',
    'B078XJ8L38',
    'B002G9UFNK',
    'B000NE8LMM',
    'B002D47XC4',
    'B06WLMDL9Y',
    'B006ZUNMLS',
    'B00535OW6A',
    'B0179KVUVG',
    'B0762S8PYM',
    'B078SZS7C6',
    'B071VCYK5R',
    'B07H1L7TR1',
    'B075FR5V58',
    'B071J32L4S',
    'B07BZ6WJ5Q',

    # second
    'B07DNYMM9G',
    'B07C1C41GB',
    'B07C1C9LBN',
    'B07C1C9LBP',
    'B07C1C9N9T',
    'B07C1C9VG9',
    'B07C1C9W2T',
    'B07C1C9WF6',
    'B07C1C9WK9',
    'B07C1C9WSQ',
    'B07C1C9WWL',
    'B07C1C9WY6',
    'B07C1C9X8W',
    'B07C1C9ZJV',
    'B07C1CB1DV',
    'B07C1CB278',
    'B07C1CB2B9',
    'B07C1PWJFM',
    'B07C1PWJMW',
    'B07C1PWLNM',
    'B07C1PYQ51',
    'B07C1QJQHC',
    'B07C1QLCB7',
    'B07C1QLFHM',
    'B07C1QLFJF',
    'B07C1QLGXZ',
    'B07C1QLHGK',
    'B07C1QLKD8',
    'B07C1QLMFS',
    'B07C1QLNGP',
    'B07C1QLNJJ',
    'B07C1QMC22',
    'B07C1QNCDG',
    'B07C1QNCYY',
    'B07C1QT4RJ',
    'B07C1QT5J8',
    'B07C1QT5Z1',
    'B07C1QT6Q4',
    'B07C1QT91L',
    'B07C1QVVKS',
    'B07C1QVXKT',
    'B07C1QVXVZ',
    'B07C1T8Z9T',
    'B07C1TQZNF',
    'B07C1TSMLB',
    'B07C1TTPXT',
    'B07C1TTRB1',
    'B07C1TTS5W',
    'B07C1TTSCL',
    'B07C1TTW2G',
    'B07C1TTW7X',
    'B07C1TTWS6',
    'B07C1TW26D',
    'B07C1VD1C2',
    'B07CBPK1JL',
    'B07CBQ8D8M',
    'B07CBQK24M',
    'B07CBQXW6W',
    'B07CBRTLZX',
    'B07CBRYYJ2',
    'B07CBRZ776',
    'B07CBS2FRK',
    'B07CBS2FRM',
    'B07CBS9YPL',
    'B07CBSBY98',
    'B07CBSL2Q4',
    'B07CBSQ3BH',
    'B07CBT6HVP',
    'B07CF7BW8C',
]


def save_html(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        '''保存HTML的装饰器, 此装饰器, 装饰在产品详情与库存的解析方法上'''
        # 运行原函数
        result = func(*args, **kwargs)
        try:
            if 'qty' in func.__name__:
                '''如果是获取库存的函数, 用此逻辑获取相应参数'''
                asin = kwargs.get('asin', '')
                html = kwargs.get('html_code', '')
                html_type = 'inventory'
                print(asin, html)
            else:
                '''如果不是获取库存的函数, 用此逻辑获取相应参数'''
                asin = args[2]
                html = args[1]
                html_type = 'product'
            print('*' * 20)
            print(func.__name__, html_type, asin, len(html), type(html))
            print('*' * 20)
            ## 在 save_asin_list 中的 asin 才保存
            # if asin in save_asin_list:
            '''注释掉上面一行后, 则是所有合法HTML都保存.'''
            if type(html) is str and html:
                print(1111111111)
                # 获取pt时间
                datenow = return_PST()
                # 文件保存目录
                # base_dir = '/data3/var/devtest/'
                base_dir = '../../data/devtest/'
                # 若目录不存在, 分级创建各种目录
                if not os.path.exists(base_dir):
                    os.mkdir(base_dir)
                html_dir = os.path.join(base_dir, 'save_asin_html/')
                if not os.path.exists(html_dir):
                    os.mkdir(html_dir)
                save_dir = os.path.join(html_dir, datenow.strftime('%Y%m%d'))
                if not os.path.exists(save_dir):
                    os.mkdir(save_dir)
                # 生成文件名
                file_path = os.path.join(save_dir,
                                         '%s_%s_%s.html' % (asin, html_type, datenow.strftime('%Y%m%d_%H_%M_%S')))
                # 将HTML写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)

                print(2222222)
        except Exception as e:
            print(e)
        return result

    return wrap


'''↑↑↑ author: 陈欣群 ↑↑↑'''


def save_kw_html(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        '''保存HTML的装饰器, 此装饰器, 装饰在关键字的解析方法上'''
        # 运行原函数
        result = func(*args, **kwargs)

        try:
            keyword = args[2]
            html_list = args[1]
            html_type = 'keyword'
            # print(keyword, html_list)

            print('*' * 20)
            print(func.__name__, html_type, keyword, len(html_list), type(html_list))
            print('*' * 20)
            ## 在 save_asin_list 中的 asin 才保存
            # if asin in save_asin_list:
            '''注释掉上面一行后, 则是所有合法HTML都保存.'''
            if type(html_list) is list and html_list:
                i = 1
                for html in html_list:
                    # 获取pt时间
                    datenow = return_PST()
                    # 文件保存目录
                    base_dir = '../../data/devtest/'
                    # 若目录不存在, 分级创建各种目录
                    if not os.path.exists(base_dir):
                        os.mkdir(base_dir)
                    html_dir = os.path.join(base_dir, 'save_asin_html/')
                    if not os.path.exists(html_dir):
                        os.mkdir(html_dir)
                    save_dir = os.path.join(html_dir, datenow.strftime('%Y%m%d'))
                    if not os.path.exists(save_dir):
                        os.mkdir(save_dir)
                    # 生成文件名
                    keyword = '_'.join(keyword.split(' '))
                    print(keyword, i)
                    file_path = os.path.join(save_dir,
                                             '%s_%s_%s_%s.html' % (keyword, html_type, datenow.strftime('%Y%m%d_%H_%M_%S'), i))
                    # 将HTML写入文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    i += 1
        except Exception as e:
            print(e)
        return result

    return wrap