#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base


class BaseModel:
    '''一个Model基类'''
    # 单例模式
    obj = None
    def __new__(cls, *args, **kwargs):
        if cls.obj is None:
            cls.obj = object.__new__(cls)
            return cls.obj

    def __init__(self, config: dict):
        '''初始化数据库连接, 自动读取数据库中的表结构, 并生成相应关系对象'''
        self.table_map = automap_base()
        self.conn_url = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)s/%(database)s' % config
        self.engine = sqlalchemy.create_engine(self.conn_url)
        self.table_map.prepare(self.engine, reflect=True)

    def get_table(self, table_name: str) -> "class 'sqlalchemy.sql.schema.Table'":
        '''获取查询对象时调用, 传入表名, 表名不存在会抛出 KeyError'''
        return self.table_map.metadata.tables[table_name]

    def get_class(self, table_name: str) -> "class 'sqlalchemy.ext.automap.table_name'":
        '''获取crud对象时调用, 传入表名, 表名不存在会同时抛出 KeyError 与 AttributeError'''
        return getattr(self.table_map.classes, table_name)

    def get_session(self) -> object:
        '''获取session对象'''
        return Session(self.engine)

    def get_conn(self) -> object:
        '''获取一个数据库连接'''
        return self.engine.connect()

if __name__ == '__main__':

    DATADB_CONFIG = dict(
        database='ic_crawler',
        user='postgres',
        password='123456',
        host='192.168.13.8',
        port='15432'
    )

    conn = BaseModel(DATADB_CONFIG)
    print(conn.get_table('amazon_druid_product_data'))
    print(conn.get_class('amazon_druid_product_data'))
    print(conn.get_session())
