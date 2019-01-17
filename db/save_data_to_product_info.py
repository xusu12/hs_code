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

while True:
        # 查询amazon_product_data表中商品的asin 每次查询1000条数据  获取时间戳  根据时间戳排序  记录最小时间戳  下次查询的时候在这个时间戳之前查询
        cur.execute(
            "select asin,brand,category,image,title,pasin,asin_type, getinfo_tm from public.amazon_product_data where length(title)< 255 and getinfo_tm<'" + str(
                anchor_tm) + "' order by getinfo_tm desc limit 1000;")
        product_data_rows = cur.fetchall()

        if not product_data_rows:
            break

        # 逐个取出asin  去amazon_product_info表中查对应的数据
        for product_data_row in product_data_rows:
            product_data_asin = product_data_row[0]
            getinfo_tm = product_data_row[7]

            data_dict = {'asin': product_data_row[0], 'brand': product_data_row[1],
                         'brand_tm': tm if product_data_row[1] else 0,
                         'category': product_data_row[2], 'category_tm': tm if product_data_row[2] else 0,
                         'image': product_data_row[3], 'image_tm': tm if product_data_row[3] else 0,
                         'title': product_data_row[4],
                         'title_tm': tm if product_data_row[4] else 0, 'pasin': product_data_row[5],
                         'pasin_tm': tm if product_data_row[5] else 0, 'asin_type': product_data_row[6],
                         'tm': tm if product_data_row[6] else 0, }

            # 查询amazon_product_info表中是否存在对应的asin的数据
            cur.execute(
                "select asin,brand,category,image,title,pasin,asin_type from public.amazon_product_info where asin='" + product_data_asin + "';")
            info_asin_row = cur.fetchone()
            # 如果有对应的asin  那就逐个对比字段信息  update

            # 如果asin对应的数据在info表中存在  进行更新操作
            if info_asin_row:
                # flag为0的时候  amazon_product_info已有的asin对应的字段就不再更新  逐个找出没有数据的字段并更新
                if not flag:
                    # 如果brand字段在info表中没有而在data表中有 那么就更新这个字段
                    if not info_asin_row[1] and product_data_row[1]:
                        data_dict = {'brand': product_data_row[1], 'brand_tm': tm if product_data_row[1] else 0}
                        sql = "update public.amazon_product_info set brand=%(brand)s, brand_tm= %(brand_tm)s where asin='" + \
                              product_data_row[0] + "'"
                        cur.execute(sql, data_dict)
                        print(product_data_row)
                    # 如果category字段在info表中没有而在data表中有 那么就更新这个字段
                    if not info_asin_row[2] and product_data_row[2]:
                        data_dict = {'category': product_data_row[2], 'category_tm': tm if product_data_row[2] else 0}
                        sql = "update public.amazon_product_info set category=%(category)s, category_tm=%(category_tm)s where asin='" + \
                              product_data_row[0] + "'"
                        cur.execute(sql, data_dict)
                        print(product_data_row)
                    # 如果image字段在info表中没有而在data表中有 那么就更新这个字段
                    if not info_asin_row[3] and product_data_row[3]:
                        data_dict = {'image': product_data_row[3], 'image_tm': tm if product_data_row[3] else 0}
                        sql = "update public.amazon_product_info set image= %(image)s, image_tm=%(image_tm)s where asin='" + \
                              product_data_row[0] + "'"
                        cur.execute(sql, data_dict)
                        print(product_data_row)
                    # 如果title字段在info表中没有而在data表中有 那么就更新这个字段
                    if not info_asin_row[4] and product_data_row[4]:
                        data_dict = {'title': product_data_row[4], 'title_tm': tm if product_data_row[4] else 0}
                        sql = "update public.amazon_product_info set title=%(title)s, title_tm=%(title_tm)s where asin='" + \
                              product_data_row[0] + "'"
                        cur.execute(sql, data_dict)
                        print(product_data_row)
                    # 如果pasin字段在info表中没有而在data表中有 那么就更新这个字段
                    if not info_asin_row[5] and product_data_row[5]:
                        data_dict = {'pasin': product_data_row[5], 'pasin_tm': tm if product_data_row[5] else 0}
                        sql = "update public.amazon_product_info set pasin=%(pasin)s, pasin_tm=%(pasin_tm)s where asin='" + \
                              product_data_row[0] + "'"
                        cur.execute(sql, data_dict)
                        print(product_data_row)
                # flag不为0的时候  所有字段全部更新
                else:
                    sql = "update public.amazon_product_info set brand=%(brand)s, brand_tm= %(brand_tm)s, category=%(category)s, category_tm=%(category_tm)s, image= %(image)s, image_tm=%(image_tm)s, title=%(title)s, title_tm=%(title_tm)s, pasin=%(pasin)s, pasin_tm=%(pasin_tm)s, asin_type=%(asin_type)s, tm=%(tm)s where asin=%(asin)s;"
                    cur.execute(sql, data_dict)
            # 如果没有对应的asin  那就直接插入这条数据  如果某个字段没有值  那么相对应的时间戳保存0
            else:
                sql = "INSERT INTO amazon_product_info (asin, brand, brand_tm, category, category_tm, image, image_tm, title, title_tm, pasin, pasin_tm, asin_type, tm) VALUES (%(asin)s, %(brand)s,  %(brand_tm)s,  %(category)s,  %(category_tm)s,  %(image)s, %(image_tm)s,  %(title)s,  %(title_tm)s,  %(pasin)s,  %(pasin_tm)s,  %(asin_type)s,  %(tm)s)"
                cur.execute(sql, data_dict)

        # 最后一个查询结果的时间戳  保存到时间戳锚点
        anchor_tm = product_data_row[7]

# 提交操作到数据库
conn.commit()
# 关闭连接
conn.close()
