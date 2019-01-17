# coding=utf-8
import functools
import xml.dom.minidom
from pprint import pprint


def check_indexoutof(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            return ''
        return result
    return wrapper

class Parser:
    def __init__(self, resp_text=None, doc=None):
        self.resp_text = resp_text
        self.doc = doc
        self.data = {}

    @check_indexoutof
    def get_xml_element(self, item):
        if self.doc.getElementsByTagName(item):
            item_value = self.doc.getElementsByTagName(item)[0].childNodes[0].data
            return item_value

    @check_indexoutof
    def get_xml_sub_element(self, pitem, citem):
        if self.doc.getElementsByTagName(pitem):
            if self.doc.getElementsByTagName(pitem)[0].getElementsByTagName(citem):
                item_value = self.doc.getElementsByTagName(pitem)[0].getElementsByTagName(citem)[0].childNodes[0].data
                return item_value


class parent_parse(Parser):
    def __init__(self, resp_text=None, doc=None):
        super(parent_parse, self).__init__(resp_text=resp_text, doc=doc)
        self.data = {}
        self.doc = doc
        self.data['asin'] = self.get_xml_element("ASIN")  # 获取asin数据
        self.data['parentAsin'] = self.get_xml_element("ParentASIN")  # 获取父asin
        self.data['brand'] = self.get_xml_element("Brand")  # 获取brand
        self.data['bsr'] = self.get_xml_element("SalesRank")  # 获取bsr
        self.data['title'] = self.get_xml_element("Title")  # 获取title
        self.data['newTosell'] = self.get_xml_element("TotalNew")  # 获取全新跟卖数量
        self.data['usedTosell'] = self.get_xml_element("TotalUsed")  # 获取二手跟卖数量
        self.data['hasReviews'] = self.get_xml_element("HasReviews")  # 判断评论
        self.data['totalVariations'] = self.get_xml_element("TotalVariations")  # 获取子产品数量
        self.data['releaseDate'] = self.get_xml_element("ReleaseDate")  # 获取发布日期
        self.data['sname'] = self.get_xml_sub_element("Merchant", "Name")  # 获取sname
        self.data['largeImage'] = self.get_xml_sub_element("LargeImage", "URL")  # 获取image
        self.data['listPrice'] = self.get_xml_sub_element("ListPrice", "FormattedPrice")  # 获取原价
        self.data['condition'] = self.get_xml_sub_element("OfferAttributes", "Condition")  # 判断Condition
        self.data['price'] = self.get_xml_sub_element("Price", "FormattedPrice")  # 获取折扣价
        self.data['lowestPrice'] = self.get_xml_sub_element("LowestNewPrice", "FormattedPrice")  # 获取最低价
        self.data['imageSetsdict'] = self.get_imageSets()  # 获取ImageSets数据
        self.data['featureList'] = self.get_feature()  # 获取描述信息
        self.data['category'] = self.get_category()  # 获取分类信息

    def get_data(self):
        return self.data

    # 获取ImageSets数据
    def get_imageSets(self):
        if self.doc.getElementsByTagName("ImageSets"):
            ImageSetsList = self.doc.getElementsByTagName("ImageSets")[0].getElementsByTagName("ImageSet")
            ImageSetsdict = {}
            n = 1
            for set in ImageSetsList:
                ImageSetsList = self.doc.getElementsByTagName("ImageSets")[0].getElementsByTagName("ImageSet")
                ImageSetsdict = {}
                n = 1
                try:
                    for set in ImageSetsList:
                        if set.getAttribute("Category"):
                            Category = set.getAttribute("Category")
                            if not Category in ImageSetsdict.keys():
                                ImageSetsdict[Category] = {
                                    'SwatchImage': self.get_xml_sub_element("SwatchImage", "URL"),
                                    'SmallImage': self.get_xml_sub_element("SmallImage", "URL"),
                                    'ThumbnailImage': self.get_xml_sub_element("ThumbnailImage", "URL"),
                                    'TinyImage': self.get_xml_sub_element("TinyImage", "URL"),
                                    'MediumImage': self.get_xml_sub_element("MediumImage", "URL"),
                                    'LargeImage': self.get_xml_sub_element("LargeImage", "URL"),
                                }
                            else:
                                Category = Category + 'x' * n
                                ImageSetsdict[Category] = {
                                    'SwatchImage': self.get_xml_sub_element("SwatchImage", "URL"),
                                    'SmallImage': self.get_xml_sub_element("SmallImage", "URL"),
                                    'ThumbnailImage': self.get_xml_sub_element("ThumbnailImage", "URL"),
                                    'TinyImage': self.get_xml_sub_element("TinyImage", "URL"),
                                    'MediumImage': self.get_xml_sub_element("MediumImage", "URL"),
                                    'LargeImage': self.get_xml_sub_element("LargeImage", "URL"),
                                }
                except Exception:
                    pass
            return ImageSetsdict

    # 获取feature
    def get_feature(self):
        Feature_List = []
        if self.doc.getElementsByTagName("ItemAttributes"):
            try:
                FeatureList = self.doc.getElementsByTagName("ItemAttributes")[0].getElementsByTagName("Feature")
                for f in FeatureList:
                    text = f.childNodes[0].data.strip()
                    # text = text.encode('utf-8')
                    text = text.replace('\n', '').replace('  ', '')
                    Feature_List.append(text)
            except Exception:
                pass
            return Feature_List

    # 获取category
    def get_category(self):
        if self.doc.getElementsByTagName("BrowseNodes"):
            category = ''
            try:
                # 获取BrowseNodes子节点的长度
                browseNode_list = self.doc.getElementsByTagName("BrowseNodes")[0].childNodes
                print('len:', len(browseNode_list))

                # 当子节点的长度大于3的时候 传参数1获取正常的分类的数据的概率最大 部分不能正常获取
                if len(browseNode_list) > 3:
                    category = self.get_category_detail(1)
                # 当子节点长度为1的时候  传参数0可以获取正常的分类信息  长度为2和3的时候  传参数0获取正确分类数据的概率最高 有部分是要传参数1才能获取正常数据
                if len(browseNode_list) == 1 or len(browseNode_list) == 2 or len(browseNode_list) == 3:
                    category = self.get_category_detail(0)

            except Exception as e:
                print('error:', e)
            return category

    def get_category_detail(self, index):
        data = ''
        ItemList = self.doc.getElementsByTagName("BrowseNodes")[0].childNodes[index].getElementsByTagName("Name")
        for item in ItemList:
            cate = item.childNodes[0].data
            if cate == 'Departments' or cate == 'Shops' or cate == 'Categories' or cate == 'Products':
                continue
            data = cate + '>' + data
        return data


class child_item_parse(Parser):
    def __init__(self, resp_text=None, doc=None):
        super(child_item_parse, self).__init__(resp_text=resp_text, doc=doc)
        self.data = {}
        self.doc = doc
        self.data['asin'] = self.get_xml_element("ASIN")  # 获取asin数据
        self.data['parentAsin'] = self.get_xml_element("ParentASIN")  # 获取父asin
        self.data['brand'] = self.get_xml_element("Brand")  # 获取brand
        self.data['title'] = self.get_xml_element("Title")  # 获取title
        self.data['price'] = self.get_xml_sub_element("Price", "FormattedPrice")  # 获取折扣价
        self.data['listPrice'] = self.get_xml_sub_element("ListPrice", "FormattedPrice")  # 获取原价
        self.data['largeImage'] = self.get_xml_sub_element("LargeImage", "URL")  # 获取image
        self.data['releaseDate'] = self.get_xml_element("ReleaseDate")  # 获取发布日期
        self.data['featureList'] = self.get_feature()  # 获取描述信息
        self.data['variationAttributes'] = self.get_attributes()  # 获取attributes信息

    def get_data(self):
        return self.data

    def get_feature(self):
        Feature_List = []
        if self.doc.getElementsByTagName("Feature"):
            FeatureList = self.doc.getElementsByTagName("Feature")
            try:
                for f in FeatureList:
                    text = f.childNodes[0].data.strip()
                    text = text.replace('\n', '').replace('  ', '')
                    Feature_List.append(text)
            except Exception as e:
                pass
            return Feature_List

    def get_attributes(self):
        # 获取变体的描述信息
        if self.doc.getElementsByTagName("VariationAttributes"):
            try:
                VariationList = self.doc.getElementsByTagName("VariationAttributes")[0].getElementsByTagName(
                    "VariationAttribute")
                Attributes = {}
                for item in VariationList:
                    name = item.getElementsByTagName("Name")[0].childNodes[0].data
                    value = item.getElementsByTagName("Value")[0].childNodes[0].data
                    Attributes[name] = value
            except Exception:
                pass

            return Attributes


def child_parse(doc):
    item_product_dict = {}
    # 子产品
    if doc.getElementsByTagName("Variations"):
        try:
            ItemList = doc.getElementsByTagName("Variations")[0].getElementsByTagName("Item")
            for item in ItemList:
                child_p = child_item_parse(doc=item)
                item_data = child_p.get_data()
                item_product_dict[item_data['asin']] = item_data
        except Exception as e:
            print(e)

        return item_product_dict


if __name__ == '__main__':
    from pprint import pprint

    # 打开xml文档
    # doc = xml.dom.minidom.parse('test1.xml')
    doc = xml.dom.minidom.parse('B0748284L520181113095954.xml')

    # 获取父产品数据
    p_parse = parent_parse(doc=doc)
    data = p_parse.get_data()
    pprint(data)

    print('*' * 10)

    # 获取子产品数据
    child_data = child_parse(doc)
    pprint(child_data)
