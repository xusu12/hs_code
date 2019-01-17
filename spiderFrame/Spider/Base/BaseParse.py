#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
sys.path.append("../../")
from typing import List
import lxml.etree as etree

from Spider.Base.BaseClass import BaseParse


# 所有的解析类, 继承此类.
class Parse(BaseParse):
    @staticmethod
    def get_new_data(
            pattern_str: str=None,
            expr_list: List[object or str]=None,
            xpath_obj: etree._Element=None,
            data_type: str=None
        ) -> list:
        '''
        解析数据都调用此方法.
        :param pattern_str: 正则表达式的解析目标, 一般是HTML
        :param expr_list: 表达式, 可以是预编译过的正则表达式, 也可以是string型的xpath表达式
        :param xpath_obj: xpath对象, 即lxml.etree.HTML(HTML) 的返回值
        :param data_type: 解析的数据类型, 比如一般都是爬虫名. 比如product, keyword等等.
        :return: 返回list.
        '''
        # expr_list 为必要参数, 如果不是list, 直接报错.
        if not isinstance(expr_list, list):
            raise TypeError('param "expr_list" type must be list!')
        if expr_list is not None and pattern_str is not None :
            callable_obj = GetData.get_data_use_re_findall
            parse_obj = pattern_str
        elif expr_list is not None and xpath_obj is not None:
            callable_obj = GetData.get_data_use_xpath
            parse_obj = xpath_obj
        else:
            callable_obj = None
            parse_obj = None
        if not callable(callable_obj):
            return []
        for expr in expr_list:
            try:
                # 正常情况, 返回结果集.
                return callable_obj(parse_obj, expr)
            except Exception as e:
                err_msg = 'Expr:, "{}", Extract:, "{}", Error:, "{}"'.format(expr, data_type, e)
                print(err_msg)
        # 异常情况, 返回空列表
        return []


class GetData:
    @staticmethod
    def get_data_use_xpath(xpath_obj: etree._Element, xpath_expr: str) -> list or None:
        if not hasattr(xpath_obj, 'xpath'):
            raise AttributeError(('object "{}" not attribute "xpath"'.format(xpath_obj)))
        elif not isinstance(xpath_obj, etree._Element) :
            raise TypeError('param "xpath_obj" type must be lxml.etree._Element object!')
        elif not isinstance(xpath_expr, str):
            raise TypeError('param "xpath_expr" type must be str!')
        return xpath_obj.xpath(xpath_expr)

    @staticmethod
    def get_data_use_re_findall(pattern_str: str, pattern_expr: object) -> list or None:
        if not isinstance(pattern_str, str):
            raise TypeError('param "pattern_str" type must be string!')
        elif not hasattr(pattern_expr, 'findall'):
            raise AttributeError('object "pattern_list[{}]" not attribute "findall"'.format(pattern_expr))
        return pattern_expr.findall(pattern_str)