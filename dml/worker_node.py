#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 文件名：work_simulator1.py
import json
import queue
import socket
import threading
import time

data_size = 1024


class WorkerNode:

    def __init__(self):
        """
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.net_ready = False  # 网络连接准备状态
        self.send_queue = queue.Queue()
        self.rec_queue = queue.Queue()
        self.send_lock = threading.Lock()
        self.rec_lock = threading.Lock()
        self.socket_reference_count = 0

    def __del__(self):
        self._close_socket()

    def increase_socket_reference_count(self):
        self.socket_reference_count += 1

    def decrease_socket_reference_count(self):
        self.socket_reference_count -= 1

    def connect(self, host, port):
        self.server_socket.connect((host, port))
        return self.server_socket

    def prepare_net(self):
        while not self.net_ready:
            data = self.server_socket.recv(data_size)
            print(data.decode("utf-8"))
            if data.decode("utf-8") == "OK":
                self.net_ready = True

    def add_send_data(self, data):
        self.send_queue.put(data)

    def get_rec_data(self):
        # self.rec_lock.acquire()
        if not self.rec_queue.empty():
            return self.rec_queue.get()
        # self.rec_lock.release()


def _close_socket(self):
    if self.socket_reference_count == 0:
        self.server_socket.close()


class WorkBaseSendThread(threading.Thread):
    send_client: WorkerNode

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
    rec_client: WorkerNode

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
            data = self.rec_client.server_socket.recv(data_size)
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
