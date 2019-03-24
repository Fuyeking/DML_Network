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

    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.server_obj = None
        self.rec_q = None
        self.rec_lock = None
        print("开启" + self.thread_name)

    def init_para(self, server_obj, rec_q, rec_lock):
        self.server_obj = server_obj
        self.rec_q = rec_q
        self.rec_lock = rec_lock
        self.server_obj.increase_reference_count()

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

    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.server_obj = None
        self.send_q = None
        self.send_lock = None
        print("start the thread" + self.thread_name)

    def init_para(self, server_obj, send_q, send_lock):
        self.server_obj = server_obj
        self.send_q = send_q
        self.send_lock = send_lock
        self.server_obj.increase_reference_count()

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


class CalcAverageLoss(threading.Thread):
    rec_lock_list: dict
    rec_data_list: dict
    send_data_list: dict

    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.send_data_list = None
        self.rec_data_list = None
        self.rec_lock_list = None
        self.ip_set = None

        print("start the thread:" + self.thread_name)

    def init_para(self, ip_set, send_list, rec_list, rec_lock_list):
        self.send_data_list = send_list
        self.rec_data_list = rec_list
        self.rec_lock_list = rec_lock_list
        self.ip_set = ip_set

    def run(self):
        while True:
            while self._check_rec_list():  # 所有计算节点已经发送数据到参数节点
                send_loss = self._calc_average_loss()  # 计算均值
                self._send_new_loss(send_loss)  # 给所有计算节点发送新的loss

    def _check_rec_list(self):
        '''
        判断所有的接受队列是否为空，不为空返回True，发送数据。为空，返回False，不发送数据
        :return:
        '''
        for port, ip in self.ip_set.items():
            if self.rec_data_list[port].empty():
                return False
        return True

    def _calc_average_loss(self):
        sum_w = 0
        sum_b = 0
        for port, ip in self.ip_set.items():
            self.rec_lock_list[port].acquire()
            if not self.rec_data_list[port].empty():
                data = self.rec_data_list[port].get()
                if data is not None:
                    sum_w += data['w']
                    sum_b += data['b']
            self.rec_lock_list[port].release()

        average_loss = dict()
        average_loss['w'] = sum_w / 3
        average_loss['b'] = sum_b / 3
        print("new  loss：", average_loss)
        return average_loss

    def _send_new_loss(self, new_loss):
        for port, ip in self.ip_set.items():
            self.send_data_list[port].put(new_loss)
