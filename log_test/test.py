import json
from conf.downloads import get_use_requests

params = {'url': 'https://junglescoutpro.herokuapp.com/api/v1/sales_estimator?rank=1&category=Appliances&store=us'}
response =get_use_requests(params)

print(json.loads(response.text))