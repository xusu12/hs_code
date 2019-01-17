import time
from datetime import date, timedelta
import psycopg2

# 是否更新amazon_product_info中已存在的数据  0表示不更新  1表示要更新
flag = 0

# 秒级时间戳
tm = int(time.time())
# 获取当前时间戳  毫秒级
ms_tm = int(round(time.time() * 1000))
# 锚点时间戳  记录查询amazon_product_data数据库的锚点
anchor_tm = ms_tm

# 建立连接
conn = psycopg2.connect(
    database='ic_crawler',
    user='postgres',
    password='123456',
    host='192.168.13.8',
    port='15432',
)

# 建立游标
cur = conn.cursor()

# 查询amazon_druid_keyword_data表中所有的asin数据  按照asin进行分组  取出最新的日期
cur.execute(
    "select asin, max(aday) from amazon_druid_keyword_data  group by asin;")
kw_max_day_asins = cur.fetchall()

i = 0
# 逐个取出asin对应的最新日期的数据
for kw_max_day_asin in kw_max_day_asins:
    asin = kw_max_day_asin[0]
    max_aday = kw_max_day_asin[1]

    cur.execute(
        "select asin,brand,category,img,title,aday from amazon_druid_keyword_data where asin='"+asin+"' and aday='"+max_aday+"';")
    kw_data_row = cur.fetchone()
    data_dict = {'asin': kw_data_row[0], 'brand': kw_data_row[1],
                 'brand_tm': tm if kw_data_row[1] else 0,
                 'category': kw_data_row[2], 'category_tm': tm if kw_data_row[2] else 0,
                 'image': kw_data_row[3], 'image_tm': tm if kw_data_row[3] else 0,
                 'title': kw_data_row[4],
                 'title_tm': tm if kw_data_row[4] else 0, 'pasin': '',
                 'pasin_tm': 0, 'asin_type': 0,
                 'tm': 0, }

    # 查询amazon_product_info表中是否存在对应的asin的数据
    cur.execute(
        "select asin,brand,category,image,title,pasin,asin_type from public.amazon_product_info where asin='" + asin + "';")
    info_asin_row = cur.fetchone()

    # 如果有对应的asin  那就逐个对比字段信息  update
    # 如果asin对应的数据在info表中存在  进行更新操作
    if info_asin_row:
        # flag为0的时候  amazon_product_info已有的asin对应的字段就不再更新  逐个找出没有数据的字段并更新
        if not flag:
            # 如果brand字段在info表中没有而在data表中有 那么就更新这个字段
            if not info_asin_row[1] and kw_data_row[1]:
                data_dict = {'brand': kw_data_row[1], 'brand_tm': tm if kw_data_row[1] else 0}
                sql = "update public.amazon_product_info set brand=%(brand)s, brand_tm= %(brand_tm)s where asin='" + \
                      kw_data_row[0] + "'"
                cur.execute(sql, data_dict)
                print(kw_data_row)
            # 如果category字段在info表中没有而在data表中有 那么就更新这个字段
            if not info_asin_row[2] and kw_data_row[2]:
                data_dict = {'category': kw_data_row[2], 'category_tm': tm if kw_data_row[2] else 0}
                sql = "update public.amazon_product_info set category=%(category)s, category_tm=%(category_tm)s where asin='" + \
                      kw_data_row[0] + "'"
                cur.execute(sql, data_dict)
                print(kw_data_row)
            # 如果image字段在info表中没有而在data表中有 那么就更新这个字段
            if not info_asin_row[3] and kw_data_row[3]:
                data_dict = {'image': kw_data_row[3], 'image_tm': tm if kw_data_row[3] else 0}
                sql = "update public.amazon_product_info set image= %(image)s, image_tm=%(image_tm)s where asin='" + \
                      kw_data_row[0] + "'"
                cur.execute(sql, data_dict)
                print(kw_data_row)
            # 如果title字段在info表中没有而在data表中有 那么就更新这个字段
            if not info_asin_row[4] and kw_data_row[4]:
                data_dict = {'title': kw_data_row[4], 'title_tm': tm if kw_data_row[4] else 0}
                sql = "update public.amazon_product_info set title=%(title)s, title_tm=%(title_tm)s where asin='" + \
                      kw_data_row[0] + "'"
                cur.execute(sql, data_dict)
                print(kw_data_row)
        # flag不为0的时候  所有字段全部更新
        else:
            sql = "update public.amazon_product_info set brand=%(brand)s, brand_tm= %(brand_tm)s, category=%(category)s, category_tm=%(category_tm)s, image= %(image)s, image_tm=%(image_tm)s, title=%(title)s, title_tm=%(title_tm)s, pasin=%(pasin)s, pasin_tm=%(pasin_tm)s, asin_type=%(asin_type)s, tm=%(tm)s where asin=%(asin)s;"
            cur.execute(sql, data_dict)
    # 如果没有对应的asin  那就直接插入这条数据  如果某个字段没有值  那么相对应的时间戳保存0
    else:
        sql = "INSERT INTO amazon_product_info (asin, brand, brand_tm, category, category_tm, image, image_tm, title, title_tm, pasin, pasin_tm, asin_type, tm) VALUES (%(asin)s, %(brand)s,  %(brand_tm)s,  %(category)s,  %(category_tm)s,  %(image)s, %(image_tm)s,  %(title)s,  %(title_tm)s,  %(pasin)s,  %(pasin_tm)s,  %(asin_type)s,  %(tm)s)"
        cur.execute(sql, data_dict)

# 提交操作到数据库
conn.commit()
# 关闭连接
conn.close()
