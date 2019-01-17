#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
import os
import time

from conf.setting import REPORT_DIR
from utils.util import Logger, GetRedis, IpQueue, DataQueue, UrlQueue, return_PST
from conf.setting import BASE_TYPE


def statistics(ipQ, urlQ, dataQ, debug_log, num=60):
    if BASE_TYPE == 'develop':
        num = 10
    i = 0
    while True:
        time.sleep(num)
        i += 1
        print('statistics 循环计数 %s \n' % (i))
        if i % 60 == 0:
            # 重设为0节约内存
            i = 0
            if urlQ.retrieve_goodsUrl_len() > 0:
                DisabledDict = {}
                RobotChekDict = {}
                useDict = {}
                ipSetDisabled = ipQ.return_disabled_IP()
                if ipSetDisabled:
                    for ip in ipSetDisabled:
                        DisabledDict[str(ip[0]).split("'")[1]] = ip[1]
                print('\nDisabledDict', DisabledDict)

                ipSetRobotChek = ipQ.return_RobotChek_IP()
                if ipSetRobotChek:
                    for ip in ipSetRobotChek:
                        RobotChekDict[str(ip[0]).split("'")[1]] = ip[1]
                print('\nRobotChekDict', RobotChekDict)

                ipUseTimes = ipQ.return_use_times()
                if ipUseTimes:
                    for ip in ipUseTimes:
                        useDict[str(ip[0]).split("'")[1]] = ip[1]
                print('\nuseDict', useDict)
                urlNum = urlQ.get_html_ok_times()
                goodsNum = urlQ.get_goodsHtml_ok_times()
                keywordNum = urlQ.get_keywordHtml_ok_times()
                tosellNum = urlQ.get_tosellHtml_ok_times()
                reviewsNum = urlQ.get_reviewsHtml_ok_times()
                print('\nurlNum', urlNum)
                if not urlNum:
                    urlNum = 0
                dataNum = dataQ.get_data_ok_times()
                dbSumNum = dataQ.get_dbSum_times()
                dbOkNum = dataQ.get_db_ok_times()
                goodsOkNum = dataQ.get_goods_ok_times()
                reviewsOkNum = dataQ.get_reviews_ok_times()
                tosellOkNum = dataQ.get_tosell_ok_times()
                keywordOkNum = dataQ.get_keyword_ok_times()
                keywordNotFundNum = dataQ.get_keyword_not_fund_times()
                dataRatio = dbRatio = goodsRatio = reviewsRatio = tosellRatio = keywordRatio = 0
                if urlNum > 0:
                    dataRatio = dataNum / urlNum
                if dbSumNum > 0:
                    dbRatio = dbOkNum / dbSumNum
                if goodsNum > 0:
                    goodsRatio = goodsOkNum / goodsNum
                if reviewsNum > 0:
                    reviewsRatio = reviewsOkNum / reviewsNum
                if tosellNum > 0:
                    tosellRatio = tosellOkNum / tosellNum
                if keywordNum > 0:
                    keywordRatio = keywordOkNum / (keywordNum - keywordNotFundNum)
                print('\ndataNum', dataNum)
                if not dataNum:
                    dataNum = 0
                pstNow = return_PST()
                timeNow = pstNow.strftime("%Y-%m-%d %H:%M:%S")
                dateNow = pstNow.strftime("%Y_%m_%d")
                statFile = os.path.join(REPORT_DIR, 'statistics_%s.txt' % (dateNow))
                try:
                    with open(statFile, 'a') as f:
                        f.write('\r\n[%s] 分时报告' % (timeNow))
                        f.write(
                            '[网络请求成功总次数: %s]; [数据解析成功总次数: %s]; [总成功率: %.2f%%]; \n' % (urlNum, dataNum, dataRatio * 100))
                        f.write('[数据入库总次数: %s]; [入库成功总次数: %s]; [成功率: %.2f%%]; \n' % (dbSumNum, dbOkNum, dbRatio * 100))
                        f.write('[goods 网络请求成功次数: %s]; [goods 数据解析成功次数: %s]; [goods 成功率: %.2f%%]; \n' % (
                        goodsNum, goodsOkNum, goodsRatio * 100))
                        f.write('[reviews 网络请求成功次数: %s]; [reviews 数据解析成功次数: %s]; [reviews 成功率: %.2f%%]; \n' % (
                        reviewsNum, reviewsOkNum, reviewsRatio * 100))
                        f.write('[tosell 网络请求成功次数: %s]; [tosell 数据解析成功次数: %s]; [tosell 成功率: %.2f%%]; \n' % (
                        tosellNum, tosellOkNum, tosellRatio * 100))
                        f.write(
                            '[keyword 网络请求成功次数: %s]; [keyword 不存在次数: %s]; [keyword 数据解析成功次数: %s]; [keyword 成功率(排除关键字不存在的情况): %.2f%%]; \n' %
                            (keywordNum, keywordNotFundNum, keywordOkNum, keywordRatio * 100))
                        urlQ.pop_html_ok_times()
                        urlQ.pop_goodsHtml_ok_times()
                        urlQ.pop_reviewsHtml_ok_times()
                        urlQ.pop_tosellHtml_ok_times()
                        urlQ.pop_keywordHtml_ok_times()
                        dataQ.pop_data_ok_times()
                        dataQ.pop_dbSum_times()
                        dataQ.pop_db_ok_times()
                        dataQ.pop_goods_ok_times()
                        dataQ.pop_reviews_ok_times()
                        dataQ.pop_tosell_ok_times()
                        dataQ.pop_keyword_ok_times()
                        dataQ.pop_keyword_not_fund_times()
                        if useDict and type(useDict) is dict:
                            for item in useDict:
                                ip = item
                                useNum = useDict[item]
                                disabledNum = 0
                                RobotChekNum = 0
                                if item in DisabledDict:
                                    disabledNum = DisabledDict[item]
                                if item in RobotChekDict:
                                    RobotChekNum = RobotChekDict[item]
                                if useNum > 0:
                                    RobotRatio = RobotChekNum / useNum
                                    disabledRatio = disabledNum / useNum
                                else:
                                    RobotRatio = disabledRatio = 0
                                f.write('Ip [%s] 总使用次数 %s; 遭遇验证码次数 %s, 验证码几率: %.2f%%; 请求失败次数 %s, 失败几率: %.2f%%; \n' %
                                        (ip, useNum, RobotChekNum, RobotRatio * 100, disabledNum, disabledRatio * 100))
                                ipQ.pop_use_times(item)
                                if disabledNum > 0:
                                    ipQ.pop_disabled_IP(item)
                                if RobotChekNum > 0:
                                    ipQ.pop_RobotChek_IP(item)
                    debug_log.war('%s 报告生成成功 %s; \n' % (statFile, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
                except Exception as e:
                    debug_log.error('生成报告时 [%s]; \n' % (e))



if __name__ == '__main__':
    debug_log = Logger()
    myRedis = GetRedis().return_redis(debug_log)
    ipQ = IpQueue(myRedis, debug_log)
    dataQ = DataQueue(myRedis, debug_log)
    urlQ = UrlQueue(myRedis, debug_log)
    statistics(ipQ=ipQ, urlQ=urlQ, dataQ=dataQ, debug_log=debug_log, num=0.5)
