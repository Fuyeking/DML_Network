#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 文件名：client_test2.py
from dn import client_node as cn


port = 12346
ip = "127.0.0.1"


def test():
    client = cn.ClientNode()
    client.connect(ip, port)
    client.prepare_net()
    for loss in range(1, 10):
        client.add_send_data(loss)
    send_thread = cn.SendThread("计算节点", client)
    send_thread.start()
    rec_thread = cn.RecThread("计算节点", client)
    rec_thread.start()


if __name__ == '__main__':
    test()
