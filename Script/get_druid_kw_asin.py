import time
import csv
from datetime import datetime
from datetime import date, timedelta
import pytz
import psycopg2


def return_PST():
    # 设置为洛杉矶时区
    time_zone = pytz.timezone('America/Los_Angeles')
    dateNow = datetime.now(time_zone)
    return dateNow


asin_list = []
today = datetime.date(return_PST())
i = 0

# 建立连接
conn = psycopg2.connect(
    database='ic_crawler_online',
    user='postgres',
    password='123456',
    host='192.168.0.149',
    port='15432'
)
cur = conn.cursor()

for i in range(1, 2):
    data = today + timedelta(days=-i)
    data = ''.join(str(data).split('-'))
    print(data)
    # 查询没有库存的商品的asin
    cur.execute(
        "select asin from public.amazon_druid_keyword_data where aday='" + data + "' group by asin;")
    asin_rows = cur.fetchall()

    with open('druid_kw_asin_{}.csv'.format(data), 'w') as f:
        # 设定写入模式
        csv_write = csv.writer(f, dialect='excel')
        for asin_row in asin_rows:
            csv_write.writerow(asin_row)

# 提交操作到数据库
conn.commit()
# 关闭连接
conn.close()
