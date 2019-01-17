import re
from xmltodict import parse
from pprint import pprint


def xml_parse(xmldict):
    data = {
        'asin': '',
        'parentAsin': '',
        'LargeImage': '',
        'ImageSetsdict': '',
        'Feature_List': '',
        'brand': '',
        'bsr': '',
        'title': '',
        'new_tosell': '',
        'used_tosell': '',
        'listPrice': '',
        'price': '',
        'lowestPrice': '',
        'category': '',
        'hasReviews': '',
        'TotalVariations': '',
        'ReleaseDate': '',
        'sname': '',
        'Condition': '',
    }

    asin = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('ASIN')
    data['asin'] = asin

    pasin = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('ParentASIN')
    data['parentAsin'] = pasin

    LargeImage = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('LargeImage').get('URL')
    data['LargeImage'] = LargeImage

    ImageSetsdict = {}
    ImageSets = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('ImageSets').get('ImageSet')
    # pprint(ImageSets[0])
    for ImageSet in ImageSets:
        category = ImageSet.get('@Category')
        ImageSetsdict[category] = {
            'SwatchImage': ImageSet.get('SwatchImage').get('URL'),
            'SmallImage': ImageSet.get('SmallImage').get('URL'),
            'ThumbnailImage': ImageSet.get('ThumbnailImage').get('URL'),
            'TinyImage': ImageSet.get('TinyImage').get('URL'),
            'MediumImage': ImageSet.get('MediumImage').get('URL'),
            'LargeImage': ImageSet.get('LargeImage').get('URL'),
        }
    data['ImageSetsdict'] = ImageSetsdict

    Feature_List = []
    Features = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('ItemAttributes').get('Feature')
    for Feature in Features:
        Feature_List.append(Feature.replace('\n', '').replace('  ', ''))
    data['Feature_List'] = Feature_List

    Brand = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('ItemAttributes').get('Brand')
    data['brand'] = Brand

    bsr = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('SalesRank')
    data['bsr'] = bsr

    Title = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('ItemAttributes').get('Title')
    data['title'] = Title

    new_tosell = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('OfferSummary').get('TotalNew')
    data['new_tosell'] = new_tosell

    used_tosell = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('OfferSummary').get('TotalUsed')
    data['used_tosell'] = used_tosell

    listPrice = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('ItemAttributes').get('ListPrice').get('FormattedPrice')
    data['listPrice'] = listPrice

    price = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('Offers').get('Offer').get('OfferListing').get('Price').get('FormattedPrice')
    data['price'] = price

    lowestPrice = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('OfferSummary').get('LowestNewPrice').get('FormattedPrice')
    data['lowestPrice'] = lowestPrice

    hasReviews = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('CustomerReviews').get('HasReviews')
    data['hasReviews'] = hasReviews

    Condition = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('Offers').get('Offer').get('OfferAttributes').get('Condition')
    data['Condition'] = Condition

    category_list = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('BrowseNodes').get('BrowseNode')[1]
    category = category_list.get('Name')
    # category_list = category_list[1].get('Children').get('BrowseNode')
    # for category in category_list:
    #     category = category.get('Name')
    #     print(category)
    pprint(category_list.get('Children'))
    data['category'] = category

    date = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('ItemAttributes').get('ReleaseDate')
    data['ReleaseDate'] = date

    sname = xmldict.get('ItemLookupResponse').get('Items').get('Item').get('Offers').get('Offer').get('Merchant').get('Name')
    data['sname'] = sname

    return data


if __name__ == '__main__':
    lxmls = open('./test1.xml', encoding='utf8').read()
    xmldict = parse(lxmls)
    data = xml_parse(xmldict)
    pprint(data)