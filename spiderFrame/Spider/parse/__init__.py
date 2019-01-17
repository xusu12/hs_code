#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
将parse包中的模块中的变量, 都加载为items包的变量, 简化外部模块导包层级
包内新增的模块, 要注册在 FRAME_BASE 列表中.
包内模块导入包内模块成员是, 统一用多级路径导入.
from Spider.parse.productParse import PriceParse
包外模块导入包内成员时, 可以统一从 __init__.py 即 包本身导入.
from parse import PriceParse
'''

import sys
sys.path.append("../")
sys.path.append("../../")

from importlib import import_module


# 要加载的基础模块
FRAME_BASE = [
    'Spider.parse.productParse'
]
mod_list = []
for item in FRAME_BASE:
    mod_list.append(import_module(item))

# 加载 FRAME_BASE 成员的动态代码
mod_vaule = '''
{} = getattr(mod, '{}')
'''

# 动态生成代码
for mod in mod_list:
    for item in dir(mod):
        if not item.startswith('__'):
            code = mod_vaule.format(item, item)
            exec(code)
