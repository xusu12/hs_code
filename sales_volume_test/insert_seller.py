import psycopg2
from bsrSpider.conf.config import DATADB_CONFIG, BASE_TYPE
# 建立连接
conn = psycopg2.connect(**DATADB_CONFIG[BASE_TYPE])
# 建立游标
cur = conn.cursor()
# 执行相关操作
cur.execute("INSERT INTO amazon_seller_qty (sid, asin, seller_id, seller_name, seller_sum, fba, price, quantity, qtydt, asin_state, condition, stype, positive, total_ratings, reivew_count, delivery, aday, offering_id, crawler_state, rank, seller_rank, qty_source, tm) VALUES ('', 'C7602JKSKY', 'OPTKPN01DIY8K', 'aili', 1, 1, 1280, 300, 0, 1, '', '', 83, 113, 43, '', '20180930', 'wxYPF3BbXnTeY9eeHdKzd8rX%2FWQsNav7P%2BZYuOqeT41mM84u3bqFX2YDrkIZVBUaa9tJSLCmFarbfAFX1EIj6%2FURXMTXkhjw%2FcS8JoxtmofFi3pwZ8uTFJ%2BRbTZUw6sUKV4ZH3CksXtrQXiB27hMpGrtOK6o17ob', 0, 0, 0, 0, 1536661143276)")
# 提交操作到数据库
conn.commit()
# 关闭连接
conn.close()