#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
sys.path.append("../../")

from items import ProductItem


def start():
    import glob
    import lxml.etree as etree
    file_list = glob.glob('../tests/*.html')
    parmas = {}
    result = []
    for file_name in file_list:
        product = ProductItem()
        with open(file_name, 'r', encoding='utf-8') as f:
            html = f.read()
        parmas['html_code'] = html
        parmas['xpath_obj'] = etree.HTML(html)
        product(parmas)
        result.append(product.__dict__)
    return result


if __name__ == '__main__':
    import time
    time_now = lambda: time.time()
    time1 = time_now()
    print(start())
    print(time_now() - time1)