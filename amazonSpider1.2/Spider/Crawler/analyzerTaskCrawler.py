#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")

import time
import pickle
import json
import psycopg2

from conf.setting import BASE_TYPE
from conf.setting import develop_e_name
from Crawler.productUtils import get_the_time
from conf.setting import DATADB_CONFIG, BASE_TYPE
from utils.util import return_PST
from utils.util import Logger, GetRedis, UrlQueue, KeyWordQueue, DataQueue


queue_name = 'analyzerTaskQueue'


# 获取任务
def get_task(urlQ, retry=10):

    url_tuple = urlQ._get_member_from_queue(queue_name)
    # 如果 取出来是空数据
    if len(url_tuple) < 1:
        # 查询队列长度
        urllen = urlQ._get_queue_len(queue_name)
        # 如果队列长度大于0
        if urllen > 0:
            time.sleep(0.1)
            # 重试
            return get_task(urlQ, retry=retry - 1)
        else:
            # 否则返回空字典
            return {}
    # 还原任务字典
    print(url_tuple, type(url_tuple))
    print(url_tuple[0], type(url_tuple[0]))
    task_dict = pickle.loads(url_tuple[1])
    if type(task_dict) is dict:
        # 如果数据合法, 则返回
        return task_dict
    else:
        # 否则查询队列长度
        urllen = urlQ._get_queue_len(queue_name)
        # 如果队列长度大于0
        if urllen > 0:
            time.sleep(0.1)
            # 重试
            return get_task(urlQ, retry=retry - 1)
        else:
            # 否则返回空字典
            return {}



def save_task_to_db(urlQ, data_dict, url_type=''):
    data_bytes = pickle.dumps(data_dict)
    result = False
    if url_type == 'goods':
        queue_name = 'monitorGoods'
    elif url_type == 'keyword':
        queue_name = 'monitorKeyword'
    else:
        queue_name = ''
    if queue_name:
        if urlQ._get_queue_len(queue_name) > 500:
            result = urlQ._rpushx_member_to_queue(queue_name, data_bytes)
        else:
            result = urlQ._add_member_to_queue(queue_name, data_bytes)
    return result

# 更改分析状态
def update_analyzer_state(tid, aid, crawler_state, finish_count=0, finish_kws=''):
    conn = psycopg2.connect(**DATADB_CONFIG[BASE_TYPE])
    cur = conn.cursor()
    print(update_analyzer_state.__name__+ '0', tid, aid, crawler_state, finish_count, finish_kws)
    if finish_kws:
        print(update_analyzer_state.__name__+ '1', tid, aid, crawler_state, finish_count, finish_kws)
        sql = "update public.amazon_analyzer_task set is_sync=0, update_tm=extract(epoch from now()), crawler_state=%(crawler_state)s, \
        crawler_finish_count=%(crawler_finish_count)s, finish_kws=%(finish_kws)s where tid=%(tid)s and aid=%(aid)s;"
        cur.execute(sql, {'crawler_state': crawler_state, 'crawler_finish_count':finish_count, 'tid':tid, 'aid': str(aid), 'finish_kws': finish_kws})
        row = cur.rowcount
        print(row, '行 update public.amazon_analyzer_task ')
    else:
        print(update_analyzer_state.__name__+ '2', tid, aid, crawler_state, finish_count, finish_kws)
        sql = "update public.amazon_analyzer_task set crawler_state=%s, crawler_finish_count=%s where tid=%s and aid='%s'" \
            % (crawler_state, finish_count, tid, aid)
        cur.execute(sql)
        row = cur.rowcount
        print(row, '行 update public.amazon_analyzer_task ')
    conn.commit()
    cur.close()
    conn.close()


