from Crawler.goodsParser import GoodsParser

goods = GoodsParser()
with open('0.html', 'r', encoding='utf8') as f:
    html = f.read()
goods.parser_goods(html, 'the_asin', '')
count = goods._get_review_count(html_code=html)
code = goods._get_review_rating(html_code=html)
print(count)
print(code)