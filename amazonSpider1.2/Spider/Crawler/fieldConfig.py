#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
各表所需的数据, 与程序打包的数据, 字段之间的对应关系
'''

# amazon_product_data 表所需字段
product = dict(
    asin='asin',                        # 产品asin type: string
    pasin='pasin',                      # 父asin type: string
    title='title',                      # 标题 type: string
    image='image',                      # 图片 type: string
    brand='brand',                      # 品牌 type: string
    price='price',                      # 单价(折扣价) type: int
    quantity='quantity',                # 库存 type: int
    release_date='release_date',        # 发布日期 type: int
    sname='sname',                      # 卖家名称 type: string
    ts_min_price='ts_min_price',        # 最低跟卖价格 type: int
    to_sell='to_sell',                  # 跟卖数量 type: int
    byb='byb',                          # 是否黄金购物车 type: int
    bsr='bsr',                          # 销量排名 type: int
    rc='rc',                            # 评论 type: int
    rrg='rrg',                          # 评分 type: int
    r5p='r5p',                          # 五星百分比 type: int
    r4p='r4p',                          # 四星百分比 type: int
    r3p='r3p',                          # 三星百分比 type: int
    r2p='r2p',                          # 二星百分比 type: int
    r1p='r1p',                          # 一星百分比 type: int
    feature='feature',                  # 特点 type: string
    cart_price='cart_price',            # 购物车价格 type: int
    getinfo_tm='getinfo_tm',            # 数据更新时间戳(毫秒级) type: int
    category='category',                # 类别 type: string
    image_more='image_more',            # 图片组 type: string
    asin_type='asin_type',              # 产品类型 type: int
    asin_state='asin_state',            # 产品asin状态 type: int
    seller_id='seller_id',              # 卖家ID type: int
    crawler_state='crawler_state',      # 是否已爬取 type: int
    is_sync='is_sync',                   # 是否已同步 type: int
    fba='fba',                           # 是否fba type: int
)

# amazon_druid_product_data 表所需字段
druid_product = dict(
    tm='getinfo_tm',                # 数据更新时间戳(毫秒级) type: int
    asin='asin',                    # 产品asin type: string
    pasin='pasin',                  # 父asin type: string
    sn='sname',                     # 卖家名称 type: string
    pre='dpre',                     # 原价(没有时用单价) type: int
    dpre='price',                   # 折扣价(单价) type: int
    bs1='bs1',                      # 是否销量第一 type: int
    qc='qc',                        # 问答数 type: int
    rc='rc',                        # 评论数 type: int
    rrg='rrg',                      # 评分 type: int
    qty='quantity',                 # 库存 type: int
    ts='to_sell',                   # 跟卖数量 type: int
    byb='byb',                      # 是否黄金购物车 type: int
    r5p='r5p',                       # 五星百分比 type: int
    r4p='r4p',                       # 四星百分比 type: int
    r3p='r3p',                       # 三星百分比 type: int
    r2p='r2p',                       # 二星百分比 type: int
    r1p='r1p',                       # 一星百分比 type: int
    tpre='ts_min_price',            # 最低跟卖价 type: int
    bsr='bsr',                       # 销量排名 type: int
    aday='aday',                     # pt时间 '20181111' type: string
    qtydt='qtydt',                   # 库存状态 type: int
    is_limit='is_limit',            # 是否限售 type: int
)

# amazon_druid_product_data_bsr 表所需字段
druid_bsr = dict(
    tm='tm',                # 数据更新时间戳(毫秒级) type: int
    asin='asin',            # 产品asin type: string
    bsrc='bsrc',            # 销量排名的具体信息 type: string
    bsr='bsr',              # 销量排名 type: int
    aday='aday',            # pt时间 '20181111' type: string
)

# amazon_keyword_data 表所需字段
keyword = dict(
    kw='kw',                                # 关键词 type: string
    cid='cid',                              # 搜索类型 type: int
    search_num='search_num',                # 搜索结果产品数 type: int
    price_max='price_max',                  # 前50最高价 type: int
    price_min='price_min',                  # 前50最低价 type: int
    price_ave='price_ave',                  # 前50平均价 type: int
    rrg_max='rrg_max',                      # 前50最高评分 type: int
    rrg_min='rrg_min',                      # 前50最低评分 type: int
    rrg_ave='rrg_ave',                      # 前50平均评分 type: int
    rc_max='rc_max',                        # 前50最高评论 type: int
    rc_min='rc_min',                        # 前50最低评论 type: int
    rc_ave='rc_ave',                        # 前50平均评论 type: int
    date='date',                            # 采集日期 type: int
    other_state='other_state',              # 其他数据采集状态 type: int
    getinfo_tm='getinfo_tm',                # 数据更新时间 type: int
    crawler_state='crawler_state',          # 爬取状态 type: int
    is_sync='is_sync',                      # 是否已同步 type: int
)

# amazon_druid_keyword_data 表所需字段
druid_keyword = dict(
    kw='kw',                    # 产品所属关键词 type: string
    cid='cid',                  # 搜索类型 type: int
    pr='pr',                    # 产品排序 type: int
    asin='asin',                # 产品asin type: string
    title='title',              # 产品标题 type: string
    img='img',                  # 产品图片 type: string
    brand='brand',              # 产品品牌 type: string
    srn='srn',                  # 搜索结果产品数 type: int
    price='price',              # 产品价格 type: int
    rrg='rrg',                  # 评分 type: int
    rc='rc',                    # 评论 type: int
    tm='tm',                    # 数据更新时间戳 type: int
    aday='aday',                # pt时间 '20181111' type: string
    issp='issp',                # 是否广告推广 type: int
    is_sync='is_sync',          # 是否已同步 type: int
    bsr='bsr',                  # 销量排名 type: int
    fba='fba',                  # 是否fba type: int
    category='category',        # 产品类别 type: string
    is_prime='is_prime',        # 是否有prime标记 type: int
)

# amazon_product_comment 表所需字段
reviews = dict(
    asin='asin',            # 产品asin type: string
    date='date',            # 评论日期 type: int
    rrg='rrg',              # 评分 type: int
    theme='theme',          # 主题 type: string
    body='body',            # 内容 type: string
    buyer='buyer',          # 评论人 type: string
    helpful='helpful',      # 多少人觉得有帮助 type: int
)

# amazon_product_data_tosell 表所需字段
tosell = dict(
    asin='asin',                        # 产品asin type: string
    sn='sn',                            # 跟卖数量 type: int
    fba_sn='fba_sn',                    # fba跟卖数量 type: int
    plow='plow',                        # 跟卖最低价 type: int
    plows='plows',                      # 最低价跟卖的卖家 type: string
    plows_id='plows_id',                # 最低价跟卖的卖家ID type: string
    getinfo_tm='getinfo_tm',            # 数据更新时间 type: int
    sname='sname',                       # 购物车卖家 type: string
    seller_id='seller_id',               # 购物车卖家ID type: string
    crawler_state='crawler_state',       # 爬取状态 type: int
    is_sync='is_sync',                    # 是否已同步 type: int
    asin_state='asin_state',              # 产品状态 type: int
)

# amazon_product_tosell 表所需字段
druid_tosell = dict(
    asin='asin',                            # 产品asin type: string
    condition='condition',                  # 使用情况(新旧程度) type: string
    sname='sname',                          # 卖家 type: string
    stype='stype',                          # 运费信息 type: string
    price='price',                          # 跟卖价格 type: int
    demo='demo',                            # 产品描述, 包含好评率/评论数等信息(废弃) type: string
    positive='positive',                    # 好评率 type: int
    total_ratings='total_ratings',          # 评论总数 type: int
    tm='tm',                                 # 更新时间戳(秒级) type: int
    fba='fba',                               # 是否fba type: int
    seller_id='seller_id',                  # 卖家ID type: string
    reivew_count='reivew_count',            # 评分 type: int
    delivery='delivery',                    # 配送方式 type: string
    aday='aday',                             # pt时间 '20181111' type: string
    sn='sn',                                # 卖家数量 type: int
    rank='rank',                            # 跟卖排序 type: int
    srank='srank',                          # 同一个卖家之间的跟卖排序 type: int
    qty='qty',                              # 此卖家的库存 type: int
    qtydt='qtydt',                          # 库存状态 type: int
    is_limit='is_limit',                    # 是否限售 type: int
    qty_source='qty_source',                # 库存来源 type: int
    offering_id='offering_id',              # 购物车指纹 type: string
    crawler_state='crawler_state',          # 库存爬取状态 type: int
)