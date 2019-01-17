import time
from datetime import datetime
from datetime import date, timedelta

import psycopg2
import pytz

# 建立连接
conn = psycopg2.connect(
        # database='ic_crawler',
        # user='postgres',
        # password='123456',
        # host='192.168.13.8',
        # port='15432',
        database='ic_crawler_online',
        user='postgres',
        password='123456',
        host='192.168.0.149',
        port='15432'
)

def return_PST():
    # 设置为洛杉矶时区
    time_zone = pytz.timezone('America/Los_Angeles')
    dateNow = datetime.now(time_zone)
    return dateNow


data = datetime.date(return_PST())
t = str(data)
tt = str(data)+" "+"16:00:00"
timeArray = time.strptime(tt, "%Y-%m-%d %H:%M:%S")
tm = int(round(time.mktime(timeArray)*1000))
print(tm)

# 建立游标
cur = conn.cursor()
# 查询没有库存的商品的asin
cur.execute(
    "select asin,quantity from public.amazon_product_data where quantity = -1 and asin_state = 3 and getinfo_tm >='"+str(tm)+"';")
asin_rows = cur.fetchall()
with open('not_found_inventory_asin_{}.csv'.format(t), 'w') as f:
    for asin_row in asin_rows:
        f.write(asin_row[0])
        f.write('\n')


# 查询没有价格的商品的asin
cur.execute(
    "select asin from public.amazon_product_data where asin_state=3 and price <=0 and getinfo_tm >= '"+str(tm)+"';")
asin_rows = cur.fetchall()

with open('not_found_price_asin_{}.csv'.format(t), 'w') as f:
    for asin_row in asin_rows:
        f.write(asin_row[0])
        f.write('\n')

# 查询没有bsr的商品的asin
cur.execute(
    "select asin from public.amazon_product_data where asin_state!=0 and bsr <=0 and getinfo_tm >= '"+str(tm)+"';")
asin_rows = cur.fetchall()

with open('not_found_bsr_asin_{}.csv'.format(t), 'w') as f:
    for asin_row in asin_rows:
        f.write(asin_row[0])
        f.write('\n')

# 查询没有brand的商品的asin
cur.execute(
    "select asin from public.amazon_product_data where asin_state!=0 and brand = '' and getinfo_tm >= '"+str(tm)+"';")
asin_rows = cur.fetchall()

with open('not_found_brand_asin_{}.csv'.format(t), 'w') as f:
    for asin_row in asin_rows:
        f.write(asin_row[0])
        f.write('\n')

# 查询没有评论的商品的asin
cur.execute(
    "select asin from public.amazon_product_data where asin_state!=0 and rc <= 0 and getinfo_tm >= '"+str(tm)+"';")
asin_rows = cur.fetchall()

with open('not_found_rc_asin_{}.csv'.format(t), 'w') as f:
    for asin_row in asin_rows:
        f.write(asin_row[0])
        f.write('\n')

# 查询没有评分的商品的asin
cur.execute(
    "select asin from public.amazon_product_data where asin_state!=0 and rrg <= 0 and getinfo_tm >= '"+str(tm)+"';")
asin_rows = cur.fetchall()

with open('not_found_rrg_asin_{}.csv'.format(t), 'w') as f:
    for asin_row in asin_rows:
        f.write(asin_row[0])
        f.write('\n')


# 提交操作到数据库
conn.commit()
# 关闭连接
conn.close()
