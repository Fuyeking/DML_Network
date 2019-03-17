#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 文件名：client_test2.py
from dn import client_node as cn

client = cn.ClientNode()
client.connect("127.0.0.1", 12346)
client.prepare_net()
for index in range(1, 10):
    client.add_send_data(index)
send_thread = cn.SendThread("客户端发进程", client)
send_thread.start()
rec_thread = cn.RecThread("客户端收进程", client)
rec_thread.start()
