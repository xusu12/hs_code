#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import sys
sys.path.append("../")

import time
import pickle
from copy import deepcopy

from utils.util import return_PST
from Crawler.DataOutput import DataOutput
from Crawler.tosellCrawler import TosellCrawler
from Crawler.sellerInventoryCrawler import scrape_inventory


class Tosell(TosellCrawler):

    def download(self, asin_or_kw, url_dict, **kwargs):
        url_type = self.url_type
        asin = asin_or_kw
        monitor_type = url_dict.get('mtp') or 5
        print('url type11: ', url_type)
        startTime = return_PST().strftime("%Y-%m-%d %H:%M:%S")
        time_now = lambda: time.time()
        time1 = time_now()
        url_md5key = url_dict.get('md5') or ''
        if not url_md5key:
            url_md5key = self.get_md5_key(asin + url_type)
        goodsUrl_tuple = self.make_url(asin, url_type='goods')
        goodsUrl, referer = goodsUrl_tuple
        if goodsUrl:
            html_list, url_list, cookiesObj, is_error_lsit, tosellSum = \
                self.get_tosell_html_lsit(asin, goodsUrl, referer, **kwargs)
            old_dnum = url_dict.get('dnum') or 0
            durl = url_dict.get('durl') or []
            url_dict['durl'] = list(set(durl + url_list))
            url_dict['dnum'] = old_dnum + 1
            # 如果判定为没有跟卖, 结束程序
            if self.not_found:
                self.urlQ.record_tosell_notFound_times()
                msgInt = 0
                proxyInfo = 'the asin not tosell'
                self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)
                return self.debug_log.war('%s没有跟卖' % (asin))
            i = -1
            tosell_html_list = []
            if len(html_list) > 0:
                for html in html_list:
                    i += 1
                    is_error = is_error_lsit[i]
                    print(is_error_lsit, is_error_lsit[i])
                    url = url_list[i]
                    if is_error:
                        self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
                        msgInt = 6
                        proxyInfo = 'get Html error'
                        self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)

                    else:
                        analyze = self.analyze_html(html, asin, url_dict, time1,
                                                    startTime, html_type=url_type)
                        if analyze and analyze != 404:
                            tosell_html_list.append(html)
                print('html num: ', len(html_list), 'tosell_html num: ', len(tosell_html_list))
                if len(tosell_html_list) == len(html_list):
                    result, is_error = self.parser(tosell_html_list, html_type=url_type, asin=asin,
                                                   monitor_type=monitor_type, tosellSum=tosellSum,
                                                   goods_html_code=self.goods_html)
                    # from pprint import pprint
                    # pprint('tosell_result', result)
                    if is_error:
                        self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
                        msgInt = 3
                        proxyInfo = 'get data error'
                        self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)
                    else:
                        if not result:
                            self.the_url_is_discard(asin, url_dict, url_type, url_md5key)
                            msgInt = 2
                            proxyInfo = 'get data defeated'
                            self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)
                        else:
                            self.save_success_asin_keyword(asin, url_type=url_type)
                            msgInt = 1
                            proxyInfo = 'get data success'
                            self.record_log(asin, time1, msgInt, url_type, startTime, proxyInfo)
                            tosell_datas = result[0]
                            from pprint import pprint
                            print('*'*10, tosell_datas, '*'*10)
                            pprint(tosell_datas)
                            return tosell_datas
        return {}


def tosell_crawler(asin, url_dict, crawler_obj, goods_html, crawler_param, **kwargs):
    tosell_url_dict = url_dict
    tosell_type = 'tosell'
    md5value = asin + tosell_type
    md5key = crawler_obj.get_md5_key(md5value)
    usedMd5key = crawler_obj.get_md5_key(md5value + 'useInterval')
    print(tosell_url_dict, type(tosell_url_dict))
    tosell_url_dict['utp'] = tosell_type
    tosell_url_dict['md5'] = md5key
    tosell_url_dict['umd5'] = usedMd5key
    tosell = Tosell(*crawler_param)
    tosell_datas = tosell.download(asin, tosell_url_dict, goods_html=goods_html)
    # 打印调试
    from pprint import pprint
    pprint(tosell_datas)
    return tosell_datas


