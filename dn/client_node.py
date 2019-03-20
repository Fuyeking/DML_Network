#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 文件名：work_simulator1.py
import socket
import queue
import threading
import time

data_size = 1024


class ClientNode:

    def __init__(self):
        """
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ready = False  # 网络连接准备状态
        self.send_queue = queue.Queue()
        self.rec_queue = queue.Queue()
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
        while not self.ready:
            data = self.server_socket.recv(1024)
            print(data.decode("utf-8"))
            if data.decode("utf-8") == "OK":
                self.ready = True

    def add_send_data(self, data):
        self.send_queue.put(data)

    def send_data(self):
        if self.ready:
            if not self.send_queue.empty():
                # send_lock.acquire()
                loss = self.send_queue.get()
                print("send loss:", loss)
                self.server_socket.send(str(loss).encode("utf-8"))
                time.sleep(0.1)
                # send_lock.release()

    def rec_data(self):
        if self.ready:
            data = self.server_socket.recv(data_size)
            if data:
                p = data.decode("utf-8")
                self.rec_queue.put(float(p))

    def get_rec_data(self):
        if not self.rec_queue.empty():
            return self.rec_queue.get()

    def _close_socket(self):
        if self.socket_reference_count == 0:
            self.server_socket.close()


class SendThread(threading.Thread):
    send_client: ClientNode

    def __init__(self, name, send_client):
        threading.Thread.__init__(self)
        self.name = name
        self.send_client = send_client
        self.send_client.increase_socket_reference_count()
        print("create the send thread：" + self.name)

    def __del__(self):
        print("delete the thread：" + self.name)
        self.send_client.decrease_socket_reference_count()

    def run(self):
        print("start thread：" + self.name)
        while True:
            self.send_client.send_data()


class RecThread(threading.Thread):
    rec_client: ClientNode

    def __init__(self, name, rec_client):
        threading.Thread.__init__(self)
        self.name = name
        self.rec_client = rec_client
        self.rec_client.increase_socket_reference_count()

    def __del__(self):
        self.rec_client.decrease_socket_reference_count()
        print("delete the thread：" + self.name)

    def run(self):
        print("start the thread：" + self.name)
        while True:
            self.rec_client.rec_data()
