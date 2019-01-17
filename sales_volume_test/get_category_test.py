import requests
from lxml import etree

# url = 'https://www.amazon.com/dp/B01F8UIFXK?th=1&psc=1'
url = 'https://www.amazon.com/dp/B07C1R9Q9R?th=1&psc=1'
res = requests.get(url)
html = res.text
print(res)
html = etree.HTML(html)
# data = html.xpath('//ul[@class="a-unordered-list a-horizontal a-size-small"]//span[@class="a-list-item"]/a/text()')
data = html.xpath('//*[@id="bylineInfo"]/text()')
for d in data:
    print(d.strip())