def start(**kwargs):
    '''
    :param kwargs:
        必须参数:
        asin
        user_anget
        html_code
        cookies
        goods_datas
    :return:
    '''
    # 必要参数
    asin = kwargs['asin']
    user_anget = kwargs['user_anget']
    goods_html = kwargs['goods_html']
    cookies = kwargs['cookies']
    goods_datas = kwargs['goods_datas']
    crawler_obj = kwargs['crawler_obj']
    url_dict = kwargs['url_dict']

    # 如果asin校验不通过, 则标记为已下架
    if kwargs.get('asin_') and kwargs.get('asin_') != asin:
        DataOutput.record_not_found_goods(asin)
        DataOutput.record_not_found_tosell(asin)
    # # 调试打印
    from pprint import pprint
    # print('*' * 20)
    # print('productTosellCrawler.goods_datas:')
    # pprint(goods_datas)

    # 非必要参数
    log_param = kwargs.get('log_param')
    # print(log_param, type(log_param))
    # print(crawler_obj)
    if type(log_param) is tuple and crawler_obj:
        crawler_obj.record_log(*log_param)
    crawler_param = (crawler_obj.urlQ, crawler_obj.kwQ, crawler_obj.dataQ, crawler_obj.info_log, crawler_obj.debug_log)
    try:
        tosell_datas = tosell_crawler(asin, url_dict, crawler_obj, goods_html, crawler_param)
    except Exception as e:
        # 如果跟卖下载出错, 结束这个线程.
    	return
    # 解包跟卖数据
    tosell_data, tosell_list = tosell_datas.get(asin, ({}, []))

    # 将跟卖数据包加入库存信息
    inv_list = []
    is_limit = 0
    qty_list = []
    tosell_sum = len(tosell_list)
    # 卖家数量重新赋值
    goods_datas[asin]['to_sell'] = tosell_sum
    # 卖家数量至少为1才去拿库存
    if tosell_sum >= 1:
        for tosell in tosell_list:
            inv_dict = scrape_inventory(tosell)
            # 如果库存大于0则存入库存
            if inv_dict['qty'] > 0:
                qty_list.append(inv_dict['qty'])
            else:
                # 否则存0
                qty_list.append(0)
            if inv_dict['qtydt'] == 2:
                is_limit = 1
            inv_list.append(inv_dict)

    # 标记限售状态
    goods_datas[asin]['is_limit'] = is_limit
    # 库存数量重新赋值
    goods_datas[asin]['quantity'] = sum(qty_list)
    if sum(qty_list) > 0:
        goods_datas[asin]['qtydt'] = 0
    else:
        goods_datas[asin]['qtydt'] = 1
    print('*' * 20)
    print('add to queue goods_datas:')
    pprint(goods_datas)
    goods_bytes = pickle.dumps(goods_datas)
    crawler_obj.dataQ.add_goods_data_to_queue(goods_bytes)
    # 解包bsr详情数据
    bsr_info = goods_datas[asin]['bsr_info']
    if bsr_info:
        # 将bsr详情数据加入数据队列
        bsr_bytes = pickle.dumps({asin: bsr_info})
        crawler_obj.dataQ.add_bsrData_to_queue(bsr_bytes)
    # 将跟卖(含库存)数据加入数据队列
    tosell_qty_datas = {asin: (tosell_data, inv_list)}
    pprint(tosell_qty_datas)
    tosell_bytes = pickle.dumps(tosell_qty_datas)
    crawler_obj.dataQ.add_tosell_to_queue(tosell_bytes)

    '''
    暂时废弃. 作为备用方案(此方案的跟卖数据, 适用1.1的SQL).
    # 将跟卖数据(不含库存)加入数据队列
    pprint(tosell_datas)
    tosell_bytes = pickle.dumps(tosell_datas)
    crawler_obj.dataQ.add_tosell_to_queue(tosell_bytes)
    # 将库存打包发送队列.
    pprint(inv_list)
    inv_dict = {asin: inv_list}
    qty_bytes = pickle.dumps(inv_dict)
    crawler_obj.dataQ.add_seller_qty_to_queue(qty_bytes )
    '''
