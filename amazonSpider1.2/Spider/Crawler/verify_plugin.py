#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
# import os
import re
# import time
from functools import wraps

from utils.util import Logger
from utils.util import GetRedis

log_name = sys.argv[0].split('/')[-1].split('.')[0]
debug_log = Logger(log_name=log_name)
redisQ = GetRedis().return_redis(debug_log)


def has_bsr(html_code):
    pattern = re.compile('Best Sellers Rank')
    result = pattern.search(html_code)
    if result:
        return True
    return False



def verify_plugin(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        result = func(*args, **kwargs)
        html = args[1]
        asin = args[2]
        # 判断是否有bsr
        bsr_result = has_bsr(html)
        # 将结果设置进redis以供统计脚本查验.
        redisQ.set('%shasbsr' % (asin), bsr_result, 3600*24)
        # has_bsr1 = str(redisQ.get('%shasbsr' % (asin)), encoding='utf-8')
        # if 'True' in has_bsr1:
        #     print('%shasbsr' % (asin), has_bsr1)
        return result
    return wrap



if __name__ == '__main__':
    from tests.goods_html1 import goods_html1
    html_code = goods_html1
    print(has_bsr(html_code))