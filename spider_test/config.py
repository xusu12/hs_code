import os
BASE_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, 'log')
BASE_TYPE = 'development'
# print(LOG_DIR)
LOG_TEM_DEBUG = ('GMT+8:%(asctime)s, PID:%(process)d, TID:[%(thread)d %(threadName)s, LEV:%(levelno)s %(levelname)s, MSG:, %(message)s','%Y-%m-%d %H:%M:%S')
LOG_TEM_INFO = ('GMT+8:%(asctime)s, TID:%(thread)d %(threadName)s, MSG:, %(message)s', '%Y-%m-%d %H:%M:%S')
LOG_TEM_DB = ('GMT+8:%(asctime)s, TID:%(thread)d %(threadName)s, MSG:, %(message)s', '%Y-%m-%d %H:%M:%S')
LOG_TEM_ERROR = ('GMT+8:%(asctime)s, PID:%(process)d, TID:%(thread)d %(threadName)s, LEV:%(levelno)s %(levelname)s, MSG:, %(message)s', '%Y-%m-%d %H:%M:%S')