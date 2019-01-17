#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
sys.path.append("../../")

# 要导入的模块名. 新写了一个解析模块, 就在此配置.
product_parse_module = 'Spider.parse.productParse'

# 新增的配置字典, 一定要写成lambda, 不然的话, conf dict 就会变成一个全局可变变量, 只有第一次引用能够正常使用.
product_items_conf = lambda: dict(
    # 键是数据库所需字段的键, 值是解析这个字段的类(必须是可调用类), 或者函数的名字, string型.
    # 如果类名有修改, 也要改动相应的配置文件.
    price='PriceParse',     # 价格
    brand='BrandParse',     # 品牌
    ts='ts',

)