def select_analyzer_state(asins, kws, urlQ, aid, tid, aday=None):
    if not aday:
        aday = return_PST().strftime("%Y%m%d")
    _, init_time = get_the_time()
    asin_tuple = tuple(set(asins))
    kw_tulep = tuple(set(kws))
    asin_sql = 'select count(*) from amazon_product_data where getinfo_tm > ' + str(init_time - 3600 * 2) +  'and asin in %s;'
    the_vaule = lambda lst: lst[0][0] if len(lst) > 0 and type(lst[0]) is tuple and len(lst[0]) > 0 else 0
    asin_count = the_vaule(urlQ.retrieve_asin(asin_sql, [asin_tuple]))
    print(asin_count, type(asin_count))
    # kw_sql = 'select count(*) from amazon_keyword_data where getinfo_tm > ' + str(init_time - 3600 * 2) + 'and kw in %s;'
    # kw_count = the_vaule(urlQ.retrieve_asin(kw_sql, [kw_tulep]))
    # print(kw_count, type(kw_count))
    sql1 = "select kw from public.amazon_druid_keyword_data where tm > " + str(init_time - 3600 * 2)
    sql2 = sql1 + "and kw in %s group by kw;"
    print(sql2)
    get_vlues = lambda lst: [x[0] for x in lst if len(lst) > 0 and type(x) is tuple and len(x) > 0]
    rows = get_vlues(urlQ.retrieve_asin(sql2, [kw_tulep]))
    # rows = list(set(rows))
    finish_kws = json.dumps(rows)
    finish_count = len(rows)
    print(finish_kws, type(finish_kws))
    print('总共 %s 个asin, %s 个关键词\n已更新%s个asin, %s个关键词' % (len(asin_tuple), len(kw_tulep), asin_count, finish_count))
    # 有90%的关键词完成, 就可以标记完成状态了.
    if len(kw_tulep) - finish_count < len(kw_tulep) * 0.1:
        # 标记爬虫完成(crawler_state=2).
        update_analyzer_state(tid, aid, 2, finish_count, finish_kws=finish_kws)
        return True


def analyzer_start(urlQ, dataQ, kwQ, info_log, debug_log, i):
    print('\nanalyzer_start%s 启动成功' % (i))
    while True:
        urllen = urlQ._get_queue_len(queue_name)
        print('当前analyzer任务队列长度 %s' % (urllen))
        if urllen < 1:
            sys.exit()
        # 获取任务字典
        task_dict = get_task(urlQ)
        # 提取监测时间
        mtm = task_dict.get('mtm', int(time.time()))
        # 提取aid
        aid = task_dict.get('aid', -1)
        # 提取tid
        tid = task_dict.get('tid')

        # 解包asin加工后重新打包
        asin_list = task_dict.get('asins', [])
        for asin in asin_list:
            asin_dict = dict(asin=asin, monitor_tm=mtm, aid=aid, utp='goods')
            # 将asin加入监测
            save_task_to_db(urlQ, asin_dict, url_type='goods')
        # 解包关键词加工后并重新打包
        kws_dict = task_dict.get('kws', {})
        # print(kws_dict, type(kws_dict))
        kw_list = []
        for k, v in kws_dict.items():
            # print(k, type(k))
            # print(v, type(v))
            kw_list.extend(v)
        for kw in kw_list:
            kw_dict = dict(aid=aid, monitor_tm=mtm, kw=kw, utp='keyword')
            # 将关键词加入监测
            save_task_to_db(urlQ, kw_dict, url_type='keyword')
        # 更改分析器状态(1 分析中)
        update_analyzer_state(tid, aid, 1)
        aday = return_PST().strftime("%Y%m%d")
        while 1:
            if select_analyzer_state(asin_list, kw_list, urlQ, aid, tid, aday=aday):
                break
            time.sleep(60 * 5)

if __name__ == '__main__':
    log_name = sys.argv[0].split('/')[-1].split('.')[0]
    info_log = Logger(log_level='info', log_name=log_name)
    debug_log = Logger(log_name=log_name)
    myRedis = GetRedis().return_redis(debug_log)
    urlQ = UrlQueue(myRedis, debug_log)
    dataQ = DataQueue(myRedis, debug_log)
    kwQ = KeyWordQueue(myRedis, debug_log)
    debug_log = Logger(log_name=log_name)
    analyzer_start(urlQ, dataQ, kwQ, info_log, debug_log, 1)