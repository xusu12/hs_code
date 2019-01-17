import time
import csv
from datetime import date, timedelta

import psycopg2

# 建立连接
conn = psycopg2.connect(
    database='ic_crawler',
    user='postgres',
    password='123456',
    host='192.168.13.8',
    port='15432',
)

cur = conn.cursor()
# 查询没有库存的商品的asin
update_sql = "INSERT INTO public.amazon_product_data_tosell(asin, sn, fba_sn, plow, plows,\
plows_id, getinfo_tm, sname, seller_id, crawler_state) VALUES (%(asin)s, %(sn)s, %(fba_sn)s, %(plow)s, %(plows)s,\
%(plows_id)s, %(getinfo_tm)s, %(sname)s, %(seller_id)s, 1);"
data_dict = {'asin': 'B01F0QQN8Q',
                                     'fba_sn': 1,
                                     'getinfo_tm': 1542018763364,
                                     'plow': 1,
                                     'plows': 'largeshop',
                                     'plows_id': 'df',
                                     'seller_id': 'A1XEMYOCVN4TN8',
                                     'sn': 1,
                                     'sname': 'Gemschest'}
cur.execute(update_sql, data_dict)
asin_rows = cur.fetchall()
print(asin_rows)

# 提交操作到数据库
conn.commit()
# 关闭连接
conn.close()
