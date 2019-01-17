from parse import GoodsParser
import requests

url = 'https://www.amazon.com/dp/B01KMWCNBY?th=1&psc=1'
res = requests.get(url, verify=False)
print(res)
html = res.text
GoodsParser().parser_goods(html, '', 0, '', 0, '', )

