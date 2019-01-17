#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
from copy import deepcopy
from datetime import timedelta

from sqlalchemy import desc

from utils.util import return_PST
from conf.setting import BASE_TYPE
from conf.setting import DATADB_CONFIG
from Crawler.baseModel import BaseModel
from Crawler.fieldConfig import product
from Crawler.fieldConfig import druid_product


class ProductModel(BaseModel):
    def __init__(self):
        # 配置文件
        self.db_config = deepcopy(DATADB_CONFIG[BASE_TYPE])
        # 数据库名
        self.database = self.db_config['database']
        super(ProductModel, self).__init__(self.db_config)

        # amazon_product_data 表
        self.product_name = 'amazon_product_data'
        self.product_class = self.get_class(self.product_name)  # crud用

        # amazon_druid_product_data 表
        self.druid_name = 'amazon_druid_product_data'
        self.druid_class = self.get_class(self.druid_name)  # crud用

        # amazon_druid_product_data_bsr
        self.bsr_name = 'amazon_druid_product_data_bsr'
        self.bsr_class = self.get_class(self.bsr_name)

        # amazon_product_monitor 表
        self.monitor_name = 'amazon_product_monitor'
        self.monitor_class = self.get_class(self.monitor_name)

        # 时间相关的对象.
        self.date_fmt = '%Y%m%d'
        self.today = return_PST()
        self.old_date = self.today + timedelta(days=-3)

    # 存储逻辑
    def save_course(self, datas: dict, redisQ: object):
        # 今天pt时间string fromat: 20181111
        aday = self.today.strftime(self.date_fmt)
        # 统一用redis所在服务器的时间戳
        tm = self.get_redis_tm(redisQ)
        # 处理数据
        asin, course_data = self.handle_data(datas, tm)
        # 创建产品对象
        pro_obj = self.product_class(**(course_data.get('pro', {})))
        # 创建产品druid对象
        dru_obj = self.druid_class(**(course_data.get('dru', {})))
        # bsr data 是一个 list 需要做批量插入处理.
        bsr_list = course_data.get('bsr', [])

        # 开始存储过程
        session = self.get_session()
        # 查询druid表中今天的数据是否存在
        query_dru = session.query(self.druid_class).filter(asin=asin, aday=aday).one_or_none()
        if not query_dru:
            # 不存在则插入druid表
            dru_obj.insert()
            # 查询product表是否存在此asin(唯一约束)
            query_pro = session.query(self.product_class).filter(asin=asin)
            if query_pro:
                # 存在则update
                query_pro.update(**(course_data.get('pro', {})))
            else:
                # 不存在则insert
                pro_obj.insert()
            # bsr直接insert
            for bsr in bsr_list:
                if isinstance(bsr, dict) and bsr:
                    self.bsr_class(**bsr).insert()
            # 标记监测表的爬取时间
            session.query(self.monitor_class).filter(asin=asin).update(info_tm=tm / 1000)
        # 提交操作
        session.commit()
        # 关闭session
        session.close()

    # 操作数据总逻辑
    def handle_data(self, datas: dict, tm: int) -> 'str, dict':
        '''
        :param datas: {asin: {field: value}}
        :return:
        先清洗数据
            清洗数据分三步
            第一步先做沿用旧数据的判断与加工
            第二步筛选各表所需字段
            第三步过滤空值与空字符串
        再存储数

        '''
        asin = ''
        course_data = {}
        for k, v in datas.items():
            asin = k
            data = self.use_the_old_data(asin, v)
            data['getinfo_tm'] = tm
            # 获取所需数据
            product_data = self.filter_none_field(self.filter_field(data, product))
            course_data['pro'] = product_data
            druid_product_data = self.filter_none_field(self.filter_field(data, druid_product))
            course_data['dru'] = druid_product_data
            # bsr data 是一个列表, 需要专门处理. 插入的时候, 也要批量插入.
            bsr_data = data.get('bsr_info', [])
            for bsr in bsr_data:
                # bsr数据只需要对tm重新赋值, 并不需要做字段筛选
                if isinstance(bsr, dict):
                    bsr['tm'] = tm
            course_data['bsr'] = bsr_data
        return asin, course_data

    # 过滤字段(为空的字段不存储)
    def filter_none_field(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return {}
        for item in data:
            # 如果是空字符串或者None则直接弹出.
            if data[item] == '' or data[item] is None:
                data.pop(item)
        return data

    # 筛选所需字段
    def filter_field(self, data: dict, relevant: dict) -> dict:
        '''将对应的字段重新赋值'''
        if not isinstance(data, dict) or not isinstance(relevant, dict):
            return {}
        for relev in relevant:
            relevant[relev] = data.get(relevant[relev])
        return relevant

    # 沿用旧数据的处理逻辑
    def use_the_old_data(self, asin: str, data: dict) -> dict:
        # 参数类型检查
        if not isinstance(asin, str) or not isinstance(data, dict):
            return {}

        # 三天前的pt时间string fromat: 20181111
        old_aday = self.old_date.strftime(self.date_fmt)

        # 获取druid表中的数据(沿用历史数据).
        session = self.get_session()
        old_data = session.query(self.druid_class).filter(
            self.druid_class.asin == asin, self.druid_class.aday >= old_aday, self.druid_class.qtydt != 4). \
            order_by(desc(self.druid_class.aday)).first()
        session.close()

        if old_data:
            # 如果今天没有库存, 用前一天的数据
            if data['quantity'] == -1 and old_data.qty >= 0 and data['asin_state'] == 3:
                data['quantity'] = old_aday.qty
                # 标记一下
                data['qtydt'] = 4

            # 如果今天没有价格, 用前一天的数据.
            if data['price'] <= 0 and old_data.dpre > 0 and data['asin_state'] == 3:
                data['price'] = old_data.dpre

            # 如果今天的评论小于昨天的评论, 用昨天的评论
            if data['rc'] > 0 and data['rc'] < old_data.rc:
                data['rc'] = old_aday.rc
            '''
            如果没有 title 与 brand 会在 filter_field 那一步进行操作, 弹出该字段.
            这样update的时候, 就会忽略该字段, 以此达到沿用历史数据的目的
           '''

        # 如果没有dpre, 就用price赋值
        if data['dpre'] <= 0 and data['price'] > 0:
            data['dpre'] = data['price']

        # 如果没有cart_price 就用 price赋值
        if data['cart_price'] <= 0 and data['price'] > 0:
            data['cart_price'] = data['price']

        # 如果不可售
        if data['asin_state'] == 2:
            data['quantity'] = 0
            data['byb'] = 0
            data['qtydt'] = 5
        return data


if __name__ == '__main__':
    pass