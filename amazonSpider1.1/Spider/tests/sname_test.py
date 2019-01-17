from Crawler.tosellParser import TosellParser

with open('./22.html', 'r', encoding='utf8') as f:
    html = f.read()
html_list = [html]
TosellParser().tosell_parser(html_list, 'B06XCQFX94', goods_html_code=html)

