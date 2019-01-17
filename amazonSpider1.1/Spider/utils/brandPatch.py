import sys
from lxml import etree

sys.path.append("../")
import requests
import json
from Crawler.BaseCrawler import BaseCrawler
from conf.setting import GET_ASIN_DATA_API
from utils.util import Logger, UaPond, GetRedis, UrlQueue
from Crawler.goodsParser import GoodsParser
from Crawler.Downloader import get_html_useRequest, get_product
from functools import wraps

# 以当前文件的名称作为日志文件的名称　sys.argv[0]是获取当前模块的名字
log_name = sys.argv[0].split('/')[-1].split('.')[0]
debug_log = Logger(log_name=log_name)


def get_data_from_db(sql, asin=None, data=None):
    myRedis = GetRedis().return_redis(debug_log)
    # 先从redis的product_info_asin中获取品牌数据
    print(asin)
    brand = myRedis.hget('product_info_asin', 'product_info_{}'.format(asin))
    print(brand)
    if brand:
        return brand
    print(2222)
    urlQ = UrlQueue(myRedis, debug_log)
    if type(data) is dict:
        result = urlQ.retrieve_asin(sql, data)
    else:
        result = urlQ.retrieve_asin(sql)
    return result


def get_data_from_api(api_url):
    data = requests.get(api_url, verify=False)
    data_dict = json.loads(data.text)
    return data_dict


def get_data_from_requests(url):
    html_code, cookie, is_error = get_product(url=url)
    return html_code


# 通过查询数据库获取品牌信息
def get_brand_from_db(asin):
    # 获取品牌信息  先从redis缓存中获取数据  如果没有  再查postgresql数据库
    str_brand = lambda lst: [x[0] for x in lst if type(x) is tuple and len(x) > 0]
    # 查询数据库的sql语句
    # sql = "select brand from public.amazon_product_info where asin='%s'" % (asin)
    sql = "select brand from public.amazon_product_data where asin='%s'" % (asin)
    print(sql)
    brand = str_brand(get_data_from_db(sql, asin=asin))
    return brand


# 就通过api接口获取品牌信息
def get_brand_from_api(asin):
    brand = ''
    api_url = GET_ASIN_DATA_API.format(asin)
    data_dict = get_data_from_api(api_url)
    if type(data_dict) is dict:
        data = data_dict.get('data', {})
        # TODO 将数据保存到redis中  以product_info_asin为键  hash格式
        myRedis = GetRedis().return_redis(debug_log)
        myRedis.hset('product_info_asin', 'product_info_{}'.format(asin), data)
        print(data)
        brand = data.get('brand', '')
    return brand


# 通过商品解析类中的方法获取商品的品牌信息
def get_brand_from_parser(asin):
    # 根据asin获取url
    url, refer = BaseCrawler.make_url(asin)
    # 调用下载器方法获取页面数据
    html_code = get_data_from_requests(url)
    # 调用商品解析的方法获取页面的品牌信息
    print(222)
    brand = GoodsParser(html_code)._get_brand()
    return brand


def get_brand(asin):
    # 1. 通过查询数据库获取品牌信息
    # TODO 查询数据库
    brand = ''
    brand = get_brand_from_db(asin)

    # 2. 如果数据库中未能获取品牌信息　就通过api接口获取品牌信息
    if not brand:
        brand = get_brand_from_api(asin)

        # 3. 如果通过API未能获取品牌信息 就通过商品解析类中的方法获取商品的品牌信息
        if not brand:
            brand = get_brand_from_parser(asin)
    return brand


def get_category(asin):
    category = ''
    # 根据asin获取url
    url, refer = BaseCrawler.make_url(asin)
    # 调用下载器方法获取页面数据
    html_code = get_data_from_requests(url)
    html = etree.HTML(html_code)
    data = html.xpath('//*[@id="bylineInfo"]/text()')
    print(data)
    return data[0].strip()


def field_patch(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        # 运行被装饰方法　　获取返回数据
        data_dict = func(*args, **kwargs)

        # 如果数据为空　直接返回
        if not data_dict:
            return data_dict

        # 返回数据的字典
        result_dict = {}
        data_list = []

        # result_dict拆包
        for key, value in data_dict.items():
            kw = key
            keyword_data_dict = value[0]
            keyword_druid_data_list = value[1]
            # 遍历获取列表中的每一条数据　判断brand是否为空　如果是　就重新获取brand数据写入列表
            for data in keyword_druid_data_list:
                if not data['brand']:
                    data['brand'] = get_brand(data['asin'])
                if not data['category']:
                    data['category'] = get_category(data['asin'])
                # 将更新后的每条数据添加进新的列表
                data_list.append(data)
            result_dict[kw] = (keyword_data_dict, data_list)
        return result_dict

    return wrap


if __name__ == '__main__':
    asins = [
        # 'B00001YVH0',  # 接口中有
        # 'B018TDACOS',  # 接口中有
        'B0757MWSKK'  # 数据库中有
    ]
    for asin in asins:
        # category = get_category(asin)
        # print('分类信息是：', category)
        brand = get_brand(asin)
        print('品牌信息是：', brand)
