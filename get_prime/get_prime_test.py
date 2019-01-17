from lxml import etree
from Crawler.keywordParser import KwParser


class Parser(KwParser):
    def get_prime(self):
        pass


if __name__ == '__main__':
    with open('./2.html', 'r', encoding='utf8') as f:
        html_code = f.read()
    pa = Parser()
    dic = pa.kw_parser([html_code], '', 0, not_match=True)
    print(dic)
    index = 0
    for data in dic.get('')[1]:

        if data['prime']:
            print(data['title'])
            index += 1
    print(index)
