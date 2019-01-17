import time
from datetime import datetime
from utils.util import return_PST


def get_the_time():
    # 日期格式
    date_str = '%Y%m%d'
    # 时间格式
    time_str = '%Y%m%d%H%M%S'

    # 当天的日期对象
    the_day = datetime.now()
    the_hour = the_day.hour
    pstNow = return_PST()
    pstHour = pstNow.hour
    # print(1.1, the_day)
    # 当天日期字符串
    date_str = the_day.strftime(date_str)
    # 当天15点整字符串
    the_day_str = '%s150000' % (date_str)
    # 当天15点的时间对象
    time_day = time.strptime(the_day_str, time_str)
    # print(1, time_day)

    the_time = time.mktime(time_day)
    # 当天15点时间戳
    the_date_time = the_time
    # 昨天15点时间戳
    old_date_time = the_date_time - 86400

    # 如果过了太平洋时间0点了, 需要另外计算.
    if 10 >= pstHour >= 0 and 15 <= the_hour <= 23:
        the_date_time = the_time + 86400
        old_date_time = the_time

    return the_date_time, old_date_time

print(get_the_time())