import csv
import psycopg2

# 建立连接
conn = psycopg2.connect(
        database='ic_crawler_online',
        user='postgres',
        password='123456',
        host='192.168.0.149',
        port='15432'
)

# 建立游标
cur = conn.cursor()
# 查询没有库存的商品的asin
cur.execute(
    "select kw,count(kw) from public.amazon_druid_keyword_data where aday='20181029' and brand='' group by kw;")
asin_rows = cur.fetchall()
with open('brand_is_none.csv', 'w') as f:
    # 设定写入模式
    csv_write = csv.writer(f, dialect='excel')
    for asin_row in asin_rows:
        csv_write.writerow(asin_row)
        f.write('\n')

# 提交操作到数据库
conn.commit()
# 关闭连接
conn.close()