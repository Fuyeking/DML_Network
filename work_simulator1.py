#!/usr/bin/env python
# encoding: utf-8
'''
@author: yeqing
@contact: 474387803@qq.com
@software: pycharm
@file: work_simulator1.py
@time: 2019/3/20 13:32
@desc:
'''
from testtool import test_fun

port = 12345
ip = "127.0.0.1"

if __name__ == '__main__':
    test_fun.dnn_test(ip, port)
