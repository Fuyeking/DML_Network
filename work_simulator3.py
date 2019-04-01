#!/usr/bin/env python
# encoding: utf-8
'''
@author: yeqing
@contact: 474387803@qq.com
@software: pycharm
@file: work_simulator3.py
@time: 2019/3/20 13:34
@desc:
'''
from examples import test_fun
from examples import gd
port = 12347
ip = "127.0.0.1"

if __name__ == '__main__':
    #test_fun.dnn_test(ip, port)
    gd.gd_test(ip, port)