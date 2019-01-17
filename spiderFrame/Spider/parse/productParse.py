#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

sys.path.append("../")
sys.path.append("../../")
import re

from Base import Parse


class PriceParse(Parse):

    def __init__(self):
        '''
        继承之后, 要先调用super方法.
        注册方法的时候, 要注意只注册有最终结果返还的主方法.
        主方法用 "get" 开头命名.被主方法调用的辅助方法用"_" 单下划线开头命名.
        一些字段的xpath之间, 会互相冲突的, 要注意分清先后顺序.
        一个方法内, 最好只有一条xpath表达式, 或者正则表达式.
        而实例本身, 是一个 callable 对象. 只接受一个字典参数.
        返回值是 注册过的 主方法的最终返回值.
        单独调用示例:
        instance = PriceParse()
        params = {'html_code': html, 'xpath_obj': lxml.etree.HTML(html), 'bs4_obj': BeautifulSoup(html, 'lxml')}
        price = instance(params)
        '''
        super(PriceParse, self).__init__()

        # 提取价格的正则表达式.
        self.pattern = re.compile('\$[\d,\.]+')
        # 处理有逗号有小数点有空格的价格 string
        self.filtr = lambda price_str: ''.join(
            ''.join(''.join(price_str.split('$')).split(',')).split('.')).strip().lstrip()

        # 注册顺序不能乱.每个方法都独写一行注册, 方便调整顺序, 或者注释单个方法.
        self.register(self.get_price_from_xpath1.__name__)
        self.register(self.get_price_from_xpath2.__name__)
        self.register(self.get_price_from_xpath3.__name__)
        self.register(self.get_price_from_xpath4.__name__)
        self.register(self.get_price_from_xpath5.__name__)
        self.register(self.get_price_from_xpath6.__name__)
        self.register(self.get_price_from_xpath7.__name__)
        self.register(self.get_price_from_xpath8.__name__)
        self.register(self.get_price_from_xpath9.__name__)

    def _filtr_price_data(self, result_list: list) -> int or None:
        '''
        传入一个xpath的结果集, 用正则提取, 字符串操作等对结果集进行清洗过滤, 返还None 或者合法的 int型结果.
        :param params: {'xpath_obj': object, 'html_code': str, 'bs4_obj': object}
        :return: int or None
        '''
        result_str = ''.join(result_list)
        serch_result = self.pattern.search(result_str)
        if serch_result:
            result = serch_result.group(0)
            result = self.filtr(result)
            if result.isdigit():
                return int(result)

    def get_price_from_xpath1(self, parmas: dict) -> int or None:
        '''
        新写的或者已经摸清情况的每一行xpath表达式的尾部注释, 都加一两个 亚马逊的asin 以此标记xpath所对应的亚马逊页面.
        :param parmas: {'xpath_obj': object, 'html_code': str, 'bs4_obj': object}
        :return: int or None
        '''
        xpath_obj = parmas.get('xpath_obj')
        xpath_list = [
            '//*[@id="priceInsideBuyBox_feature_div"]//*[@id="price_inside_buybox"]/text()',  # B00XLBELKK 优先拿购物车价格解决冲突
            '//*[contains(text(), "Price:")]/..//*[contains(@class, "a-color-price")]//text()',
        ]
        result_list = self.get_new_data(expr_list=xpath_list, xpath_obj=xpath_obj)
        return self._filtr_price_data(result_list)

    def get_price_from_xpath2(self, parmas: dict) -> int or None:
        xpath_obj = parmas.get('xpath_obj')
        xpath_list = [
            '//*[contains(text(), "Price:")]/../..//*[contains(@class, "a-color-price")]//text()',
        ]
        result_list = self.get_new_data(expr_list=xpath_list, xpath_obj=xpath_obj)
        return self._filtr_price_data(result_list)

    def get_price_from_xpath3(self, parmas: dict) -> int or None:
        xpath_obj = parmas.get('xpath_obj')
        xpath_list = [
            '//*[contains(text(), "Buy New")]/../..//text()',
        ]
        result_list = self.get_new_data(expr_list=xpath_list, xpath_obj=xpath_obj)
        return self._filtr_price_data(result_list)

    def get_price_from_xpath4(self, parmas: dict) -> int or None:
        xpath_obj = parmas.get('xpath_obj')
        xpath_list = [
            '//*[contains(@id, "snsPrice")]//*[contains(@class, "price")]/text()',  # 案例 B014TF6LRC
        ]
        result_list = self.get_new_data(expr_list=xpath_list, xpath_obj=xpath_obj)
        return self._filtr_price_data(result_list)

    def get_price_from_xpath5(self, parmas: dict) -> int or None:
        xpath_obj = parmas.get('xpath_obj')
        xpath_list = [
            '//*[contains(@id, "buybox")]//*[contains(@id, "buyNew")]//*[contains(@class, "price")]/text()',
            # 案例　0060012781　0060899220
        ]
        result_list = self.get_new_data(expr_list=xpath_list, xpath_obj=xpath_obj)
        return self._filtr_price_data(result_list)

    def get_price_from_xpath6(self, parmas: dict) -> int or None:
        xpath_obj = parmas.get('xpath_obj')
        xpath_list = [
            '//*[contains(@id, "addToCart")]//*[contains(@id, "price")]/text()',  # 案例　B01LYCX1GU　B016X6SEAC
        ]
        result_list = self.get_new_data(expr_list=xpath_list, xpath_obj=xpath_obj)
        return self._filtr_price_data(result_list)

    def get_price_from_xpath7(self, parmas: dict) -> int or None:
        xpath_obj = parmas.get('xpath_obj')
        xpath_list = [
            '//*[contains(@id, "newPrice")]//*[contains(@class, "priceblock")]//text()',  # 案例　B01N5OKGLH 游戏类
        ]
        result_list = self.get_new_data(expr_list=xpath_list, xpath_obj=xpath_obj)
        # 这一条xpath表达式, 返回的值, 结构与前面的都不一样, 所以要多一步操作
        item_list = []
        if len(result_list) > 0:
            for item in result_list:
                item = item.lstrip.strip()
                if item:
                    item_list.append(item)
        return self._filtr_price_data(item_list)

    def get_price_from_xpath8(self, parmas: dict) -> int or None:
        xpath_obj = parmas.get('xpath_obj')
        xpath_list = [
            '//*[contains(@id, "price")]//*[contains(@id, "priceblock")]/text()',  # 案例 B014TF6LRC
        ]
        result_list = self.get_new_data(expr_list=xpath_list, xpath_obj=xpath_obj)
        return self._filtr_price_data(result_list)

    def get_price_from_xpath9(self, parmas: dict) -> int or None:
        xpath_obj = parmas.get('xpath_obj')
        xpath_list = [
            '//*[contains(@id, "price-quantity")]//*[contains(@class, "a-color-price")]/text()',  # 案例　B016X6SEAC
        ]
        result_list = self.get_new_data(expr_list=xpath_list, xpath_obj=xpath_obj)
        return self._filtr_price_data(result_list)


