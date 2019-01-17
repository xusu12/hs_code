#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
sys.path.append("../../")
from importlib import import_module

from Base import Items
from Spider.items.itemsConf import product_items_conf as conf
from Spider.items.itemsConf import product_parse_module as parse_name


# 导入产品解析模块
parse_module = import_module(parse_name)


class ProductItem(Items):
    def __init__(self, config=None, module=None):
        '''
        初始化之后, 先调用super方法, 然后设置 配置字典, 初始化配置字典.
        实例初始化之后, 实例属性self.__dict__ 会变成{'filed': callble object} 这样的结构.
        而实例本身, 是一个 callable 对象. 只接受一个字典参数.
        实例本身没有返回值.
        instance = ProductItem()
        params = {'html_code': html, 'xpath_obj': lxml.etree.HTML(html), 'bs4_obj': BeautifulSoup(html, 'lxml')}
        instance(params)
        data_dict = instance.__dict__
        :param config: 一个字典, 键是数据库所需字段的键, 值是解析这个字段的类(必须是可调用类), 或者函数的名字, string型.
        :param module: 一个python模块对象.
        '''
        super(ProductItem, self).__init__()
        self.module = module if module else parse_module
        config = config if config else conf()
        self.config = self.filrt_call_conf(config, self.module)
        self.init_config(self.config)


if __name__ == '__main__':
    import glob
    import lxml.etree as etree
    file_list = glob.glob('../tests/*.html')
    parmas = {}
    for file_name in file_list:
        product = ProductItem()
        with open(file_name, 'r', encoding='utf-8') as f:
            html = f.read()
        parmas['html_code'] = html
        parmas['xpath_obj'] = etree.HTML(html)
        product(parmas)
        print(id(product), product.__dict__)