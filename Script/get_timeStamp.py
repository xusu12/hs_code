import time
from datetime import datetime, date, timedelta

t = date.today()
print(t)  # 2018-10-17
# 获取今天的日期
today = str(t).replace('-', '')
# 获取昨天的日期
yesterday = str(t + timedelta(days=-1)).replace('-', '')
print(yesterday)  # 20181016

# 获取当前时间戳  毫秒级
tm = int(round(time.time() * 1000))
print(tm)

# 将毫秒级时间戳转换成日期格式
t = 1539943882
time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))  # 参数是秒级时间戳
print(time)  # 2018-09-19 17:25:57
