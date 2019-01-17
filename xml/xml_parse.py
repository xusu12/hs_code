# coding=utf-8
import xml.dom.minidom
from pprint import pprint


def parent_parse(doc):
    data = {
        'asin': '',
        'parentAsin': '',
        'largeImage': '',
        'imageSetsdict': '',
        'featureList': '',
        'brand': '',
        'bsr': '',
        'title': '',
        'newTosell': '',
        'usedTosell': '',
        'listPrice': '',
        'price': '',
        'lowestPrice': '',
        'category': '',
        'hasReviews': '',
        'totalVariations': '',
        'releaseDate': '',
        'sname': '',
        'condition': '',
    }

    # 获取asin数据
    if doc.getElementsByTagName("ASIN"):
        asin = doc.getElementsByTagName("ASIN")[0].childNodes[0].data
        data['asin'] = asin

    # 获取父asin
    if doc.getElementsByTagName("ParentASIN"):
        parentAsin = doc.getElementsByTagName("ParentASIN")[0].childNodes[0].data
        data['parentAsin'] = parentAsin

    # 获取image
    if doc.getElementsByTagName("LargeImage"):
        if doc.getElementsByTagName("LargeImage")[0].getElementsByTagName("URL"):
            LargeImage = doc.getElementsByTagName("LargeImage")[0].getElementsByTagName("URL")[0].childNodes[0].data
            data['largeImage'] = LargeImage

    # 获取ImageSets数据
    if doc.getElementsByTagName("ImageSets"):
        if doc.getElementsByTagName("ImageSets")[0].getElementsByTagName("ImageSet"):
            ImageSetsList = doc.getElementsByTagName("ImageSets")[0].getElementsByTagName("ImageSet")
            ImageSetsdict = {}
            n = 1
            try:
                for set in ImageSetsList:
                    if set.getAttribute("Category"):
                        Category = set.getAttribute("Category")
                        if not Category in ImageSetsdict.keys():
                            ImageSetsdict[Category] = {
                                'SwatchImage': set.getElementsByTagName("SwatchImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                                'SmallImage': set.getElementsByTagName("SmallImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                                'ThumbnailImage':
                                    set.getElementsByTagName("ThumbnailImage")[0].getElementsByTagName("URL")[0].childNodes[
                                        0].data,
                                'TinyImage': set.getElementsByTagName("TinyImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                                'MediumImage': set.getElementsByTagName("MediumImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                                'LargeImage': set.getElementsByTagName("LargeImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                            }
                        else:
                            Category = Category + 'x' * n
                            ImageSetsdict[Category] = {
                                'SwatchImage': set.getElementsByTagName("SwatchImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                                'SmallImage': set.getElementsByTagName("SmallImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                                'ThumbnailImage':
                                    set.getElementsByTagName("ThumbnailImage")[0].getElementsByTagName("URL")[0].childNodes[
                                        0].data,
                                'TinyImage': set.getElementsByTagName("TinyImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                                'MediumImage': set.getElementsByTagName("MediumImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                                'LargeImage': set.getElementsByTagName("LargeImage")[0].getElementsByTagName("URL")[0].childNodes[
                                    0].data,
                            }
            except Exception:
                pass
            data['imageSetsdict'] = ImageSetsdict

    # 获取feature
    Feature_List = []
    if doc.getElementsByTagName("ItemAttributes"):
        try:
            FeatureList = doc.getElementsByTagName("ItemAttributes")[0].getElementsByTagName("Feature")
            for f in FeatureList:
                text = f.childNodes[0].data.strip()
                # text = text.encode('utf-8')
                text = text.replace('\n', '').replace('  ', '')
                Feature_List.append(text)
        except Exception:
            pass

        data['featureList'] = Feature_List

    # 获取brand
    if doc.getElementsByTagName("Brand"):
        brand = doc.getElementsByTagName("Brand")[0].childNodes[0].data
        data['brand'] = brand

    # 获取bsr
    if doc.getElementsByTagName("SalesRank"):
        bsr = doc.getElementsByTagName("SalesRank")[0].childNodes[0].data
        data['bsr'] = bsr


    # 获取sname
    if doc.getElementsByTagName("Merchant"):
        if doc.getElementsByTagName("Merchant")[0].getElementsByTagName("Name"):
            sname = doc.getElementsByTagName("Merchant")[0].getElementsByTagName("Name")[0].childNodes[0].data
            data['sname'] = sname

    # 获取全新跟卖数量
    if doc.getElementsByTagName("TotalNew"):
        new_tosell = doc.getElementsByTagName("TotalNew")[0].childNodes[0].data
        data['newTosell'] = new_tosell

    # 获取二手跟卖数量
    if doc.getElementsByTagName("TotalUsed"):
        used_tosell = doc.getElementsByTagName("TotalUsed")[0].childNodes[0].data
        data['usedTosell'] = used_tosell

    # 获取原价
    if doc.getElementsByTagName("ListPrice"):
        if doc.getElementsByTagName("ListPrice")[0].getElementsByTagName("FormattedPrice"):
            listPrice = doc.getElementsByTagName("ListPrice")[0].getElementsByTagName("FormattedPrice")[0].childNodes[
                0].data
            data['listPrice'] = listPrice

    # 获取折扣价
    if doc.getElementsByTagName("Price"):
        if doc.getElementsByTagName("Price")[0].getElementsByTagName("FormattedPrice"):
            price = doc.getElementsByTagName("Price")[0].getElementsByTagName("FormattedPrice")[0].childNodes[0].data
            data['price'] = price

    # 获取最低价
    if doc.getElementsByTagName("LowestNewPrice"):
        if doc.getElementsByTagName("LowestNewPrice")[0].getElementsByTagName("FormattedPrice"):
            lowestPrice = doc.getElementsByTagName("LowestNewPrice")[0].getElementsByTagName("FormattedPrice")[0].childNodes[0].data
            data['lowestPrice'] = lowestPrice

    # 判断评论
    if doc.getElementsByTagName("HasReviews"):
        reviews = doc.getElementsByTagName("HasReviews")[0].childNodes[0].data
        data['hasReviews'] = reviews

    # 判断Condition
    if doc.getElementsByTagName("OfferAttributes"):
        if doc.getElementsByTagName("OfferAttributes")[0].getElementsByTagName("Condition"):
            Condition = doc.getElementsByTagName("OfferAttributes")[0].getElementsByTagName("Condition")[0].childNodes[0].data
            data['condition'] = Condition

    # 获取category
    if doc.getElementsByTagName("BrowseNodes"):
        category = ''
        try:
            if doc.getElementsByTagName("BrowseNodes")[0].childNodes[3]:
                ItemList = doc.getElementsByTagName("BrowseNodes")[0].childNodes[3].getElementsByTagName("Name")
                for item in ItemList:
                    cate = item.childNodes[0].data
                    if cate == 'Departments' or cate == 'Shops':
                        continue
                    category = cate + '>' + category
        except Exception as e:
            if doc.getElementsByTagName("BrowseNodes")[0].childNodes[1]:
                ItemList = doc.getElementsByTagName("BrowseNodes")[0].childNodes[1].getElementsByTagName("Name")
                for item in ItemList:
                    cate = item.childNodes[0].data
                    if cate == 'Departments' or cate == 'Shops':
                        continue
                    category = cate + '>' + category
        data['category'] = category

    # 获取子产品数量
    if doc.getElementsByTagName("TotalVariations"):
        reviews = doc.getElementsByTagName("TotalVariations")[0].childNodes[0].data
        data['totalVariations'] = reviews

    # 获取title
    if doc.getElementsByTagName("Title"):
        title = doc.getElementsByTagName("Title")[0].childNodes[0].data.strip()
        data['title'] = title

    # 获取发布日期
    if doc.getElementsByTagName("ReleaseDate"):
        date = doc.getElementsByTagName("ReleaseDate")[0].childNodes[0].data
        data['releaseDate'] = date

    return data


def child_item_parse(doc):
    data = {
        'asin': '',
        'parentAsin': '',
        'largeImage': '',
        'featureList': '',
        'brand': '',
        'title': '',
        'listPrice': '',
        'price': '',
        'variationAttributes': '',
        'releaseDate': '',
    }

    # 获取asin数据
    if doc.getElementsByTagName("ASIN"):
        asin = doc.getElementsByTagName("ASIN")[0].childNodes[0].data
        data['asin'] = asin

    # 获取父asin
    if doc.getElementsByTagName("ParentASIN"):
        parentAsin = doc.getElementsByTagName("ParentASIN")[0].childNodes[0].data
        data['parentAsin'] = parentAsin

    # 获取image
    if doc.getElementsByTagName("LargeImage"):
        if doc.getElementsByTagName("LargeImage")[0].getElementsByTagName("URL"):
            LargeImage = doc.getElementsByTagName("LargeImage")[0].getElementsByTagName("URL")[0].childNodes[0].data
            data['largeImage'] = LargeImage

    # 获取title
    if doc.getElementsByTagName("Title"):
        title = doc.getElementsByTagName("Title")[0].childNodes[0].data
        data['title'] = title

    # 获取feature
    Feature_List = []
    if doc.getElementsByTagName("Feature"):
        FeatureList = doc.getElementsByTagName("Feature")
        try:
            for f in FeatureList:
                text = f.childNodes[0].data.strip()
                # text = text.encode('utf-8')
                text = text.replace('\n', '').replace('  ', '')
                Feature_List.append(text)
        except Exception as e:
            pass
        data['featureList'] = Feature_List

    # 获取brand
    if doc.getElementsByTagName("Brand"):
        brand = doc.getElementsByTagName("Brand")[0].childNodes[0].data
        data['brand'] = brand

    # 获取原价
    if doc.getElementsByTagName("ListPrice"):
        if doc.getElementsByTagName("ListPrice")[0].getElementsByTagName("FormattedPrice"):
            listPrice = doc.getElementsByTagName("ListPrice")[0].getElementsByTagName("FormattedPrice")[0].childNodes[
                0].data
            data['listPrice'] = listPrice

    # 获取折扣价
    if doc.getElementsByTagName("Price"):
        if doc.getElementsByTagName("Price")[0].getElementsByTagName("FormattedPrice"):
            price = doc.getElementsByTagName("Price")[0].getElementsByTagName("FormattedPrice")[0].childNodes[0].data
            data['price'] = price

    # 获取发布日期
    if doc.getElementsByTagName("ReleaseDate"):
        date = doc.getElementsByTagName("ReleaseDate")[0].childNodes[0].data
        data['releaseDate'] = date

    # 获取变体的描述信息
    if doc.getElementsByTagName("VariationAttributes"):
        try:
            VariationList = doc.getElementsByTagName("VariationAttributes")[0].getElementsByTagName("VariationAttribute")
            Attributes = {}
            for item in VariationList:
                name = item.getElementsByTagName("Name")[0].childNodes[0].data
                value = item.getElementsByTagName("Value")[0].childNodes[0].data
                Attributes[name] = value
        except Exception:
            pass

        data['variationAttributes'] = Attributes

    return data


def child_parse(doc):
    item_product_dict = {}
    # 子产品
    if doc.getElementsByTagName("Variations"):
        try:
            ItemList = doc.getElementsByTagName("Variations")[0].getElementsByTagName("Item")
            for item in ItemList:
                item_data = child_item_parse(item)
                item_product_dict[item_data['asin']] = item_data
        except Exception as e:
            print(e)

        return item_product_dict


if __name__ == '__main__':
    # 打开xml文档
    doc = xml.dom.minidom.parse('111.xml')

    # 获取父产品数据
    data = parent_parse(doc)
    pprint(data)

    print('*'*20)

    # 获取子产品数据
    child_data = child_parse(doc)
    pprint(child_data)

