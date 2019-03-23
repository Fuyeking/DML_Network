#!/usr/bin/env python
# encoding: utf-8
'''
@author: yeqing
@contact: 474387803@qq.com
@software: pycharm
@file: test_fun.py
@time: 2019/3/20 13:27
@desc:
'''
from dml import client_node as cn


def dnn_test(ip, port):
    client = cn.ClientNode()
    client.connect(ip, port)
    client.prepare_net()

    for loss in range(1, 10):
        dic = dict()
        dic['w'] = loss
        dic['b'] = loss + 0.1
        client.add_send_data(dic)

    send_thread = cn.SendThread("计算节点", client)
    send_thread.start()
    rec_thread = cn.RecThread("计算节点", client)
    rec_thread.start()
    while True:
        data = client.get_rec_data()
        if data is not None:
            print(data)
