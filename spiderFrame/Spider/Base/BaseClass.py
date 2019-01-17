#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
sys.path.append("../../")
from abc import ABC
from typing import Dict
from typing import List
from abc import abstractmethod
from configparser import ConfigParser


# 一个自定义的字典, 并没有什么特殊的地方, BaseConfig专用.
class Dictionary(dict):
    def __getattr__(self, key):
        return self.get(key, None)


# 一个获取文件配置的基类
class BaseConfig:
    '''子类调用super方法后, 需要设置配置文件的路径. 然后调用read方法, 再调用set方法. 完成初始化. 实例调用get方法, 获取配置.'''
    def __init__(self):
        # 创建ConfigParser实例对象
        self.conf = ConfigParser()

    def read(self, file_name: str):
        # 读取配置文件中的配置
        return self.conf.read(file_name)

    def set(self):
        # 将配置存入实例对象中.
        for section in self.conf.sections():
            setattr(self, section, Dictionary())
            for key, value in self.conf.items(section):
                setattr(getattr(self, section), key, value)

    # 获取配置
    def get(self, section, key):
        return getattr(getattr(self, section), key, None)


# 一个打包数据的基类, 要与解析基类配合使用
class BaseData:
    def init_config(self, config: dict):
        '''
        初始化实例属性, 每个子类的__init__方法, 必须调用此方法.
        :param config: 一个字典, 键是解析数据所需字段, 值是一个callable对象, 即解析这个字段的对象.
        :return: None
        '''
        conf: Dict(str, callable) = config
        self.__dict__ = conf

    def __call__(self, params: dict):
        '''自动调用可调用的实例属性'''
        for item in self.__dict__:
            if callable(self.__dict__[item]):
                self.__dict__[item] = self.__dict__[item](params)


# 解析基类, 适用于单字段解析.
class BaseParse:
    '''
    子类继承调用super方法后,
    调用 self.register 方法,
    传入子类新增的方法名,
    即可注册子类新增方法,
    使方法自动运行
    '''
    def __init__(self):
        # 设置启动方法, 默认为'run', 如无特殊需要, 子类不要修改
        self.__run: str = 'run'
        # 设置方法数组(一个方法名列表, 默认为空, 由子类注册进来)
        self.__func_array: List[str] = []

    def register(self, func_name: str):
        '''注册新方法(子类有新增方法, 则在子类__init__方法中调用此方法, 传入新增方法名, 注册此方法)'''
        self.__func_array.append(func_name)

    def set_run(self, run_name: str):
        '''设置启动方法(如无特殊需要, 子类不要调用此方法)'''
        self.__run = run_name

    def get_run_name(self):
        '''获取run方法'''
        return self.__run

    def get_func_array(self):
        '''获取注册方法列表'''
        return self.__func_array

    def run(self, params: dict):
        '''
        启动方法, 指定为run方法.子类中如果更换了启动方法, 需要将启动方法的方法名赋值给 __run 变量
        :param params: 一个字典
        :return: 返回整个实例的运行结果
        '''
        for func in self.__func_array:
            if not isinstance(func, str):
                raise ValueError('__func_array value must str')
            if not hasattr(self, func):
                raise AttributeError('"%s" object has not attribute "%s"' % (self.__class__.__name__, func))
            obj = getattr(self, func)
            if not callable(obj):
                raise RuntimeError(obj, 'is not callable')
            result = obj(params)
            if result:
                return result

    def __call__(self, params: dict):
        '''
        让类函数化,作为实例的唯一对外接口
        :param params: 一个字典
        :return: 返回rum方法的运行结果
        '''
        if not isinstance(self.__run, str):
            raise TypeError('paser_obj must str')
        if not hasattr(self, self.__run):
            raise AttributeError('"%s" object has not attribute "%s"' % (self.__class__.__name__, self.__run))
        obj = getattr(self, self.__run)
        if not callable(obj):
            raise RuntimeError(obj, 'is not callable')
        return obj(params)


# 启动基类, 抽象类, 并没有什么卵用.
class BaseRun(ABC):
    '''抽象基类, 接口类'''
    @abstractmethod
    def run(self):
        pass