class BrandParse(Parse):
    def __init__(self):
        '''
        继承之后, 要先调用super方法.
        注册方法的时候, 要注意只注册有最终结果返还的主方法.
        主方法用 "get" 开头命名.被主方法调用的辅助方法用"_" 单下划线开头命名.
        一些字段的xpath之间, 会互相冲突的, 要注意分清先后顺序.
        一个方法内, 最好只有一条xpath表达式, 或者正则表达式.
        而实例本身, 是一个 callable 对象. 只接受一个字典参数.
        返回值是 注册过的 主方法的最终返回值.
        单独调用示例:
        instance = PriceParse()
        params = {'html_code': html, 'xpath_obj': lxml.etree.HTML(html), 'bs4_obj': BeautifulSoup(html, 'lxml')}
        price = instance(params)
        '''
        super(BrandParse, self).__init__()

        # 提取价格的正则表达式.
        self.pattern = re.compile('\$[\d,\.]+')
        # 处理有逗号有小数点有空格的价格 string
        self.filtr = lambda price_str: ''.join(
            ''.join(''.join(price_str.split('$')).split(',')).split('.')).strip().lstrip()

        # 注册顺序不能乱.每个方法都独写一行注册, 方便调整顺序, 或者注释单个方法.
        self.register(self.get_price_from_xpath1.__name__)

    def get_price_from_xpath1(self, parmas: dict):
        return 'brand'


def ts(parmas):
    return 'ts'


if __name__ == '__main__':
    import glob
    import lxml.etree as etree

    file_list = glob.glob('../tests/*.html')
    html = ''
    parmas = {}
    get_data = PriceParse()
    for file_name in file_list:
        with open(file_name, 'r', encoding='utf-8') as f:
            html = f.read()
            parmas['html_code'] = html
            parmas['xpath_obj'] = etree.HTML(html)
            data = get_data(parmas)
            print(file_name, data)
