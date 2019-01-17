import time
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

tm = int(time.time())
# 建立游标
cur = conn.cursor()
# 查询没有库存的商品的asin
cur.execute(
    "select asin,brand,image,title,pasin,asin_type from public.amazon_product_data where title!='' and brand not like '%jpg' and brand!='' and length(title) < 255 limit 1000;")
asin_rows = cur.fetchall()

for asin_row in asin_rows:
    print(asin_row)
    data_dict = {'asin': asin_row[0], 'brand': asin_row[1], 'brand_tm': tm, 'category': '', 'category_tm': tm,
                 'image': asin_row[2], 'image_tm': tm, 'title': asin_row[3], 'title_tm': tm, 'pasin': asin_row[4],
                 'pasin_tm': tm, 'asin_type': asin_row[5], 'tm': tm, }
    sql = "INSERT INTO amazon_product_info (asin, brand, brand_tm, category, category_tm, image, image_tm, title, title_tm, pasin, pasin_tm, asin_type, tm) VALUES (%(asin)s, %(brand)s,  %(brand_tm)s,  %(category)s,  %(category_tm)s,  %(image)s, %(image_tm)s,  %(title)s,  %(title_tm)s,  %(pasin)s,  %(pasin_tm)s,  %(asin_type)s,  %(tm)s)"
    cur.execute(sql, data_dict)
    # cur.execute(
    #     "INSERT INTO amazon_product_info (asin, brand, brand_tm, category, category_tm, image, image_tm, title, title_tm, pasin, pasin_tm, asin_type, tm) VALUES ('" +
    #     asin_row[0] + "', '" + asin_row[1] + "', '" + str(tm) + "', 'wahaha',  '" + str(tm) + "', '" + asin_row[
    #         2] + "',  '" + str(tm) + "', '" + asin_row[3] + "',  '" + str(tm) + "', '" + asin_row[4] + "',  '" + str(
    #         tm) + "', '" + str(asin_row[5]) + "',  '" + str(tm) + "');")

# 提交操作到数据库
conn.commit()
# 关闭连接
conn.close()
