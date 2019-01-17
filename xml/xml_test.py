import os
import xml.dom.minidom

from pprint import pprint
from xml_parse_class import parent_parse, child_parse


# 解析页面
def parse(file_name):
    # 打开xml文档
    doc = xml.dom.minidom.parse('./save_xml/{}'.format(file_name))

    # 获取父产品数据
    p_parse = parent_parse(doc=doc)
    data = p_parse.get_data()
    pprint(data)

    print('*' * 10)

    # 获取子产品数据
    child_data = child_parse(doc)
    pprint(child_data)


# 获取文件名
def file_name(file_dir):
    for root, dirs, files in os.walk(file_dir):
        xml_name_list = files

    i = 1
    for file in files:
        parse(file)
        print(i)
        i += 1


if __name__ == '__main__':
    file_name('./save_xml/')