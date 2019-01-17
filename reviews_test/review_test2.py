from parse2 import GoodsParser
import requests

url = 'https://www.amazon.com/dp/B07C1R9Q9R?th=1&psc=1'
res = requests.get(url)
html = res.text
print(res)
reviews = GoodsParser(html)._get_review_count()
print(reviews)

