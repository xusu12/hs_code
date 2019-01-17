import time
import csv
from datetime import date, timedelta

import psycopg2

# 建立连接
conn = psycopg2.connect(
        database='ic_crawler_online',
        user='postgres',
        password='123456',
        host='192.168.0.149',
        port='15432'
)

cur = conn.cursor()
# 查询没有库存的商品的asin
cur.execute(
    "select asin, aday, qty, qtydt from public.amazon_druid_product_data where qtydt=4 and aday='20181022';")
asin_rows = cur.fetchall()
print(asin_rows)
with open('inventory_data.csv', 'w') as f:
     #设定写入模式
    csv_write = csv.writer(f,dialect='excel')
    for asin_row in asin_rows:
        csv_write.writerow(asin_row)
        f.write('\n')


# 提交操作到数据库
conn.commit()
# 关闭连接
conn.close()
