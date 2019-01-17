#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import pytz
from datetime import datetime
from datetime import date, timedelta


def return_PST():
    # 设置为洛杉矶时区
    time_zone = pytz.timezone('America/Los_Angeles')
    dateNow = datetime.now(time_zone)
    return dateNow

# 获取美国时间当前的日期
t = datetime.date(return_PST())

date = t + timedelta(days=-2)
date = ''.join(str(date).split('-'))
print(date)

# shell = 'rm -rf ./{}'.format(date)
# os.system(shell)


