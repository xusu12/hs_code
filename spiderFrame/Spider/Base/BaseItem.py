#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
sys.path.append("../../")

# 包内导入模块, 写全路径.
from Spider.Base.BaseClass import BaseData


class Items(BaseData):

    @staticmethod
    def filrt_call_conf(config, modules):
        '''
        加工配置字典, 将配置字典中键所对应的字符串值, 加工成一个可调用对象值.
        :param config: 配置字典, 键是数据库所需的字段, 值是 解析这个字段的类或者方法的名字.
        :param modules: 一个python模块对象.
        :return: 返回加工后的配置字典, 只包含可调用对象的键值对. 如果某个键值对的可调用对象不存在, 则会被过滤掉.
        '''
        for item in config:
            config[item] = Items._filrt_callble(modules, config[item])
        result = {}
        for item in config:
            if callable(config[item]):
                result[item] = config[item]
        return result

    @staticmethod
    def _filrt_callble(modules, call_name):
        '''
        :param modules: 一个python模块对象
        :param call_name: 一个string, 是想要导入的模块成员名.
        :return: 返回模块中的可调用对象, 或者None
        '''
        if isinstance(call_name, str):
            if hasattr(modules, call_name):
                obj = getattr(modules, call_name)
                if type(obj) is type(object):
                    instance = obj()
                    if callable(instance):
                        return instance
                elif callable(obj):
                    return obj