import re
str = '<span class="a-size-base" id="acrCustomerReviewText">3,854 customer reviews</span>'
review = re.findall(r'<.*>(.*) customer reviews<.*>', str)
print(review)
