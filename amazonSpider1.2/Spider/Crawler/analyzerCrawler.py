#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys

from utils.util import UrlQueue, Logger, DataQueue, KeyWordQueue, GetRedis

sys.path.append("../")
import psycopg2
from Crawler.goodsCrawler import GoodsCrawler
from Crawler.keywordCrawler import KwCrawler
from conf.setting import DATADB_CONFIG, BASE_TYPE
from Spider.conf.setting import BASE_TYPE, ANALYZER_KEYWORD_T_NUM, ANALYZER_GOODS_T_NUM
from utils.container import MyList
from conf.setting import develop_e_name

'''
1. 导入goods kw  继承  重构run方法
2. 写一个调度器 amazon_analyzer_task拿数据
3. 拆分任务  两个asin给goods类  一堆关键词给kw类
'''

asin_list = MyList()
kw_list = MyList()

log_name = sys.argv[0].split('/')[-1].split('.')[0]
info_log = Logger(log_level='info', log_name=log_name)
debug_log = Logger(log_name=log_name)
myRedis = GetRedis().return_redis(debug_log)
urlQ = UrlQueue(myRedis, debug_log)
dataQ = DataQueue(myRedis, debug_log)
kwQ = KeyWordQueue(myRedis, debug_log)
debug_log = Logger(log_name=log_name)


class AnalyzerGoodsCrawler(GoodsCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def url_len(self):
        return len(asin_list)

    def get_asin_monitor(self, url_type='', retry=10):
        try:
            asin = asin_list.next()
            url_dict = {'asin':asin}
            return url_dict.get('asin', ''), url_dict
        except StopIteration as e:
            return '', {}


class AnalyzerKeywordCrawler(KwCrawler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def url_len(self):
        return len(kw_list)

    def get_keyword(self, retry=10):
        try:
            kw = kw_list.next()
            url_dict = {'kw': kw}
            return url_dict.get('kw', ''), url_dict
        except StopIteration as e:
            return '', {}

    def get_asin_monitor(self, url_type='', retry=10):
        if url_type == 'keyword':
            return self.get_keyword()


def goods_crawler_start():
    t_num = ANALYZER_KEYWORD_T_NUM
    if BASE_TYPE == develop_e_name:
        t_num = 1
    while True:
        llen = len(asin_list)
        # 如果asin_list的长度为0  那么就断开循环
        if not llen:
            break
        crawlers = [AnalyzerGoodsCrawler(urlQ, dataQ, kwQ, info_log, debug_log) for i in range(t_num)]
        for craw in crawlers:
            craw.start()
        for craw in crawlers:
            craw.join()


def kw_crawler_start():
    t_num = ANALYZER_GOODS_T_NUM
    print(t_num)
    if BASE_TYPE == develop_e_name:
        t_num = 1
    while True:
        llen = len(kw_list)
        if not llen:
            break
        crawlers = [AnalyzerKeywordCrawler(urlQ, dataQ, kwQ, info_log, debug_log) for i in range(t_num)]
        for craw in crawlers:
            craw.start()
        for craw in crawlers:
            craw.join()


# 从redis队列中获取每个任务  拆分任务并调用相应的爬虫方法
def task_start(cur):
    # 1. 从redis中获取任务
    task = myRedis.rpop('taskQueue')
    # 拿到每一个任务字典
    task_dict = eval(task.decode())

    tid = task_dict['tid']
    asin_l = task_dict['asin']
    kw_l = task_dict['kw']

    # 将每个任务中的asin添加到list中
    for asin in asin_l.split(','):
        print(asin)
        asin_list.add(asin)

    for kw in kw_l:
        kw_list.add(kw)

    # 更新数据库
    cur.execute("update public.amazon_analyzer_task set crawler_state=1 where tid=%s" % tid)

    print(len(kw_list))
    print(len(asin_list))

    # 2. 拆分数据  分别调用两个爬虫类
    # 调用goods爬虫类
    goods_crawler_start()
    # 调用kw爬虫类
    kw_crawler_start()


# 从数据库中获取每一个任务的数据  并将数据打包成字典 存入redis队列中
def scheduler():
    # 1. 连接数据库 获取数据
    # 建立数据库连接
    conn = psycopg2.connect(**DATADB_CONFIG[BASE_TYPE])
    # 建立游标
    cur = conn.cursor()
    # 查询数据库中的数据
    cur.execute(
        "select tid, aid, asins, kws, state, create_tm from public.amazon_analyzer_task where state=1 and crawler_state=0;")
    asin_rows = cur.fetchall()
    for asin_row in asin_rows:
        tid = asin_row[0]
        asin = asin_row[2]
        kw = asin_row[3]
        if kw:
            # 如果任务中的kw不是为空  就将kw转化成字典
            k = json.loads(kw)
            kw = []
            for key, value in k.items():
                kw.extend(value)

        task_dict = {'tid': tid, 'asin': asin, "kw": kw}
        # 将数据保存到redis中
        myRedis.lpush('analyzerTaskQueue', task_dict)
        # print(task_dict)
        task_start(cur)
    # 提交操作到数据库
    conn.commit()
    # 关闭连接
    conn.close()


if __name__ == '__main__':
    scheduler()
