with open('not_found_grade_asin_2018-10-22.csv', 'r', encoding='utf8') as f:
    grade_asins = f.readlines()

with open('not_found_review_asin_2018-10-22.csv', 'r', encoding='utf8') as f:
    review_asins = f.readlines()

url = 'https://www.amazon.com/dp/{}?th=1&psc=1'
i = 0
for asin in grade_asins:
    if asin not in review_asins:
        i += 1
        asin = asin.strip()
        print(i, asin, url.format(asin))
