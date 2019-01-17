#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")
sys.path.append("../../")
import os

from Spider.Base.BaseClass import BaseConfig


# 项目根目录: 当前文件的上级路径的上级路径的绝对路径(如果目录结构有变动, 也需要变动此行代码)
base_dir = lambda: os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class Config(BaseConfig):
    obj = None
    # 单例模式
    def __new__(cls, *args, **kwargs):
        if cls.obj is None:
            cls.obj = object.__new__(cls)
        return cls.obj

    # 初始化
    def __init__(self):
        super(Config, self).__init__()
        # 设置项目根目录
        self.base_dir = base_dir()
        # 设置配置跟目录
        self.conf_dir = os.path.join(self.base_dir, 'config/')
        # 设置配置文件路径
        self.filename = os.path.join(self.conf_dir, "config.ini")
        # 读取配置文件中的配置
        self.read(self.filename)
        # 设置配置文件
        self.set()

