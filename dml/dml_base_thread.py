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
import time

from dml import server_node as sn
from dml import worker_node as wn


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


class WorkBaseSendThread(threading.Thread):
    send_client: wn.WorkerNode

    def __init__(self, name, send_client):
        threading.Thread.__init__(self)
        self.name = name
        self.send_client = send_client
        self.send_client.increase_socket_reference_count()
        self.send_queue = send_client.send_queue
        self.send_lock = send_client.send_lock
        print("create the send thread：" + self.name)

    def __del__(self):
        print("delete the thread：" + self.name)
        self.send_client.decrease_socket_reference_count()

    def run(self):
        print("start thread：" + self.name)
        while True:
            self.send_data()

    def send_data(self):
        if self.send_client.net_ready:
            if not self.send_queue.empty():
                # self.send_lock.acquire()
                data = self.send_queue.get()
                if data is not None:
                    print("send data:", data)
                    self.send_client.server_socket.send(self.handle_data(data))
                time.sleep(0.1)
                # self.send_lock.release()

    def handle_data(self, data):
        return json.dumps(data).encode()


class WorkBaseRecThread(threading.Thread):
    rec_client: wn.WorkerNode

    def __init__(self, name, rec_client):
        threading.Thread.__init__(self)
        self.name = name
        self.rec_client = rec_client
        self.rec_client.increase_socket_reference_count()
        self.rec_queue = rec_client.rec_queue
        self.rec_lock = rec_client.rec_lock

    def __del__(self):
        self.rec_client.decrease_socket_reference_count()
        print("delete the thread：" + self.name)

    def run(self):
        print("start the thread：" + self.name)
        while True:
            self.rec_data()

    def rec_data(self):
        if self.rec_client.net_ready:
            data = self.rec_client.server_socket.recv(sn.data_size)
            if data:
                print("client recieve data", data)
                # self.rec_lock.acquire()
                self.rec_queue.put(self.handle_data(data))
                # self.rec_lock.release()

    def handle_data(self, data):
        '''
        子类继承后，根据应用场景不同，进行重载
        :param data:
        :return:
        '''
        return json.loads(data.decode())
