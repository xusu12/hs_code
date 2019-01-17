import time
from datetime import datetime, date, timedelta
import psycopg2
from bsrSpider.conf.config import DATADB_CONFIG, BASE_TYPE

t = date.today()
# 获取今天的日期
today = str(t).replace('-', '')
# 获取昨天的日期
yesterday = str(t + timedelta(days=-1)).replace('-', '')
# 当天获取的数据的asin列表
asin_list = []
# 当天获取的数据的商家的列表
seller_list = []
#  保存相同卖家的同类商品的总库存
inventory_sum = {}
#  保存相同卖家的同类商品的销量
sales_same = {}
#  保存不同卖家的同类商品的销量
sales_dif = {}


def get_data():
    # 建立连接
    conn = psycopg2.connect(**DATADB_CONFIG[BASE_TYPE])
    # 建立游标
    cur = conn.cursor()
    '''
        1. 查询今天的相应字段信息 按照asin分类计算相同商家相同商品的总库存
    '''
    cur.execute(
        "select asin, seller_name, price, quantity, asin_state, aday from amazon_seller_qty where aday='" + today + "'")
    asin_rows = cur.fetchall()

    # 遍历查询集  找到所有的asin信息存入asin_list
    for rows in asin_rows:
        if rows[0] not in asin_list:
            asin_list.append(rows[0])
        if rows[1] not in seller_list:
            seller_list.append(rows[1])

    # 按照不同的asin分类计算出相同卖家的相同asin的库存总和
    for asin in asin_list:
        for seller in seller_list:
            # sum表示同一个商家、同一个产品、产品状态正常的商品库存总和
            sum = 0
            for rows in asin_rows:
                if rows[0] == asin and rows[1] == seller and rows[4] == 1:
                    sum += rows[3]
            # 以asin_seller为键  保存相同卖家相同产品的库存总数据
            if sum:
                inventory_sum['{}_{}'.format(asin, seller)] = sum

    # print(inventory_sum)
    # print(asin_list)
    # print(seller_list)

    '''
        2. 根据asin和昨天的日期信息查询相应字段的信息  
           按照asin分类计算相同商家相同商品的总库存  再减去今天相同卖家的相同商品  得到销量的数据
    '''
    for asin in asin_list:
        cur.execute(
            "select asin, seller_name, price, quantity, asin_state, aday from amazon_seller_qty where aday='" + yesterday + "' and asin = '" + asin + "'")
        asin_rows = cur.fetchall()
        for seller in seller_list:
            # sum表示同一个商家、同一个产品、产品状态正常的商品库存总和
            sum = 0
            for row in asin_rows:
                if row[0] == asin and row[1] == seller and rows[4] == 1:
                    sum += row[3]
            if sum:
                # # 如果今天的库存大于昨天的库存(新增了库存数量)  那么销量就设置为0
                # if sum < inventory_sum['{}_{}'.format(asin, seller)]:
                #     sales_same['{}_{}'.format(asin, seller)] = 0
                # elif sum == 999 and inventory_sum['{}_{}'.format(asin, seller)] == 999:
                #     print('{}两天的库存都是999'.format(asin))
                # else:
                    sales_same['{}_{}'.format(asin, seller)] = sum - inventory_sum['{}_{}'.format(asin, seller)]

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
        cur.execute(
            "insert into amazon_sale_qty (asin, sales, asin_state, aday, tm, price) values ('" + asin + "', '" + str(
                sales) + "', '" + str(asin_state) + "', '" + today + "', '" + str(timstamp) + "', '" + str(12) + "') ")
        # 提交操作到数据库
    conn.commit()
    # 关闭连接
    conn.close()


def run():
    sales = get_data()
    # 将相同asin的不同卖家的销量汇总在一起
    for asin in asin_list:
        s = 0
        for key, value in sales.items():
            if key.split("_")[0] == asin:
                s += value
        sales_dif['{}'.format(asin)] = s
    print(sales_dif)
    save_data(sales_dif)


if __name__ == '__main__':
    run()
