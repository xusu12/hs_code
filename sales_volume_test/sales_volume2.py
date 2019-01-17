'''
两天之间卖家数量有变化，只用共同卖家计算销量:
1. 昨天有的asin商品  今天没有的  忽略
2. 昨天今天都有的asin商品 今天的卖家比昨天的卖家少  那么以今天的卖家统计库存 计算销量
3. 昨天今天都有的asin商品 今天的卖家比昨天的卖家多  那么往前七天查找库存记录

如果两天的库存都是999 或者是限购的产品 那么使用BSR销量预测的数据
'''
import time
from datetime import datetime, date, timedelta
import psycopg2
from bsrSpider.conf.config import DATADB_CONFIG, BASE_TYPE

t = date.today()
# 获取今天的日期
today = str(t).replace('-', '')
# 获取昨天的日期
yesterday = str(t + timedelta(days=-1)).replace('-', '')
# 获取七天前的日期
week = str(t + timedelta(days=-7)).replace('-', '')
# 当天获取的数据的asin_seller列表
asin_seller_list = []

#  保存相同卖家的同类商品的总库存
inventory_sum = {}
#  保存相同卖家的同类商品的销量
sales_same = {}
#  保存不同卖家的同类商品的销量
sales_dif = {}


def bsr(s):
    # 使用bsr预测销量的数据  将查询的结果写入sales_dif字典中
    print('{}使用bsr预测销量'.format(s))
    sales_dif[s] = 888


def get_data():
    # 建立连接
    conn = psycopg2.connect(**DATADB_CONFIG[BASE_TYPE])
    # 建立游标
    cur = conn.cursor()
    '''
        1. 查询今天的相应字段信息 按照asin分类计算相同商家相同商品的总库存
    '''
    cur.execute(
        "select asin, seller_name, quantity, qtydt, asin_state, aday from amazon_seller_qty where aday='" + today + "'")
    asin_rows = cur.fetchall()

    # 遍历查询集  找到所有的asin和seller的组合存入asin_list
    for rows in asin_rows:
        if rows[3] == 2:
            # 如果商品的库存状态是限售  那么直接使用bsr预测销量的数据 不需要将它加入asin_seller_list表中
            print('{}商品限售'.format(rows[0]))
            bsr(rows[0])
        elif '{}_{}'.format(rows[0], rows[1]) not in asin_seller_list:
            asin_seller_list.append('{}_{}'.format(rows[0], rows[1]))

    # 按照不同的asin分类计算出相同卖家的相同asin的库存总和
    for asin_seller in asin_seller_list:
        asin = asin_seller.split('_')[0]
        seller = asin_seller.split('_')[1]
        # sum表示同一个商家、同一个产品、产品状态正常的商品库存总和
        sum = 0
        for rows in asin_rows:
            if rows[0] == asin and rows[1] == seller and rows[4] == 1:
                sum += rows[2]
        # 以asin_seller为键  保存相同卖家相同产品的库存总数据
        if sum:
            inventory_sum['{}_{}'.format(asin, seller)] = sum

    '''
        2. 根据asin和昨天的日期信息查询相应字段的信息  
           按照asin分类计算相同商家相同商品的总库存  再减去今天相同卖家的相同商品  得到销量的数据
    '''
    for asin_seller in asin_seller_list:
        asin = asin_seller.split('_')[0]
        seller = asin_seller.split('_')[1]
        cur.execute(
            "select asin, seller_name, quantity, asin_state, aday from amazon_seller_qty where aday='" + yesterday + "' and asin = '" + asin + "'")
        asin_rows = cur.fetchall()

        # sum表示同一个商家、同一个产品、产品状态正常的商品库存总和
        sum = 0
        for row in asin_rows:
            if row[0] == asin and row[1] == seller and row[3] == 1:
                sum += row[2]

        # 如果今天的库存大于昨天的库存(新增了库存数量)  那么销量就设置为0
        if sum:
            if sum < inventory_sum['{}_{}'.format(asin, seller)]:
                sales_same['{}_{}'.format(asin, seller)] = 0
            elif sum == 999 and inventory_sum['{}_{}'.format(asin, seller)] == 999:
                print('{}两天的库存都是999'.format(asin))
                bsr(asin)
            else:
                sales_same['{}_{}'.format(asin, seller)] = sum - inventory_sum['{}_{}'.format(asin, seller)]

        # 如果sum没有值  就说明同一个商品 今天有的卖家昨天没有出现  那么就往前追溯七天内的值
        else:
            print('{}_{}往前追溯七天数据'.format(asin, seller))
            cur.execute(
                "select asin, seller_name, quantity, asin_state, aday from amazon_seller_qty where aday <= '" + yesterday + "' and aday >='"+week+"' and asin =  '" + asin + "'")
            # 查找此前七天的数据  如果有 只拿最近日期的数据
            asin_rows = cur.fetchall()
            if asin_rows:
                # 如果前七天有数据
                sum = 0
                # 记录结果中最近的一个日期  统计这个日期的商品的库存
                asin_row = asin_rows[0]
                date = asin_row[4]
                print(date)
                for row in asin_rows:
                    if row[0] == asin and row[1] == seller and row[3] == 1 and row[4] == date:
                        sum += row[2]

                print('{}前七天最近一天的总库存是{}'.format(asin, sum))
                # 如果今天的库存大于昨天的库存(新增了库存数量)  那么销量就设置为0
                if sum < inventory_sum['{}_{}'.format(asin, seller)]:
                    sales_same['{}_{}'.format(asin, seller)] = 0
                elif sum == 999 and inventory_sum['{}_{}'.format(asin, seller)] == 999:
                    print('{}两天的库存都是999'.format(asin))
                    bsr(asin)
                else:
                    sales_same['{}_{}'.format(asin, seller)] = sum - inventory_sum['{}_{}'.format(asin, seller)]
            else:
                # 前七天没有数据
                print('{}前七天也没有数据'.format(asin))

    # 提交操作到数据库
    conn.commit()
    # 关闭连接
    conn.close()
    return sales_same


def save_data(sales):
    # 建立连接
    conn = psycopg2.connect(**DATADB_CONFIG[BASE_TYPE])
    # 建立游标
    cur = conn.cursor()
    # 当前时间戳
    timstamp = int(round(time.time() * 1000))
    for key, value in sales.items():
        asin = key
        sales = value
        asin_state = 1
        # 执行相关操作
        # 从amazon_product_data表中查询商品对应的价格信息
        cur.execute("select price from amazon_product_data where asin='" + asin + "'")
        # cur.execute("select price from amazon_product_data where asin='B004DIW1HK'")
        price = cur.fetchone()
        if not price:
            price = (0,)
        # 写入销量表
        cur.execute(
            "insert into amazon_sale_qty (asin, sales, asin_state, aday, tm, price) values ('" + asin + "', '" + str(
                sales) + "', '" + str(asin_state) + "', '" + today + "', '" + str(timstamp) + "', '" + str(
                price[0]) + "') ")
        # 提交操作到数据库
    conn.commit()
    # 关闭连接
    conn.close()


def run():
    sales = get_data()
    # 将相同asin的不同卖家的销量汇总在一起
    for asin_seller in asin_seller_list:
        asin = asin_seller.split('_')[0]
        s = 0
        for key, value in sales.items():
            if key.split("_")[0] == asin:
                s += value
        if s:
            sales_dif['{}'.format(asin)] = s
    print(sales_dif)
    # save_data(sales_dif)


if __name__ == '__main__':
    run()
