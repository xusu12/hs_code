#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
import re
from utils.util import Logger, GetRedis, UrlQueue


# 商品重试
def goods_retry(urlQ, sql):
    if type(sql) is not str:
        return
    not_pattern = re.compile('delete|update|insert|INSERT|UPDATE|DELETE')
    if not_pattern.findall(sql):
        print('buhefa', sql)
        return not_pattern.findall(sql)
    else:
        print(sql)
        try:
            return urlQ.retrieve_asin(sql)
        except Exception as e:
            return [e]
         



if __name__ == '__main__':
    '''定时器, 每天16-23点的第3分钟执行'''
    '''定时器, 每天0-14点的第3分钟执行'''
    debug_log = Logger()
    myRedis = GetRedis().return_redis(debug_log)
    urlQ = UrlQueue(myRedis, debug_log)
    while True:
        sql = input('sql:')
        data = goods_retry(urlQ, sql)
        from pprint import pprint
        pprint(data)


select asin,title,image, brand,category  from public.amazon_product_data;
select asin,title,img, brand,category  from public.amazon_druid_keyword_data limit 10;
select asin,title,img, brand, aday  from public.amazon_druid_keyword_data order by aday desc limit 1000;
select asin,title,img, brand, aday  from public.amazon_druid_keyword_data group by asin;