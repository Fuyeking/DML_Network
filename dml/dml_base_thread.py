#!/usr/bin/env python
# encoding: utf-8
'''
@author: yeqing
@contact: 474387803@qq.com
@software: pycharm
@file: dml_base_thread.py
@time: 2019/3/23 9:30
@desc:
'''
import json
import threading

from dml import server_node as sn


# 服务端的接受线程
class ServerRecBaseThread(threading.Thread):
    server_obj: sn.ServerNode

    def __init__(self, thread_id, thread_name, server_obj, rec_q, rec_lock):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.server_obj = server_obj
        self.rec_q = rec_q
        self.rec_lock = rec_lock
        self.server_obj.increase_reference_count()
        print("开启" + self.thread_name)

    def __del__(self):
        self.server_obj.decrease_reference_count()

    def run(self):
        while True:
            self.rec_data()

    def rec_data(self):
        if self.server_obj.net_state:
            data = self.server_obj.client.recv(sn.data_size)
            if data:
                self.rec_lock.acquire()
                self.rec_q.put(self.post_process(data))
                self.rec_lock.release()

    # 可以被之类重载
    def post_process(self, data):
        print("recieve data:", data)
        return json.loads(data.decode())


# 服务端的发送进程
class ServerSendBaseThread(threading.Thread):
    server_obj: sn.ServerNode

    def __init__(self, thread_id, thread_name, server_obj, send_q, send_lock):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.server_obj = server_obj
        self.send_q = send_q
        self.send_lock = send_lock
        self.server_obj.increase_reference_count()
        print("start the thread" + self.thread_name)

    def __del__(self):
        self.server_obj.decrease_reference_count()

    def run(self):
        while True:
            self.send_data()

    def send_data(self):
        if self.server_obj.net_state:
            self.send_lock.acquire()
            if not self.send_q.empty():
                data = self.send_q.get()
                self.server_obj.client.send(self.pre_process(data))
            self.send_lock.release()

    # 可以被子类重载
    def pre_process(self, data):
        return json.dumps(data).encode()
