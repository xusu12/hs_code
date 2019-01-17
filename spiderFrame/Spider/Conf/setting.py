#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
sys.path.append("../../")
import re
import os

from Base import Config

# 获取配置文件配置的实例
conf = Config()

# 项目根目录
BASE_DIR = conf.base_dir
# 代码根目录
SPIDER_DIR = os.path.join(BASE_DIR, 'Spider')
# 程序数据目录
DATA_DIR = os.path.join(BASE_DIR, 'data')
# 报告文件目录
REPORT_DIR = os.path.join(BASE_DIR, 'report')
# 日志目录
LOG_DIR = os.path.join(BASE_DIR, 'log')
# 定时器目录
CRONTAB_DIR = os.path.join(BASE_DIR, 'crontabLog')
# 配置文件目录
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
# 环境变量所在目录
ENV_DIR = conf.get('main', 'env_dir')

# 太平洋时区标准城市
PST_CITY = conf.get('main', 'pst_city')

# 线程数
GOODS_T_NUM = int(conf.get('thread', 'goods_t_num'))
ANALYZER_GOODS_T_NUM = int(conf.get('thread', 'analyzer_goods_t_num'))
REVIEWS_T_NUM = int(conf.get('thread', 'reviews_t_num'))
TOSELL_T_NUM = int(conf.get('thread', 'tosell_to_num'))
KEYWORD_T_NUM = int(conf.get('thread', 'keyword_t_num'))
ANALYZER_KEYWORD_T_NUM = int(conf.get('thread', 'analyzer_keyword_t_num'))

# 进程数
DATA_P_NUM = int(conf.get('process', 'data_p_num'))
GOODS_P_NUM = int(conf.get('process', 'goods_p_num'))
REVIEWS_P_NUM = int(conf.get('process', 'reviews_p_num'))
TOSELL_P_NUM = int(conf.get('process', 'tosell_p_num'))
KEYWORD_P_NUM = int(conf.get('process', 'keyword_p_num'))

# ssl证书
proxy_verify_name = conf.get('proxy', 'proxy_verify_name')
PROXY_VERIFY = os.path.join(CONFIG_DIR, proxy_verify_name)

# get请求使用的代理
PROXY_HTTP_GET = conf.get('proxy', 'proxy_http_get')
PROXY_HTTPS_GET = conf.get('proxy', 'proxy_https_get')

# post请求使用的代理
PROXY_HTTP_POST = conf.get('proxy', 'proxy_http_inv_post')
PROXY_HTTPS_POST = conf.get('proxy', 'proxy_https_inv_post')

# 日期时间格式
data_format = '%Y-%m-%d'
data_time_format = data_format + ' ' + '%H:%M:%S'

# debug级别日志格式
LOG_TEM_DEBUG = (
'GMT+8:%(asctime)s, PID:%(process)d, TID:[%(thread)d %(threadName)s, LEV:%(levelno)s %(levelname)s, MSG:, %(message)s',
data_time_format)
# info级别日志格式
LOG_TEM_INFO = ('GMT+8:%(asctime)s, TID:%(thread)d %(threadName)s, MSG:, %(message)s', data_time_format)
# 数据入库日志格式
LOG_TEM_DB = ('GMT+8:%(asctime)s, TID:%(thread)d %(threadName)s, MSG:, %(message)s', data_time_format)
# error级别日志格式
LOG_TEM_ERROR = (
'GMT+8:%(asctime)s, PID:%(process)d, TID:%(thread)d %(threadName)s, LEV:%(levelno)s %(levelname)s, MSG:, %(message)s',
data_time_format)

develop_e_name = conf.get('env', 'develop_e_name')
test_e_name = conf.get('env', 'test_e_name')
production_e_name = conf.get('env', 'production_e_name')

# redis配置
REDIS_CONFIG = {
    develop_e_name: dict(
        host=conf.get('redis', 'dev_host'),
        port=int(conf.get('redis', 'dev_port')),
        db=int(conf.get('redis', 'dev_db')),
        max_connections=int(conf.get('redis', 'dev_max_conn')),
        # decode_responses=True
    ),
    test_e_name: dict(
        host=conf.get('redis', 'test_host'),
        port=int(conf.get('redis', 'test_port')),
        db=int(conf.get('redis', 'test_db')),
        max_connections=int(conf.get('redis', 'test_max_conn')),
    ),
    production_e_name: dict(
        host=conf.get('redis', 'pro_host'),
        port=int(conf.get('redis', 'pro_port')),
        db=int(conf.get('redis', 'pro_db')),
        max_connections=int(conf.get('redis', 'pro_max_conn')),
    )
}

# 数据库配置
DATADB_CONFIG = {
    develop_e_name: dict(
        database=conf.get('db', 'dev_database'),
        user=conf.get('db', 'dev_user'),
        password=conf.get('db', 'dev_password'),
        host=conf.get('db', 'dev_host'),
        port=conf.get('db', 'dev_port'),
    ),
    test_e_name: dict(
        database=conf.get('db', 'test_database'),
        user=conf.get('db', 'test_user'),
        password=conf.get('db', 'test_password'),
        host=conf.get('db', 'test_host'),
        port=conf.get('db', 'test_port'),
    ),
    production_e_name: dict(
        database=conf.get('db', 'pro_database'),
        user=conf.get('db', 'pro_user'),
        password=conf.get('db', 'pro_password'),
        host=conf.get('db', 'pro_host'),
        port=conf.get('db', 'pro_port'),
    )
}

BASE_TYPE_LIST = [
    develop_e_name,
    test_e_name,
    production_e_name,
]

# 获取运行环境的方法
def get_environment():
    # print(BASE_DIR, 111)
    env_file = os.path.join(CONFIG_DIR, 'environment.txt') if re.search('[Ww]in', sys.platform) \
        else os.path.join(ENV_DIR, 'environment.txt')
    # print(env_file, 3333)
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            env_str = f.readline().lstrip().strip()
            return env_str if env_str in BASE_TYPE_LIST else ''

# 程序运行环境
'''
develop     # 开发
test        # 测试
production  # 生产
'''
BASE_TYPE = get_environment() if get_environment() else develop_e_name


if __name__ == '__main__':
    print(BASE_DIR, type(BASE_DIR))
    print(DATA_DIR, type(DATA_DIR))
    print(REPORT_DIR, type(REPORT_DIR))
    print(CRONTAB_DIR, type(CRONTAB_DIR))
    print(CONFIG_DIR, type(CONFIG_DIR))
    print(ENV_DIR, type(ENV_DIR))
    print(PST_CITY, type(PST_CITY))
    print(PROXY_VERIFY, type(PROXY_VERIFY))
    print(PROXY_HTTP_GET, type(PROXY_HTTP_GET))
    print(PROXY_HTTPS_GET, type(PROXY_HTTPS_GET))
    print(PROXY_HTTP_POST, type(PROXY_HTTP_POST))
    print(PROXY_HTTPS_POST, type(PROXY_HTTPS_POST))
    print(LOG_TEM_DEBUG, type(LOG_TEM_DEBUG))
    print(LOG_TEM_INFO, type(LOG_TEM_INFO))
    print(LOG_TEM_DB, type(LOG_TEM_DB))
    print(LOG_TEM_ERROR, type(LOG_TEM_ERROR))
    print(BASE_TYPE, type(BASE_TYPE))
    print(DATADB_CONFIG, type(DATADB_CONFIG))
    print(REDIS_CONFIG, type(REDIS_CONFIG))

