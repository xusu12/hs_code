#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

sys.path.append("../")
sys.path.append("../../")
import os
import time
from datetime import datetime
from configparser import ConfigParser

base_dir = lambda: os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class Dictionary(dict):

    def __getattr__(self, key):
        return self.get(key, None)


class Config:
    obj = None

    def __new__(cls, *args, **kwargs):
        if cls.obj is None:
            cls.obj = object.__new__(cls)
        return cls.obj

    def __init__(self):
        self.base_dir = base_dir()
        # print(self.base_dir)
        self.filename = os.path.join(self.base_dir, "config/config.ini")
        # print(self.filename)
        self.conf = ConfigParser()
        self.conf.read(self.filename)

        for section in self.conf.sections():
            setattr(self, section, Dictionary())
            for key, value in self.conf.items(section):
                setattr(getattr(self, section), key, value)

    def get(self, section, key):
        return getattr(getattr(self, section), key, None)
