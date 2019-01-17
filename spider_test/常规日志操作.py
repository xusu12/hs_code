import logging
import time
import sys
import logging.handlers

# 获取logger实例，如果参数为空则返回root logger
logger = logging.getLogger("AppName")

# 指定logger输出格式
formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
# 指定日志的最低输出级别，默认为WARN级别
logger.setLevel(logging.DEBUG)

# 文件日志
file_handler = logging.FileHandler("test.log")
file_handler.setFormatter(formatter)  # 可以通过setFormatter指定输出格式

# 控制台日志
console_handler = logging.StreamHandler(sys.stdout)
console_handler.formatter = formatter  # 也可以直接给formatter赋值

# 为logger添加的日志处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)



# 输出不同级别的log
# logger.debug('this is debug info')
# logger.info('this is information')
# logger.warn('this is warning message')
# logger.error('this is error message')
# logger.fatal('this is fatal message, it is same as logger.critical')
# logger.critical('this is critical message')

a = 11
logger.info(a)
try:
    print(jj)
except Exception as e:
    logger.error(e)

t=1537410192070
t = float(t/1000)
t = time.localtime(t)
time = time.strftime("%Y-%m-%d %H:%M:%S", t)
print(time)













# 添加TimedRotatingFileHandler到nor
# 定义一个1分钟换一次log文件的handler
# filehandler = logging.handlers.TimedRotatingFileHandler(
#     "logging_test2", 'M', 1, 0)
# # 设置后缀名称，跟strftime的格式一样
# filehandler.suffix = "%Y%m%d-%H%M.log"
# logger.addHandler(filehandler)