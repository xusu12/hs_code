lis = []
url = 'https://www.amazon.com/dp/{}?th=1&psc=1'
# url_li = []
with open('brand_data.csv', 'r') as f:
    lis = f.readlines()

k = 1
for i in lis:
    asin = i.split(',')[0]
    print(url.format(asin.strip('\n')))
    k += 1
