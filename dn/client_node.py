#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 文件名：client_test1.py
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
        self.ready = False  # 准备状态
        self.send_queue = queue.Queue()
        self.rec_queue = queue.Queue()

    def __del__(self):
        self._close()

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
                print("发送数据", loss)
                self.server_socket.send(str(loss).encode("utf-8"))
                time.sleep(0.1)
                # send_lock.release()

    def rec_data(self):
        if self.ready:
            data = self.server_socket.recv(data_size)
            if data:
                p = data.decode("utf-8")
                self.rec_queue.put(float(p))
                print("接受数据：", p)

    def _close(self):
        self.server_socket.close()


class SendThread(threading.Thread):
    def __init__(self, name, send_client):
        threading.Thread.__init__(self)
        self.name = name
        self.send_client = send_client

    def run(self):
        print("开启线程：" + self.name)
        while True:
            self.send_client.send_data()
        print("退出线程：" + self.name)


class RecThread(threading.Thread):
    def __init__(self, name, rec_client):
        threading.Thread.__init__(self)
        self.name = name
        self.rec_client = rec_client

    def run(self):
        print("开启线程：" + self.name)
        while True:
            self.rec_client.rec_data()
