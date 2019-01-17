#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")


class MyList:
    def __init__(self):
        self.items = []
        self.current = 0

    def add(self, parms):
        self.items.append(parms)

    def next(self):
        return self.__next__()

    def __next__(self):
        if self.current < len(self.items):
            item = self.items.pop(0)
            return item
        else:
            raise StopIteration

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.items)


class MyDict(dict):

    def __add__(self, other):
        self.dc = {}
        self.dc.update(self)
        self.dc.update(other)
        return self.dc


class MySet(set):

    def __add__(self, other):
        return self | other


if __name__ == '__main__':
    a = MyDict()
    print()
    b = MyDict()
    a['dic'] = 1
    b['dict'] = 2
    print(a, id(a))
    print(b, id(b))
    a1 = a + b
    print(a1, id(a1))
    print(a, id(a))
    print(b, id(b))
    c = MySet()
    d = MySet()
    c.add(1)
    c.add(4)
    d.add(1)
    d.add(2)
    d.add(3)
    print(c, id(c))
    print(d, id(d))
    e = c + d
    print(e, id(e))
    print(c, id(c))